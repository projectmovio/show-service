import pytest


def test_get_show_by_tvmaze_id_not_found(mocked_shows_db):
    mocked_shows_db.table.query.return_value = {
        "Items": []
    }

    with pytest.raises(mocked_shows_db.NotFoundError):
        mocked_shows_db.get_show_by_api_id("tvmaze", "123")


def test_get_show_by_id_not_found(mocked_shows_db):
    mocked_shows_db.table.get_item.return_value = {
        "Items": []
    }

    with pytest.raises(mocked_shows_db.NotFoundError):
        mocked_shows_db.get_show_by_id("123")