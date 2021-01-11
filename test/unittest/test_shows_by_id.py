import pytest

from api.shows_by_id import handle


def test_handler(mocked_shows_db):
    exp_item = {
        "id": "123",
        "title": "twin peaks",
    }
    mocked_shows_db.table.get_item.return_value = {"Item": exp_item}
    event = {
        "pathParameters": {
            "id": "123"
        }
    }

    res = handle(event, None)

    exp = {'body': '{"id": "123", "title": "twin peaks"}', 'statusCode': 200}
    assert res == exp


def test_handler_not_found(mocked_shows_db):
    mocked_shows_db.table.get_item.side_effect = mocked_shows_db.NotFoundError
    event = {
        "pathParameters": {
            "ids": "123"
        }
    }

    res = handle(event, None)

    exp = {'statusCode': 404}
    assert res == exp
