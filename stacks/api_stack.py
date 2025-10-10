from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    Duration,
    CfnOutput
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, 
                 storage_bucket: s3.Bucket, 
                 ticket_table: dynamodb.Table,
                 rekognition_project_arn: str,
                 bedrock_agent_id: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda layer for common dependencies (optional)
        try:
            lambda_layer = _lambda.LayerVersion(
                self, "CommonLayer",
                code=_lambda.Code.from_asset("lambda_layer"),
                compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
                description="Common dependencies for Lambda functions"
            )
            layers = [lambda_layer]
        except:
            # If layer creation fails, continue without it
            layers = []

        # Environment variables for all Lambdas
        common_env = {
            "STORAGE_BUCKET": storage_bucket.bucket_name,
            "REKOGNITION_PROJECT_ARN": rekognition_project_arn,
            "BEDROCK_AGENT_ID": bedrock_agent_id
        }

        # Upload handler Lambda
        upload_handler = _lambda.Function(
            self, "UploadHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="upload_handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda_functions/upload_handler"),
            timeout=Duration.seconds(30),
            environment={
                **common_env,
                "TICKET_TABLE": ticket_table.table_name
            },
            layers=layers
        )

        # Transcribe handler Lambda
        transcribe_handler = _lambda.Function(
            self, "TranscribeHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="transcribe_handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda_functions/transcribe_handler"),
            timeout=Duration.seconds(60),
            environment=common_env,
            layers=layers
        )

        # Image analysis handler Lambda
        image_analysis_handler = _lambda.Function(
            self, "ImageAnalysisHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="image_analysis_handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda_functions/image_analysis_handler"),
            timeout=Duration.seconds(30),
            environment=common_env,
            layers=layers
        )

        # Bedrock agent handler Lambda
        bedrock_handler = _lambda.Function(
            self, "BedrockHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="bedrock_handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda_functions/bedrock_handler"),
            timeout=Duration.seconds(60),
            environment={
                **common_env,
                "TICKET_TABLE_NAME": ticket_table.table_name
            },
            layers=layers
        )

        # Action executor Lambda
        action_executor = _lambda.Function(
            self, "ActionExecutor",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="action_executor.lambda_handler",
            code=_lambda.Code.from_asset("lambda_functions/action_executor"),
            timeout=Duration.seconds(30),
            environment=common_env,
            layers=layers
        )
        
        # Audio proxy Lambda
        audio_proxy = _lambda.Function(
            self, "AudioProxy",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="audio_proxy.lambda_handler",
            code=_lambda.Code.from_asset("lambda_functions/audio_proxy"),
            timeout=Duration.seconds(30),
            environment=common_env,
            layers=layers
        )
        
        # Feedback handler Lambda
        feedback_handler = _lambda.Function(
            self, "FeedbackHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="feedback_handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda_functions/feedback_handler"),
            timeout=Duration.seconds(30),
            environment={
                **common_env,
                'FEEDBACK_TABLE': 'performance-thumbsup'
            },
            layers=layers
        )
        
        # Session recap handler Lambda
        session_recap_handler = _lambda.Function(
            self, "SessionRecapHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="session_recap_handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda_functions/session_recap_handler"),
            timeout=Duration.seconds(30),
            environment={
                **common_env,
                'FEEDBACK_TABLE': 'performance-thumbsup',
                'FUNCTION_NAME': 'CustomerServiceApi-BedrockHandler'
            },
            layers=layers
        )

        # Grant S3 permissions to all Lambdas
        for func in [
            upload_handler,
            transcribe_handler,
            image_analysis_handler,
            bedrock_handler,
            action_executor,
            audio_proxy,
            session_recap_handler
        ]:
            storage_bucket.grant_read_write(func)
        
        # Grant DynamoDB permissions to upload_handler and bedrock_handler
        ticket_table.grant_read_write_data(upload_handler)
        ticket_table.grant_read_write_data(bedrock_handler)

        # API Gateway
        api = apigateway.RestApi(
            self, "CustomerServiceApi",
            rest_api_name="Customer Service API",
            description="API for customer service troubleshooting"
        )

        # API endpoints
        upload_integration = apigateway.LambdaIntegration(upload_handler)
        transcribe_integration = apigateway.LambdaIntegration(transcribe_handler)
        image_integration = apigateway.LambdaIntegration(image_analysis_handler)
        bedrock_integration = apigateway.LambdaIntegration(bedrock_handler)
        action_integration = apigateway.LambdaIntegration(action_executor)
        audio_integration = apigateway.LambdaIntegration(audio_proxy)
        feedback_integration = apigateway.LambdaIntegration(feedback_handler)
        recap_integration = apigateway.LambdaIntegration(session_recap_handler)

        # Common CORS configuration
        cors_config = {
            "allow_origins": ["*"],
            "allow_methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key", "X-Amz-Security-Token"],
            "allow_credentials": False
        }

        # Routes with input validation
        upload_resource = api.root.add_resource("upload")
        upload_resource.add_method(
            "POST", 
            upload_integration,
            request_validator=apigateway.RequestValidator(
                self, "UploadValidator",
                rest_api=api,
                validate_request_body=True,
                validate_request_parameters=True
            )
        )
        upload_resource.add_cors_preflight(**cors_config)

        transcribe_resource = api.root.add_resource("transcribe")
        transcribe_resource.add_method(
            "POST", 
            transcribe_integration,
            request_validator=apigateway.RequestValidator(
                self, "TranscribeValidator",
                rest_api=api,
                validate_request_body=True,
                validate_request_parameters=True
            )
        )
        transcribe_resource.add_cors_preflight(**cors_config)

        image_resource = api.root.add_resource("analyze-image")
        image_resource.add_method(
            "POST", 
            image_integration,
            request_validator=apigateway.RequestValidator(
                self, "ImageValidator",
                rest_api=api,
                validate_request_body=True,
                validate_request_parameters=True
            )
        )
        image_resource.add_cors_preflight(**cors_config)

        troubleshoot_resource = api.root.add_resource("troubleshoot")
        troubleshoot_resource.add_method(
            "POST", 
            bedrock_integration,
            request_validator=apigateway.RequestValidator(
                self, "TroubleshootValidator",
                rest_api=api,
                validate_request_body=True,
                validate_request_parameters=True
            )
        )
        troubleshoot_resource.add_cors_preflight(**cors_config)

        execute_action_resource = api.root.add_resource("execute-action")
        execute_action_resource.add_method(
            "POST", 
            action_integration,
            request_validator=apigateway.RequestValidator(
                self, "ActionValidator",
                rest_api=api,
                validate_request_body=True,
                validate_request_parameters=True
            )
        )
        execute_action_resource.add_cors_preflight(**cors_config)
        
        # Audio proxy endpoint
        audio_resource = api.root.add_resource("audio")
        session_resource = audio_resource.add_resource("{session_id}")
        session_resource.add_method("GET", audio_integration)
        session_resource.add_cors_preflight(**cors_config)
        
        # Feedback endpoint
        feedback_resource = api.root.add_resource("feedback")
        feedback_resource.add_method("POST", feedback_integration)
        feedback_resource.add_cors_preflight(**cors_config)
        
        # Session recap endpoint
        recap_resource = api.root.add_resource("session-recap")
        recap_session_resource = recap_resource.add_resource("{session_id}")
        recap_session_resource.add_method("GET", recap_integration)
        recap_session_resource.add_cors_preflight(**cors_config)

        self.api_url = api.url

        # Output API URL
        CfnOutput(
            self, "ApiUrl",
            value=self.api_url,
            description="API Gateway URL"
        )
