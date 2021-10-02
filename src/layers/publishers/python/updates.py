import os

import boto3

TOPIC_ARN = os.getenv("UPDATES_TOPIC_ARN")

topic = None


def _get_topic():
    global topic

    if topic is None:
        sns = boto3.resource("sns")
        topic = sns.Topic(TOPIC_ARN)