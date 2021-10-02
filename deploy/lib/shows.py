import os
import shutil
import subprocess

from aws_cdk import core
from aws_cdk.aws_apigatewayv2 import HttpApi, HttpMethod, CfnAuthorizer, \
    CfnRoute, \
    HttpIntegration, HttpIntegrationType, PayloadFormatVersion, \
    CorsPreflightOptions, DomainMappingOptions, HttpStage, \
    DomainName
from aws_cdk.aws_certificatemanager import Certificate, ValidationMethod
from aws_cdk.aws_dynamodb import Table, Attribute, AttributeType, BillingMode
from aws_cdk.aws_events import Schedule, Rule
from aws_cdk.aws_iam import Role, ServicePrincipal, PolicyStatement, \
    ManagedPolicy
from aws_cdk.aws_lambda import LayerVersion, Code, Runtime, Function
from aws_cdk.aws_sns import Topic
from aws_cdk.core import Duration
from aws_cdk.aws_events_targets import LambdaFunction

from lib.utils import clean_pycache

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
LAMBDAS_DIR = os.path.join(CURRENT_DIR, "..", "..", "src", "lambdas")
LAYERS_DIR = os.path.join(CURRENT_DIR, "..", "..", "src", "layers")
BUILD_FOLDER = os.path.join(CURRENT_DIR, "..", "..", "build")


