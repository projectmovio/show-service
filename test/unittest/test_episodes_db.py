import pytest


def test_get_episode_by_api_id_not_found(mocked_episodes_db):
    mocked_episodes_db.table.query.return_value = {
        "Items": []
    }

    with pytest.raises(mocked_episodes_db.NotFoundError):
        mocked_episodes_db.get_episode_by_api_id("tvmaze", "123")


def test_get_episode_by_api_id_invalid_count(mocked_episodes_db):
    mocked_episodes_db.table.query.return_value = {
        "Items": [{"episode_id": "123"}],
        "Count": 2
    }

    with pytest.raises(mocked_episodes_db.InvalidAmountOfEpisodes):
        mocked_episodes_db.get_episode_by_api_id("tvmaze", "123")


def test_get_episode_by_id_not_found(mocked_episodes_db):
    mocked_episodes_db.table.query.return_value = {
        "Items": []
    }

    with pytest.raises(mocked_episodes_db.NotFoundError):
        mocked_episodes_db.get_episode_by_id("456", "123")

