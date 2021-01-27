import os
import uuid

import boto3
from boto3.dynamodb.conditions import Key
from dynamodb_json import json_util

import logger

DATABASE_NAME = os.getenv("SHOW_EPISODES_DATABASE_NAME")

table = None
client = None

log = logger.get_logger(__name__)


class Error(Exception):
    pass


class NotFoundError(Error):
    pass


def _get_table():
    global table
    if table is None:
        table = boto3.resource("dynamodb").Table(DATABASE_NAME)
    return table


def _get_client():
    global client
    if client is None:
        client = boto3.client("dynamodb")
    return client


def new_episode(show_id, api_name, api_id):
    episode_id = _create_episode_uuid(show_id, str(api_id))

    data = {
        "show_id": show_id,
        f"{api_name}_id": api_id
    }
    update_episode(episode_id, data)

    return episode_id


def _create_episode_uuid(show_id, api_id):
    return str(uuid.uuid5(uuid.UUID(show_id), str(api_id)))


def update_episode(episode_id, data):
    items = ','.join(f'#{k}=:{k}' for k in data)
    update_expression = f"SET {items}"
    expression_attribute_names = {f'#{k}': k for k in data}
    expression_attribute_values = {f':{k}': v for k, v in data.items()}

    log.debug("Running update_item")
    log.debug(f"Update expression: {update_expression}")
    log.debug(f"Expression attribute names: {expression_attribute_names}")
    log.debug(f"Expression attribute values: {expression_attribute_values}")

    _get_table().update_item(
        Key={"id": episode_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values
    )


def get_episode_by_id(episode_id):
    res = _get_table().get_item(Key={"id": episode_id})

    if "Item" not in res:
        raise NotFoundError(f"Episode with id: {episode_id} not found")

    return res["Item"]


def get_episode_by_api_id(api_name, api_id):
    key_name = f"{api_name}_id"
    res = _get_table().query(
        IndexName=key_name,
        KeyConditionExpression=Key(key_name).eq(api_id)
    )
    log.debug(f"get_episode_by_api_id res: {res}")

    if not res["Items"]:
        raise NotFoundError(f"Episode with {key_name}: {api_id} not found")

    return res["Items"][0]