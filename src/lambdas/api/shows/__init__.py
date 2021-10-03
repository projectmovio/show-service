import json
import os
from json import JSONDecodeError

import decimal_encoder
import logger
import schema
import shows_db
from tvmaze import TvMazeApi

sqs_queue = None

log = logger.get_logger("show")

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
POST_SCHEMA_PATH = os.path.join(CURRENT_DIR, "post.json")

tvmaze_api = TvMazeApi()


class Error(Exception):
    pass


class UnsupportedMethod(Error):
    pass


def handle(event, context):
    log.debug(f"Received event: {event}")

    method = event["requestContext"]["http"]["method"]

    if method == "POST":
        body = event.get("body")
        return _post_show(body)
    elif method == "GET":
        query_params = event.get("queryStringParameters")
        return _get_show_by_api_id(query_params)
    else:
        raise UnsupportedMethod()


def _post_show(body):
    try:
        body = json.loads(body)
    except (TypeError, JSONDecodeError):
        log.debug(f"Invalid body: {body}")
        return {
            "statusCode": 400,
            "body": "Invalid post body"
        }

    try:
        schema.validate_schema(POST_SCHEMA_PATH, body)
    except schema.ValidationException as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Invalid post schema",
                "error": str(e)
            })
        }

    if body["api_name"] == "tvmaze":
        return _post_tvmaze(body["api_id"])


def _post_tvmaze(tvmaze_id):
    try:
        shows_db.get_show_by_api_id("tvmaze", int(tvmaze_id))
    except shows_db.NotFoundError:
        pass
    else:
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"id": shows_db.create_show_uuid("tvmaze", tvmaze_id)})
        }

    shows_db.new_show("tvmaze", int(tvmaze_id))

    return {
        "statusCode": 200,
        "body": json.dumps(
            {"id": shows_db.create_show_uuid("tvmaze", tvmaze_id)})
    }


def _get_show_by_api_id(query_params):
    if not query_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Please specify query parameters"})
        }

    if "api_id" not in query_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing api_id query parameter"})
        }

    if "api_name" not in query_params:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing api_name query parameter"})
        }

    api_id = int(query_params["api_id"])
    api_name = query_params["api_name"]

    if api_name in ["tvmaze"]:
        try:
            res = shows_db.get_show_by_api_id(api_name, api_id)
            api_res = tvmaze_api.get_show(api_id)
            ep_count = tvmaze_api.get_show_episodes_count(api_id)
            res = {**res, **api_res, **ep_count}
            return {
                "statusCode": 200,
                "body": json.dumps(res, cls=decimal_encoder.DecimalEncoder)
            }
        except shows_db.NotFoundError:
            return {"statusCode": 404}
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Unsupported api_name"})
        }
