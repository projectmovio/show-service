import pytest


def test_get_show_by_tvmaze_id_not_found(mocked_show_db):
    mocked_show_db.table.query.return_value = {
        "Items": []
    }

    with pytest.raises(mocked_show_db.NotFoundError):
        mocked_show_db.get_show_by_tvmaze_id("123")


def test_get_show_by_id_not_found(mocked_show_db):
    mocked_show_db.table.get_item.return_value = {
        "Items": []
    }

    with pytest.raises(mocked_show_db.NotFoundError):
        mocked_show_db.get_show_by_id("123")