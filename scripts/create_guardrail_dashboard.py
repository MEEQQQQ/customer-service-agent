import boto3
import json

cloudwatch = boto3.client('cloudwatch')

def create_guardrail_dashboard():
    """Create CloudWatch Dashboard for Guardrail monitoring"""
    
    dashboard_body = {
        "widgets": [
            {
                "type": "log",
                "properties": {
                    "query": "SOURCE '/aws/lambda/CustomerServiceApi-BedrockHandler'\n| fields @timestamp, @message\n| filter @message like /Guardrail/\n| sort @timestamp desc\n| limit 100",
                    "region": "us-east-1",
                    "title": "Guardrail Activity",
                    "stacked": False
                }
            },
            {
                "type": "log",
                "properties": {
                    "query": "SOURCE '/aws/lambda/CustomerServiceApi-BedrockHandler'\n| fields @timestamp, @message\n| filter @message like /blocked request/\n| sort @timestamp desc\n| limit 50",
                    "region": "us-east-1",
                    "title": "Blocked Requests",
                    "stacked": False
                }
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Errors", {"stat": "Sum", "label": "Lambda Errors"}],
                        [".", "Invocations", {"stat": "Sum", "label": "Total Invocations"}]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Lambda Metrics",
                    "period": 300
                }
            }
        ]
    }
    
    response = cloudwatch.put_dashboard(
        DashboardName='GuardrailMonitoring',
        DashboardBody=json.dumps(dashboard_body)
    )
    
    print("✅ Dashboard created: GuardrailMonitoring")
    print("View at: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=GuardrailMonitoring")

if __name__ == '__main__':
    create_guardrail_dashboard()
