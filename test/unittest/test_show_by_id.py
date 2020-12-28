import pytest

from api.show_by_id import handle


def test_handler(mocked_show_db):
    exp_item = {
        "id": "123",
        "title": "twin peaks",
    }
    mocked_show_db.table.get_item.return_value = {"Item": exp_item}
    event = {
        "pathParameters": {
            "id": "123"
        }
    }

    res = handle(event, None)

    exp = {'body': '{"id": "123", "title": "twin peaks"}', 'statusCode': 200}
    assert res == exp


def test_handler_not_found(mocked_show_db):
    mocked_show_db.table.get_item.side_effect = mocked_show_db.NotFoundError
    event = {
        "pathParameters": {
            "ids": "123"
        }
    }

    with pytest.raises(mocked_show_db.NotFoundError):
        handle(event, None)
