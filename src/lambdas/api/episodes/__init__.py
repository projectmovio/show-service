import json
import os
from json import JSONDecodeError

import decimal_encoder
import episodes_db
import logger
import schema
import shows_db
import tvmaze

sqs_queue = None

log = logger.get_logger("show")

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
POST_SCHEMA_PATH = os.path.join(CURRENT_DIR, "post.json")

tvmaze_api = tvmaze.TvMazeApi()


class Error(Exception):
    pass


class UnsupportedMethod(Error):
    pass


def handle(event, context):
    log.debug(f"Received event: {event}")

    method = event["requestContext"]["http"]["method"]

    if method == "POST":
        show_id = event.get("pathParameters", {})
        body = event.get("body")
        return _post_episode(show_id, body)
    elif method == "GET":
        query_params = event.get("queryStringParameters")
        return _get_episode_by_api_id(query_params)
    else:
        raise UnsupportedMethod()


def _post_episode(path_params, body):
    if "id" not in path_params:
        return {
            "statusCode": 400,
            "body": "Missing id query param"
        }

    show_id = path_params["id"]

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
        return {"statusCode": 400, "body": json.dumps(
            {"message": "Invalid post schema", "error": str(e)})}

    if body["api_name"] == "tvmaze":
        return _post_tvmaze(show_id, body["api_id"])


def _post_tvmaze(show_id, tvmaze_id):
    try:
        api_res = tvmaze_api.get_episode(tvmaze_id)
        del api_res["id"]
        api_res["is_special"] = api_res["type"] != "regular"
    except tvmaze.HTTPError as e:
        return {
            "statusCode": e.code
        }

    try:
        res = episodes_db.get_episode_by_api_id("tvmaze", int(tvmaze_id))
    except episodes_db.NotFoundError:
        episodes_db.new_episode(show_id, "tvmaze", int(tvmaze_id))
        res = {
            "tvmaze_id": tvmaze_id,
            "id": episodes_db.create_episode_uuid(show_id, tvmaze_id)
        }
    else:
        return {
            "statusCode": 200,
            "body": json.dumps({**res, **api_res}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({**res, **api_res}),
    }


def _get_episode_by_api_id(query_params):
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
            res = episodes_db.get_episode_by_api_id(api_name, api_id)
            api_res = tvmaze_api.get_episode(res["tvmaze_id"])
            del api_res["id"]
            api_res["is_special"] = api_res["type"] != "regular"

            res = {**res, **api_res}
            return {
                "statusCode": 200,
                "body": json.dumps(res, cls=decimal_encoder.DecimalEncoder)
            }
        except (episodes_db.NotFoundError, episodes_db.InvalidAmountOfEpisodes):
            return {"statusCode": 404}
        except tvmaze.HTTPError as e:
            return {"statusCode": e.code}
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Unsupported api_name"})
        }
