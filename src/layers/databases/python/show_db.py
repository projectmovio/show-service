import os
import uuid

import boto3
from boto3.dynamodb.conditions import Key
from dynamodb_json import json_util

import logger

DATABASE_NAME = os.getenv("SHOWS_DATABASE_NAME")
SHOW_UUID_NAMESPACE = uuid.UUID("6045673a-9dd2-451c-aa58-d94a217b993a")

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


def new_show(show_info):
    show_id = create_show_uuid(show_info["id"])
    update_show(show_id, show_info)

    return show_id


def create_show_uuid(tvmaze_id):
    return str(uuid.uuid5(SHOW_UUID_NAMESPACE, str(tvmaze_id)))


def update_show(show_id, data):
    items = ','.join(f'#{k}=:{k}' for k in data)
    update_expression = f"SET {items}"
    expression_attribute_names = {f'#{k}': k for k in data}
    expression_attribute_values = {f':{k}': v for k, v in data.items()}

    log.debug("Running update_item")
    log.debug(f"Update expression: {update_expression}")
    log.debug(f"Expression attribute names: {expression_attribute_names}")
    log.debug(f"Expression attribute values: {expression_attribute_values}")

    _get_table().update_item(
        Key={"id": show_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values
    )


def get_show_by_id(show_id):
    res = _get_table().get_item(Key={"id": show_id})

    if "Item" not in res:
        raise NotFoundError(f"Show with id: {show_id} not found")

    return res["Item"]


def show_by_broadcast_generator(day_of_week, limit=100):
    paginator = _get_client().get_paginator('query')

    page_iterator = paginator.paginate(
        TableName=DATABASE_NAME,
        IndexName="broadcast_day",
        KeyConditionExpression="broadcast_day=:day_of_week",
        ExpressionAttributeValues={":day_of_week": {"S": str(day_of_week)}},
        Limit=limit,
        ScanIndexForward=False
    )

    for p in page_iterator:
        for i in p["Items"]:
            yield json_util.loads(i)
