import json

import episodes_db
import decimal_encoder
import logger

log = logger.get_logger("episodes_by_id")


class HttpError(object):
    pass


def handle(event, context):
    log.debug(f"Received event: {event}")

    show_id = event["pathParameters"].get("id")
    episode_id = event["pathParameters"].get("episode_id")

    try:
        res = episodes_db.get_episode_by_id(show_id, episode_id)
    except (episodes_db.NotFoundError, episodes_db.InvalidAmountOfEpisodes):
        return {"statusCode": 404}

    return {
        "statusCode": 200,
        "body": json.dumps(res, cls=decimal_encoder.DecimalEncoder)
    }
