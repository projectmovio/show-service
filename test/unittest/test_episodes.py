import copy
import json
import pytest

from api.episodes import handle, UnsupportedMethod

TEST_SHOW_UUID = "60223a49-f9ec-4bd8-b90e-23a00cba6a58"


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
        "pathParameters": {
            "id": TEST_SHOW_UUID
        },
        "body": '{"api_id": "456", "api_name": "tvmaze"}'
    }

    def test_success(self, mocked_shows_db, mocked_episodes_db):
        mocked_episodes_db.table.query.side_effect = mocked_episodes_db.NotFoundError
        mocked_shows_db.table.get_item.return_value = {
            "Item": {
                "id": TEST_SHOW_UUID
            }
        }

        res = handle(self.event, None)

        exp = {
            "body": json.dumps({"id": "20e10800-b2e2-5079-90b5-243647854ef2"}),
            "statusCode": 200
        }
        assert res == exp

    def test_already_exist(self, mocked_shows_db, mocked_episodes_db):
        mocked_episodes_db.table.query.return_value = {
            "Items": [
                {
                    "tvmaze_id": "123"
                }
            ],
            "Count": 1
        }
        mocked_shows_db.table.get_item.return_value = {
            "Item": {
                "id": TEST_SHOW_UUID
            }
        }

        res = handle(self.event, None)

        exp = {
            "body": json.dumps({"id": "20e10800-b2e2-5079-90b5-243647854ef2"}),
            "statusCode": 200
        }
        assert res == exp

    def test_no_body(self, mocked_shows_db, mocked_episodes_db):
        mocked_episodes_db.table.query.return_value = {
            "Items": [
                {
                    "tvmaze_id": "123"
                },
            ]
        }
        mocked_shows_db.table.get_item.return_value = {
            "Item": {
                "id": TEST_SHOW_UUID
            }
        }

        event = copy.deepcopy(self.event)
        del event["body"]

        res = handle(event, None)

        exp = {
            'body': '{"message": "Invalid post body"}',
            'statusCode': 400
        }
        assert res == exp

    def test_invalid_body(self, mocked_shows_db, mocked_episodes_db):
        mocked_episodes_db.table.query.return_value = {
            "Items": [
                {
                    "mal_id": 123
                }
            ]
        }
        mocked_shows_db.table.get_item.return_value = {
            "Item": {
                "id": TEST_SHOW_UUID
            }
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

    def test_missing_path_id(self, mocked_shows_db, mocked_episodes_db):
        mocked_episodes_db.table.query.return_value = {
            "Items": [
                {
                    "mal_id": 123
                }
            ]
        }

        event = copy.deepcopy(self.event)
        del event["pathParameters"]

        res = handle(event, None)

        exp = {
            'body': 'Missing id query param',
            'statusCode': 400
        }
        assert res == exp

    def test_not_found(self, mocked_shows_db, mocked_episodes_db):
        mocked_episodes_db.table.query.return_value = {
            "Items": [
                {
                    "mal_id": 123
                }
            ]
        }
        mocked_shows_db.table.get_item.side_effect = mocked_shows_db.NotFoundError

        res = handle(self.event, None)

        exp = {
            'body': '{"message": "Show not found"}',
            'statusCode': 404
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

    def test_success(self, mocked_shows_db, mocked_episodes_db):
        exp_res = {
            "id": "123",
            "tvmaze_id": "1",
        }
        mocked_episodes_db.table.query.return_value = {
            "Items": [
                exp_res
            ],
            "Count": 1
        }

        res = handle(self.event, None)
        res_body = json.loads(res["body"])

        assert res["statusCode"] == 200
        assert res_body["id"] == exp_res["id"]
        assert res_body["tvmaze_id"] == exp_res["tvmaze_id"]
        assert res_body["name"] == "Pilot"  # From real tvmaze api

    def test_not_found(self, mocked_shows_db, mocked_episodes_db):
        mocked_episodes_db.table.query.side_effect = mocked_episodes_db.NotFoundError

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