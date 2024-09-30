import os
import json
from configuration import lambda_handler
from moto import mock_dynamodb2


os.environ["AWS_REGION"] = "us-west-2"
os.environ["AWS_DEFAULT_REGION"] = "us-west-2"


@mock_dynamodb2
def test_save_configuration():
    # Create a mock DynamoDB instance
    dynamodb = boto3.resource("dynamodb", region_name="us-west-2")

    # Create a mock table (it won't persist but will exist for the test)
    dynamodb.create_table(
        TableName="UserConfiguration",
        KeySchema=[{"AttributeName": "UserID", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "UserID", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )

    event = {
        "body": json.dumps(
            {
                "UserID": "test-user",
                "S3BucketName": "test-bucket",
                "JQExpression": ".data",
            }
        )
    }

    # Invoke Lambda Handler
    response = lambda_handler(event, None)

    # Check response
    assert response["statusCode"] == 200
    assert "Configuration saved!" in response["body"]
