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
        "body": '{"api_id": "123", "api_name": "tvmaze"}'
    }

    res = handle(event, None)

    exp = {
        "body": json.dumps({"id": "cf1ffb71-48c3-53c0-9966-900cc5e5553e"}),
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
        "body": '{"api_id": "123", "api_name": "tvmaze"}'
    }

    res = handle(event, None)

    exp = {
        "body": json.dumps({"id": "cf1ffb71-48c3-53c0-9966-900cc5e5553e"}),
        "statusCode": 200
    }
    assert res == exp


def test_post_shows_no_body(mocked_shows_db):
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
    }

    res = handle(event, None)

    exp = {
        "statusCode": 400,
        "body": "Invalid post body"
    }
    assert res == exp


def test_post_shows_invalid_body(mocked_shows_db):
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
        "body": '{"aa": "bb"}'
    }

    res = handle(event, None)

    exp = {
        'body': '{"message": "Invalid post schema", '
                '"error": "Additional properties are not allowed (\'aa\' was unexpected)"}',
        'statusCode': 400
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
