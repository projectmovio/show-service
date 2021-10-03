import json

import episodes_db
import decimal_encoder
import logger
from api.shows import tvmaze_api

log = logger.get_logger("episodes_by_id")


class HttpError(object):
    pass


def handle(event, context):
    log.debug(f"Received event: {event}")

    show_id = event["pathParameters"].get("id")
    episode_id = event["pathParameters"].get("episode_id")
    query_params = event.get("queryStringParameters")

    try:
        res = episodes_db.get_episode_by_id(show_id, episode_id)

        if "api_name" in query_params:
            if query_params["api_name"] == "tvmaze" and "tvmaze_id" in res:
                api_res = tvmaze_api.get_episode(res["tvmaze_id"])
                res = {**res, **api_res}
    except (episodes_db.NotFoundError, episodes_db.InvalidAmountOfEpisodes):
        return {"statusCode": 404}

    return {
        "statusCode": 200,
        "body": json.dumps(res, cls=decimal_encoder.DecimalEncoder)
    }
