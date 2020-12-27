import json
import os

import anime_db
import boto3
import decimal_encoder
import logger
import mal

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

    mal_id = query_params.get("mal_id")
    search = query_params.get("search")

    if method == "POST":
        return _post_anime(mal_id)
    elif method == "GET":
        return _search_anime(mal_id, search)
    else:
        raise UnsupportedMethod()


def _post_anime(mal_id):
    if mal_id is None:
        return {
            "statusCode":
            400,
            "body":
            json.dumps(
                {"error": "Please specify the 'mal_id' query parameter"})
        }

    try:
        anime_db.get_anime_by_mal_id(int(mal_id))
    except anime_db.NotFoundError:
        pass
    else:
        return {
            "statusCode": 202,
            "body":
            json.dumps({"anime_id": anime_db.create_anime_uuid(mal_id)})
        }

    _get_sqs_queue().send_message(MessageBody=json.dumps({"mal_id": mal_id}))

    return {
        "statusCode": 202,
        "body": json.dumps({"anime_id": anime_db.create_anime_uuid(mal_id)})
    }


def _search_anime(mal_id, search):
    if search is None and mal_id is None:
        return {
            "statusCode":
            400,
            "body":
            json.dumps({
                "error":
                "Please specify either 'search' or 'mal_id' query parameter"
            })
        }

    if mal_id:
        try:
            res = anime_db.get_anime_by_mal_id(int(mal_id))
        except anime_db.NotFoundError:
            log.debug(f"Anime with mal_id: {mal_id} not found in DB, use API")
        else:
            return {
                "statusCode": 200,
                "body": json.dumps(res, cls=decimal_encoder.DecimalEncoder)
            }

        try:
            res = mal.MalApi().get_anime(mal_id)
        except mal.NotFoundError:
            return {"statusCode": 404}
        except mal.HTTPError:
            return {"statusCode": 503}
        else:
            return {"statusCode": 200, "body": json.dumps(res)}
    elif search:
        try:
            res = mal.MalApi().search(search)
            id_map = anime_db.get_ids(res["items"])
            res["id_map"] = id_map
        except mal.HTTPError as e:
            return {"statusCode": 503, "body": str(e)}
        return {"statusCode": 200, "body": json.dumps(res)}