class Shows(core.Stack):
    def __init__(self, app: core.App, id: str, domain_name: str,
                 **kwargs) -> None:
        super().__init__(app, id, **kwargs)
        self.domain_name = domain_name
        self.layers = {}
        self.lambdas = {}
        self._create_tables()
        self._create_topic()
        self._create_lambdas_config()
        self._create_layers()
        self._create_lambdas()
        self._create_gateway()

    def _create_tables(self):
        self.shows_table = Table(
            self,
            "shows_table",
            table_name="shows",
            partition_key=Attribute(name="id", type=AttributeType.STRING),
            billing_mode=BillingMode.PAY_PER_REQUEST,
        )
        self.shows_table.add_global_secondary_index(
            partition_key=Attribute(name="tvmaze_id",
                                    type=AttributeType.NUMBER),
            index_name="tvmaze_id"
        )

        self.episodes_table = Table(
            self,
            "episodes_table",
            table_name="shows-eps",
            partition_key=Attribute(name="show_id", type=AttributeType.STRING),
            sort_key=Attribute(name="id", type=AttributeType.STRING),
            billing_mode=BillingMode.PAY_PER_REQUEST,
        )
        self.episodes_table.add_local_secondary_index(
            sort_key=Attribute(name="id", type=AttributeType.STRING),
            index_name="episode_id"
        )
        self.episodes_table.add_global_secondary_index(
            partition_key=Attribute(name="tvmaze_id",
                                    type=AttributeType.NUMBER),
            index_name="tvmaze_id"
        )

    def _create_topic(self):
        self.show_updates_topic = Topic(
            self,
            "shows_updates",
        )

    def _create_lambdas_config(self):
        self.lambdas_config = {
            "api-shows_by_id": {
                "layers": ["utils", "databases"],
                "variables": {
                    "SHOWS_DATABASE_NAME": self.shows_table.table_name,
                    "LOG_LEVEL": "INFO",
                },
                "policies": [
                    PolicyStatement(
                        actions=["dynamodb:GetItem"],
                        resources=[self.shows_table.table_arn]
                    )
                ],
                "timeout": 3,
                "memory": 128
            },
            "api-shows": {
                "layers": ["utils", "databases", "api"],
                "variables": {
                    "SHOWS_DATABASE_NAME": self.shows_table.table_name,
                    "LOG_LEVEL": "INFO",
                },
                "policies": [
                    PolicyStatement(
                        actions=["dynamodb:Query"],
                        resources=[
                            f"{self.shows_table.table_arn}/index/tvmaze_id"]
                    ),
                    PolicyStatement(
                        actions=["dynamodb:UpdateItem"],
                        resources=[self.shows_table.table_arn]
                    ),
                ],
                "timeout": 10,
                "memory": 128
            },
            "api-episodes": {
                "layers": ["utils", "databases"],
                "variables": {
                    "SHOWS_DATABASE_NAME": self.shows_table.table_name,
                    "SHOW_EPISODES_DATABASE_NAME": self.episodes_table.table_name,
                    "LOG_LEVEL": "INFO",
                },
                "policies": [
                    PolicyStatement(
                        actions=["dynamodb:GetItem"],
                        resources=[self.shows_table.table_arn]
                    ),
                    PolicyStatement(
                        actions=["dynamodb:Query"],
                        resources=[
                            f"{self.episodes_table.table_arn}/index/tvmaze_id"]
                    ),
                    PolicyStatement(
                        actions=["dynamodb:UpdateItem"],
                        resources=[self.episodes_table.table_arn]
                    ),
                    PolicyStatement(
                        actions=["dynamodb:GetItem"],
                        resources=[self.episodes_table.table_arn]
                    ),
                ],
                "timeout": 10,
                "memory": 128
            },
            "api-episodes_by_id": {
                "layers": ["utils", "databases"],
                "variables": {
                    "SHOW_EPISODES_DATABASE_NAME": self.episodes_table.table_name,
                    "LOG_LEVEL": "INFO",
                },
                "policies": [
                    PolicyStatement(
                        actions=["dynamodb:Query"],
                        resources=[self.episodes_table.table_arn]
                    ),
                ],
                "timeout": 3,
                "memory": 128
            },
            "cron-update_eps": {
                "layers": ["utils", "databases", "api"],
                "variables": {
                    "SHOWS_DATABASE_NAME": self.episodes_table.table_name,
                    "LOG_LEVEL": "INFO",
                    "UPDATES_TOPIC_ARN": self.show_updates_topic.topic_arn,
                },
                "policies": [
                    PolicyStatement(
                        actions=["dynamodb:GetItem"],
                        resources=[self.episodes_table.table_arn],
                    ),
                    PolicyStatement(
                        actions=["sns:Publish"],
                        resources=[self.show_updates_topic.topic_arn],
                    )
                ],
                "timeout": 3,
                "memory": 128
            },
        }

    def _create_layers(self):
        if os.path.isdir(BUILD_FOLDER):
            shutil.rmtree(BUILD_FOLDER)
        os.mkdir(BUILD_FOLDER)

        for layer in os.listdir(LAYERS_DIR):
            layer_folder = os.path.join(LAYERS_DIR, layer)
            build_folder = os.path.join(BUILD_FOLDER, layer)
            shutil.copytree(layer_folder, build_folder)

            requirements_path = os.path.join(build_folder, "requirements.txt")

            if os.path.isfile(requirements_path):
                packages_folder = os.path.join(build_folder, "python", "lib",
                                               "python3.8", "site-packages")
                # print(f"Installing layer requirements to target: {os.path.abspath(packages_folder)}")
                subprocess.check_output(
                    ["pip", "install", "-r", requirements_path, "-t",
                     packages_folder])
                clean_pycache()

            self.layers[layer] = LayerVersion(
                self,
                layer,
                layer_version_name=f"shows-{layer}",
                code=Code.from_asset(path=build_folder),
                compatible_runtimes=[Runtime.PYTHON_3_8],
            )

    def _create_lambdas(self):
        for root, dirs, files in os.walk(LAMBDAS_DIR):
            for f in files:
                if f != "__init__.py":
                    continue

                parent_folder = os.path.basename(os.path.dirname(root))
                lambda_folder = os.path.basename(root)
                name = f"{parent_folder}-{lambda_folder}"
                lambda_config = self.lambdas_config[name]

                layers = []
                for layer_name in lambda_config["layers"]:
                    layers.append(self.layers[layer_name])

                lambda_role = Role(
                    self,
                    f"{name}_role",
                    assumed_by=ServicePrincipal(service="lambda.amazonaws.com")
                )
                for policy in lambda_config["policies"]:
                    lambda_role.add_to_policy(policy)
                lambda_role.add_managed_policy(
                    ManagedPolicy.from_aws_managed_policy_name(
                        "service-role/AWSLambdaBasicExecutionRole"))

                self.lambdas[name] = Function(
                    self,
                    name,
                    code=Code.from_asset(root),
                    handler="__init__.handle",
                    runtime=Runtime.PYTHON_3_8,
                    layers=layers,
                    function_name=name,
                    environment=lambda_config["variables"],
                    role=lambda_role,
                    timeout=Duration.seconds(lambda_config["timeout"]),
                    memory_size=lambda_config["memory"],
                )

        Rule(
            self,
            "update_eps",
            schedule=Schedule.cron(hour="2", minute="10"),
            targets=[
                LambdaFunction(self.lambdas["cron-update_eps"])]
        )

    def _create_gateway(self):
        cert = Certificate(
            self,
            "certificate",
            domain_name=self.domain_name,
            validation_method=ValidationMethod.DNS
        )
        domain_name = DomainName(
            self,
            "domain_name",
            certificate=cert,
            domain_name=self.domain_name,
        )

        http_api = HttpApi(
            self,
            "shows_gateway",
            create_default_stage=False,
            api_name="shows",
            cors_preflight=CorsPreflightOptions(
                allow_methods=[HttpMethod.GET, HttpMethod.POST],
                allow_origins=["https://moshan.tv", "https://beta.moshan.tv"],
                allow_headers=["authorization", "content-type"]
            )
        )

        authorizer = CfnAuthorizer(
            self,
            "cognito",
            api_id=http_api.http_api_id,
            authorizer_type="JWT",
            identity_source=["$request.header.Authorization"],
            name="cognito",
            jwt_configuration=CfnAuthorizer.JWTConfigurationProperty(
                audience=["68v5rahd0sdvrmf7fgbq2o1a9u"],
                issuer="https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_sJ3Y4kSv6"
            )
        )

        routes = {
            "get_shows": {
                "method": "GET",
                "route": "/shows",
                "target_lambda": self.lambdas["api-shows"]
            },
            "post_shows": {
                "method": "POST",
                "route": "/shows",
                "target_lambda": self.lambdas["api-shows"]
            },
            "get_shows_by_id": {
                "method": "GET",
                "route": "/shows/{id}",
                "target_lambda": self.lambdas["api-shows_by_id"]
            },
            "get_episodes": {
                "method": "GET",
                "route": "/episodes",
                "target_lambda": self.lambdas["api-episodes"]
            },
            "post_episodes": {
                "method": "POST",
                "route": "/shows/{id}/episodes",
                "target_lambda": self.lambdas["api-episodes"]
            },
            "get_episodes_by_id": {
                "method": "GET",
                "route": "/shows/{id}/episodes/{episode_id}",
                "target_lambda": self.lambdas["api-episodes_by_id"]
            },
        }

        for r in routes:
            integration = HttpIntegration(
                self,
                f"{r}_integration",
                http_api=http_api,
                integration_type=HttpIntegrationType.LAMBDA_PROXY,
                integration_uri=routes[r]["target_lambda"].function_arn,
                method=getattr(HttpMethod, routes[r]["method"]),
                payload_format_version=PayloadFormatVersion.VERSION_2_0,
            )
            CfnRoute(
                self,
                r,
                api_id=http_api.http_api_id,
                route_key=f"{routes[r]['method']} {routes[r]['route']}",
                authorization_type="JWT",
                authorizer_id=authorizer.ref,
                target="integrations/" + integration.integration_id
            )

            routes[r]["target_lambda"].add_permission(
                f"{r}_apigateway_invoke",
                principal=ServicePrincipal("apigateway.amazonaws.com"),
                source_arn=f"arn:aws:execute-api:{self.region}:{self.account}:{http_api.http_api_id}/*"
            )

        HttpStage(
            self,
            "live",
            http_api=http_api,
            auto_deploy=True,
            stage_name="live",
            domain_mapping=DomainMappingOptions(
                domain_name=domain_name,
            )
        )
