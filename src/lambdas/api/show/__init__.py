import json
from json import JSONDecodeError

import logger
import show_db

sqs_queue = None

log = logger.get_logger("show")


class Error(Exception):
    pass


class UnsupportedMethod(Error):
    pass


def handle(event, context):
    log.debug(f"Received event: {event}")

    method = event["requestContext"]["http"]["method"]

    query_params = event.get("queryStringParameters")
    if not query_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Please specify query parameters"})
        }

    tvmaze_id = query_params.get("tvmaze_id")

    if method == "POST":
        body = event.get("body")
        return _post_show(tvmaze_id, body)
    else:
        raise UnsupportedMethod()


def _post_show(tvmaze_id, body):
    if tvmaze_id is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Please specify the 'tvmaze_id' query parameter"})
        }

    try:
        body = json.loads(body)
    except (TypeError, JSONDecodeError):
        log.debug(f"Invalid body: {body}")
        return {
            "statusCode": 400,
            "body": "Invalid post body"
        }

    try:
        show_db.get_show_by_tvmaze_id(int(tvmaze_id))
    except show_db.NotFoundError:
        pass
    else:
        return {
            "statusCode": 200,
            "body": json.dumps({"show_id": show_db.create_show_uuid(tvmaze_id)})
        }

    show_db.new_show(body)

    return {
        "statusCode": 200,
        "body": json.dumps({"show_id": show_db.create_show_uuid(tvmaze_id)})
    }