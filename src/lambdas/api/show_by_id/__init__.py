import json

import show_db
import decimal_encoder
import logger

log = logger.get_logger("show_by_id")


class HttpError(object):
    pass


def handle(event, context):
    log.debug(f"Received event: {event}")

    show_id = event["pathParameters"].get("id")

    res = show_db.get_show_by_id(show_id)
    return {
        "statusCode": 200,
        "body": json.dumps(res, cls=decimal_encoder.DecimalEncoder)
    }
