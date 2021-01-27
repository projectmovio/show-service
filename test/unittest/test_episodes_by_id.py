from api.episodes_by_id import handle


def test_handler(mocked_episodes_db):
    exp_item = {
        "show_id": "123",
        "id": "456",
        "title": "episode1",
    }
    mocked_episodes_db.table.query.return_value = {"Items": [exp_item], "Count": 1}
    event = {
        "pathParameters": {
            "id": "123",
            "episode_id": "456"
        }
    }

    res = handle(event, None)

    exp = {
        'body': '{"show_id": "123", "id": "456", "title": "episode1"}',
        'statusCode': 200
    }
    assert res == exp


def test_handler_not_found(mocked_episodes_db):
    mocked_episodes_db.table.query.side_effect = mocked_episodes_db.NotFoundError
    event = {
        "pathParameters": {
            "id": "123",
            "episode_id": "456"
        }
    }

    res = handle(event, None)

    exp = {'statusCode': 404}
    assert res == exp


def test_handler_invalid_amount(mocked_episodes_db):
    mocked_episodes_db.table.query.side_effect = mocked_episodes_db.InvalidAmountOfEpisodes
    event = {
        "pathParameters": {
            "id": "123",
            "episode_id": "456"
        }
    }

    res = handle(event, None)

    exp = {'statusCode': 404}
    assert res == exp
