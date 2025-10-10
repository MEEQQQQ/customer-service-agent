#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.core_stack import CoreStack
from stacks.ml_stack import MLStack
from stacks.api_stack import ApiStack
from stacks.web_stack import WebStack

app = cdk.App()

# Core infrastructure
core_stack = CoreStack(app, "CustomerServiceCore")

# ML services
ml_stack = MLStack(app, "CustomerServiceML", 
                   storage_bucket=core_stack.storage_bucket)

# API and Lambda functions
api_stack = ApiStack(app, "CustomerServiceApi",
                     storage_bucket=core_stack.storage_bucket,
                     rekognition_project_arn=ml_stack.rekognition_project_arn,
                     bedrock_agent_id=ml_stack.bedrock_agent_id)

# Web client hosting
web_stack = WebStack(app, "CustomerServiceWeb",
                     api_url=api_stack.api_url)

app.synth()