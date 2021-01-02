import json

import shows_db
import decimal_encoder
import logger

log = logger.get_logger("show_by_id")


class HttpError(object):
    pass


def handle(event, context):
    log.debug(f"Received event: {event}")

    show_id = event["pathParameters"].get("id")

    try:
        res = shows_db.get_show_by_id(show_id)
    except shows_db.NotFoundError:
        return {"statusCode": 404}

    return {
        "statusCode": 200,
        "body": json.dumps(res, cls=decimal_encoder.DecimalEncoder)
    }
