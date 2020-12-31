import json
import pytest

from api.shows import handle, UnsupportedMethod


def test_post_shows(mocked_shows_db):
    mocked_shows_db.table.query.side_effect = mocked_shows_db.NotFoundError
    event = {
        "requestContext": {
            "http": {
                "method": "POST"
            }
        },
        "queryStringParameters": {
            "tvmaze_id": "123"
        },
        "body": '{"id": "123","image": "img"}'
    }

    res = handle(event, None)

    exp = {
        "body": json.dumps({"show_id": "5598aa78-0a11-5849-a708-6a34131c56d7"}),
        "statusCode": 200
    }
    assert res == exp


def test_post_shows_already_exist(mocked_shows_db):
    mocked_shows_db.table.query.return_value = {
        "Items": [
            {
                "tvmaze_id": "123"
            }
        ]
    }
    event = {
        "requestContext": {
            "http": {
                "method": "POST"
            }
        },
        "queryStringParameters": {
            "tvmaze_id": "123"
        }
    }

    res = handle(event, None)

    exp = {
        "body": json.dumps({"show_id": "5598aa78-0a11-5849-a708-6a34131c56d7"}),
        "statusCode": 200
    }
    assert res == exp


def test_post_shows_no_query_params(mocked_shows_db):
    mocked_shows_db.table.query.return_value = {
        "Items": [
            {
                "tvmaze_id": "123"
            }
        ]
    }
    event = {
        "requestContext": {
            "http": {
                "method": "POST"
            }
        },
        "queryStringParameters": {

        }
    }

    res = handle(event, None)

    exp = {
        "statusCode": 400,
        "body": json.dumps({
            "error": "Please specify query parameters"
        })
    }
    assert res == exp


def test_post_shows_invalid_query_params(mocked_shows_db):
    mocked_shows_db.table.query.return_value = {
        "Items": [
            {
                "mal_id": 123
            }
        ]
    }
    event = {
        "requestContext": {
            "http": {
                "method": "POST"
            }
        },
        "queryStringParameters": {
            "aa": "123"
        }
    }

    res = handle(event, None)

    exp = {
        "statusCode": 400,
        "body": json.dumps({
            "error": "Please specify the 'tvmaze_id' query parameter"
        })
    }
    assert res == exp


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