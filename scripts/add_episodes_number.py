import sys

import boto3
import requests
from dynamodb_json import json_util

client = boto3.client("dynamodb")
resource = boto3.resource("dynamodb")

SHOWS_TABLE_NAME = "shows"
SHOWS_TABLE = resource.Table(SHOWS_TABLE_NAME)

paginator = client.get_paginator('scan')

for page in paginator.paginate(TableName=SHOWS_TABLE_NAME):
    for i in page["Items"]:
        item = json_util.loads(i)
        res = requests.get(f"https://api.tvmaze.com/shows/{item['tvmaze_id']}/episodes?specials=1")
        if res.status_code != 200:
            print(res.text)
        episodes = res.json()

        ep_count = 0
        special_count = 0
        for e in episodes:
            if e["type"] == "regular":
                ep_count += 1
            else:
                special_count += 1

        # print(item['tvmaze_id'])
        item["ep_count"] = ep_count
        item["special_count"] = special_count
        print(item)

        SHOWS_TABLE.put_item(Item=item)