import json

import episodes_db
import decimal_encoder
import logger
import tvmaze

log = logger.get_logger("episodes_by_id")

tvmaze_api = tvmaze.TvMazeApi()


class HttpError(object):
    pass


def handle(event, context):
    log.debug(f"Received event: {event}")

    show_id = event["pathParameters"].get("id")
    episode_id = event["pathParameters"].get("episode_id")
    query_params = event.get("queryStringParameters")

    try:
        res = episodes_db.get_episode_by_id(show_id, episode_id)

        if query_params is not None and "api_name" in query_params:
            if query_params["api_name"] == "tvmaze" and "tvmaze_id" in res:
                api_res = tvmaze_api.get_episode(res["tvmaze_id"])
                res["is_special"] = api_res["type"] != "regular"
                res = {**res, "tvmaze_api": {**api_res} }
    except (episodes_db.NotFoundError, episodes_db.InvalidAmountOfEpisodes):
        return {"statusCode": 404}
    except tvmaze.HTTPError as e:
        return {"statusCode": e.code}
    return {
        "statusCode": 200,
        "body": json.dumps(res, cls=decimal_encoder.DecimalEncoder)
    }
