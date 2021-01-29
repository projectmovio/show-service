import json
import os
from json import JSONDecodeError

import decimal_encoder
import episodes_db
import logger
import schema
import shows_db

sqs_queue = None

log = logger.get_logger("show")

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
POST_SCHEMA_PATH = os.path.join(CURRENT_DIR, "post.json")


class Error(Exception):
    pass


class UnsupportedMethod(Error):
    pass


def handle(event, context):
    log.debug(f"Received event: {event}")

    method = event["requestContext"]["http"]["method"]
    query_params = event.get("queryStringParameters")

    if method == "POST":
        body = event.get("body")
        return _post_episode(query_params, body)
    elif method == "GET":
        return _get_episode_by_api_id(query_params)
    else:
        raise UnsupportedMethod()


def _post_episode(query_params, body):
    if query_params is None or "id" not in query_params:
        return {
            "statusCode": 400,
            "body": "Missing id query param"
        }

    show_id = query_params["id"]

    try:
        shows_db.get_show_by_id(show_id)
    except shows_db.NotFoundError:
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "Show not found"})
        }

    try:
        body = json.loads(body)
    except (TypeError, JSONDecodeError):
        log.debug(f"Invalid body: {body}")
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid post body"})
        }

    try:
        schema.validate_schema(POST_SCHEMA_PATH, body)
    except schema.ValidationException as e:
        return {"statusCode": 400, "body": json.dumps({"message": "Invalid post schema", "error": str(e)})}

    if body["api_name"] == "tvmaze":
        return _post_tvmaze(show_id, body["api_id"])


def _post_tvmaze(show_id, tvmaze_id):
    try:
        episodes_db.get_episode_by_api_id("tvmaze", int(tvmaze_id))
    except episodes_db.NotFoundError:
        pass
    else:
        return {
            "statusCode": 200,
            "body": json.dumps({"id": episodes_db.create_episode_uuid(show_id, tvmaze_id)})
        }

    episode_id = episodes_db.new_episode(show_id, "tvmaze", int(tvmaze_id))

    return {
        "statusCode": 200,
        "body": json.dumps({"id": episode_id})
    }


def _get_episode_by_api_id(query_params):
    if not query_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Please specify query parameters"})
        }

    if "tvmaze_id" in query_params:
        try:
            res = episodes_db.get_episode_by_api_id("tvmaze", int(query_params["tvmaze_id"]))
            return {"statusCode": 200, "body": json.dumps(res, cls=decimal_encoder.DecimalEncoder)}
        except (episodes_db.NotFoundError, episodes_db.InvalidAmountOfEpisodes):
            return {"statusCode": 404}
    else:
        return {"statusCode": 400, "body": json.dumps({"error": "Unsupported query param"})}