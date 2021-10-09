import copy
import json
import pytest

from api.shows import handle, UnsupportedMethod


def test_unsupported_method():
    event = {
        "requestContext": {
            "http": {
                "method": "AA"
            }
        },
        "queryStringParameters": {
            "mal_id": "123"
        }
    }

    with pytest.raises(UnsupportedMethod):
        handle(event, None)


class TestPost:
    event = {
        "requestContext": {
            "http": {
                "method": "POST"
            }
        },
        "body": '{"api_id": "123", "api_name": "tvmaze"}'
    }

    def test_success(self, mocked_shows_db):
        mocked_shows_db.table.query.return_value = {"Items": []}

        res = handle(self.event, None)
        res_body = json.loads(res["body"])

        assert res["statusCode"] == 200
        assert res_body["id"] == "cf1ffb71-48c3-53c0-9966-900cc5e5553e"
        assert res_body["tvmaze_id"] == "123"
        assert res_body["name"] == "Lost"  # From real tvmaze api
        assert res_body["ep_count"] == 121
        assert res_body["special_count"] == 29

    def test_already_exist(self, mocked_shows_db):
        mocked_shows_db.table.query.return_value = {
            "Items": [
                {
                    "tvmaze_id": "123",
                    "id": "cf1ffb71-48c3-53c0-9966-900cc5e5553e",
                }
            ]
        }

        res = handle(self.event, None)

        res_body = json.loads(res["body"])

        assert res["statusCode"] == 200
        assert res_body["id"] == "cf1ffb71-48c3-53c0-9966-900cc5e5553e"
        assert res_body["tvmaze_id"] == "123"
        assert res_body["name"] == "Lost"  # From real tvmaze api
        assert res_body["ep_count"] == 121
        assert res_body["special_count"] == 29

    def test_no_body(self, mocked_shows_db):
        mocked_shows_db.table.query.return_value = {
            "Items": [
                {
                    "tvmaze_id": "123"
                }
            ]
        }
        event = copy.deepcopy(self.event)
        del event["body"]

        res = handle(event, None)

        exp = {
            "statusCode": 400,
            "body": "Invalid post body"
        }
        assert res == exp

    def test_invalid_body(self, mocked_shows_db):
        mocked_shows_db.table.query.return_value = {
            "Items": [
                {
                    "mal_id": 123
                }
            ]
        }
        event = copy.deepcopy(self.event)
        event["body"] = '{"aa": "bb"}'

        res = handle(event, None)

        exp = {
            'body': '{"message": "Invalid post schema", '
                    '"error": "Additional properties are not allowed (\'aa\' was unexpected)"}',
            'statusCode': 400
        }
        assert res == exp


class TestGet:
    event = {
        "requestContext": {
            "http": {
                "method": "GET"
            }
        },
        "queryStringParameters": {
            "api_id": "123",
            "api_name": "tvmaze",
        }
    }

    def test_success(self, mocked_shows_db):
        exp_res = {
            "id": "123",
            "ep_count": 121,
            "special_count": 29,
            "tvmaze_id": "1111"
        }
        mocked_shows_db.table.query.return_value = {
            "Items": [
                exp_res
            ]
        }

        res = handle(self.event, None)
        res_body = json.loads(res["body"])

        assert res["statusCode"] == 200
        assert res_body["id"] == exp_res["id"]
        assert res_body["tvmaze_id"] == exp_res["tvmaze_id"]
        assert res_body["name"] == "Lost"  # From real tvmaze api

    def test_not_found(self, mocked_shows_db):
        mocked_shows_db.table.query.side_effect = mocked_shows_db.NotFoundError

        res = handle(self.event, None)

        exp = {
            "statusCode": 404,
        }
        assert res == exp

    def test_empty_query_params(self):
        event = copy.deepcopy(self.event)
        event["queryStringParameters"] = {}

        res = handle(event, None)

        exp = {
            "statusCode": 400,
            "body": json.dumps({"error": "Please specify query parameters"})
        }
        assert res == exp

    def test_invalid_query_params(self):
        event = copy.deepcopy(self.event)
        event["queryStringParameters"] = {
            "abc": "123"
        }

        res = handle(event, None)

        exp = {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing api_id query parameter"})
        }
        assert res == exp

    def test_missing_api_name(self):
        event = copy.deepcopy(self.event)
        del event["queryStringParameters"]["api_name"]
        res = handle(event, None)

        exp = {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing api_name query parameter"})
        }
        assert res == exp

    def test_invalid_api_name(self):
        event = copy.deepcopy(self.event)
        event["queryStringParameters"]["api_name"] = "INVALID"
        res = handle(event, None)

        exp = {
            "statusCode": 400,
            "body": json.dumps({"error": "Unsupported api_name"})
        }
        assert res == exp
