import os

from aws_cdk import core

from lib.shows import Shows

app = core.App()

env = {"region": "eu-west-1"}

domain_name = "api.shows.moshan.tv"

Shows(app, "shows", domain_name, env=env)

app.synth()
