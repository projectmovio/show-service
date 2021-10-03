import json

import shows_db
import decimal_encoder
import logger
from api.shows import tvmaze_api

log = logger.get_logger("show_by_id")


class HttpError(object):
    pass


def handle(event, context):
    log.debug(f"Received event: {event}")

    show_id = event["pathParameters"].get("id")
    query_params = event.get("queryStringParameters")

    try:
        res = shows_db.get_show_by_id(show_id)

        if "api_name" in query_params:
            if query_params["api_name"] == "tvmaze" and "tvmaze_id" in res:
                api_res = tvmaze_api.get_show(res["tvmaze_id"])
                ep_count = tvmaze_api.get_show_episodes_count(res["tvmaze_id"])
                res = {**res, **api_res, **ep_count}

    except shows_db.NotFoundError:
        return {"statusCode": 404}

    return {
        "statusCode": 200,
        "body": json.dumps(res, cls=decimal_encoder.DecimalEncoder)
    }
