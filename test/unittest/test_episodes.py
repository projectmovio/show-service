import json
import pytest

from api.episodes import handle, UnsupportedMethod

TEST_SHOW_UUID = "60223a49-f9ec-4bd8-b90e-23a00cba6a58"


def test_post(mocked_shows_db, mocked_episodes_db):
    mocked_episodes_db.table.query.side_effect = mocked_episodes_db.NotFoundError
    mocked_shows_db.table.get_item.return_value = {
        "Item": {
            "id": TEST_SHOW_UUID
        }
    }
    event = {
        "requestContext": {
            "http": {
                "method": "POST"
            }
        },
        "queryStringParameters": {
            "id": TEST_SHOW_UUID
        },
        "body": '{"api_id": "456", "api_name": "tvmaze"}'
    }

    res = handle(event, None)

    exp = {
        "body": json.dumps({"id": "20e10800-b2e2-5079-90b5-243647854ef2"}),
        "statusCode": 200
    }
    assert res == exp


def test_post_already_exist(mocked_shows_db, mocked_episodes_db):
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

    event = {
        "requestContext": {
            "http": {
                "method": "POST"
            }
        },
        "queryStringParameters": {
            "id": TEST_SHOW_UUID
        },
        "body": '{"api_id": "456", "api_name": "tvmaze"}'
    }

    res = handle(event, None)

    exp = {
        "body": json.dumps({"id": "20e10800-b2e2-5079-90b5-243647854ef2"}),
        "statusCode": 200
    }
    assert res == exp


def test_post_no_body(mocked_shows_db, mocked_episodes_db):
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

    event = {
        "requestContext": {
            "http": {
                "method": "POST"
            }
        },
        "queryStringParameters": {
            "id": TEST_SHOW_UUID
        },
    }

    res = handle(event, None)

    exp = {
        'body': '{"message": "Invalid post body"}',
        'statusCode': 400
    }
    assert res == exp


def test_post_invalid_body(mocked_shows_db, mocked_episodes_db):
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

    event = {
        "requestContext": {
            "http": {
                "method": "POST"
            }
        },
        "queryStringParameters": {
            "id": TEST_SHOW_UUID
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


def test_post_missing_path_id(mocked_shows_db, mocked_episodes_db):
    mocked_episodes_db.table.query.return_value = {
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
        "body": '{"api_id": "456", "api_name": "tvmaze"}'
    }

    res = handle(event, None)

    exp = {
        'body': 'Missing id query param',
        'statusCode': 400
    }
    assert res == exp


def test_post_show_not_found(mocked_shows_db, mocked_episodes_db):
    mocked_episodes_db.table.query.return_value = {
        "Items": [
            {
                "mal_id": 123
            }
        ]
    }
    mocked_shows_db.table.get_item.side_effect = mocked_shows_db.NotFoundError

    event = {
        "requestContext": {
            "http": {
                "method": "POST"
            }
        },
        "queryStringParameters": {
            "id": TEST_SHOW_UUID
        },
        "body": '{"api_id": "456", "api_name": "tvmaze"}'
    }

    res = handle(event, None)

    exp = {
        'body': '{"message": "Show not found"}',
        'statusCode': 404
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


def test_get_by_api_id(mocked_shows_db, mocked_episodes_db):
    exp_res = {
        "id": "123"
    }
    mocked_episodes_db.table.query.return_value = {
        "Items": [
            exp_res
        ],
        "Count": 1
    }
    event = {
        "requestContext": {
            "http": {
                "method": "GET"
            }
        },
        "queryStringParameters": {
            "tvmaze_id": "123"
        }
    }

    res = handle(event, None)

    exp = {
        "statusCode": 200,
        "body": json.dumps(exp_res)
    }
    assert res == exp


def test_get_by_api_id_not_found(mocked_shows_db, mocked_episodes_db):
    mocked_episodes_db.table.query.side_effect = mocked_episodes_db.NotFoundError
    event = {
        "requestContext": {
            "http": {
                "method": "GET"
            }
        },
        "queryStringParameters": {
            "tvmaze_id": "123"
        }
    }

    res = handle(event, None)

    exp = {
        "statusCode": 404,
    }
    assert res == exp


def test_get_no_query_params():
    event = {
        "requestContext": {
            "http": {
                "method": "GET"
            }
        },
        "queryStringParameters": {
        }
    }

    res = handle(event, None)

    exp = {
        "statusCode": 400,
        "body": json.dumps({"error": "Please specify query parameters"})
    }
    assert res == exp


def test_get_invalid_query_params():
    event = {
        "requestContext": {
            "http": {
                "method": "GET"
            }
        },
        "queryStringParameters": {
            "abc": "123"
        }
    }

    res = handle(event, None)

    exp = {
        "statusCode": 400,
        "body": json.dumps({"error": "Unsupported query param"})
    }
    assert res == exp
