import boto3
import json

cloudwatch = boto3.client('cloudwatch')

dashboard_body = {
    "widgets": [
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/Lambda", "Duration", {"stat": "Average"}],
                    [".", "Invocations", {"stat": "Sum"}],
                    [".", "Errors", {"stat": "Sum"}]
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Lambda Performance",
                "yAxis": {"left": {"label": "Count"}}
            }
        },
        {
            "type": "metric",
            "properties": {
                "metrics": [
                    ["AWS/ApiGateway", "Count", {"stat": "Sum"}],
                    [".", "4XXError", {"stat": "Sum"}],
                    [".", "5XXError", {"stat": "Sum"}]
                ],
                "period": 300,
                "stat": "Sum",
                "region": "us-east-1",
                "title": "API Gateway Metrics"
            }
        }
    ]
}

try:
    response = cloudwatch.put_dashboard(
        DashboardName='CustomerServiceMetrics',
        DashboardBody=json.dumps(dashboard_body)
    )
    print("Dashboard created successfully!")
    print(f"Dashboard ARN: {response['DashboardValidationMessages']}")
except Exception as e:
    print(f"Error creating dashboard: {e}")
