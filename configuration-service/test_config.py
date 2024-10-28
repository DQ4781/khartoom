import unittest
import json
import boto3
import warnings
from moto import mock_aws
from configuration import lambda_handler

warnings.filterwarnings(
    "ignore",
    message=(
        "datetime.datetime.utcnow() is deprecated and scheduled for removal "
        "in a future version. Use timezone-aware objects to represent "
        "datetimes in UTC: datetime.datetime.now(datetime.UTC)."
    ),
    category=DeprecationWarning,
    module="botocore",
)


@mock_aws  # Apply at the class level to mock AWS for all tests
class TestConfigurationService(unittest.TestCase):

    def setUp(self):
        # Set up the mock DynamoDB table
        self.dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
        self.table = self.dynamodb.create_table(
            TableName="UserConfiguration",
            KeySchema=[{"AttributeName": "UserID", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "UserID", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        self.table.wait_until_exists()

    def tearDown(self):
        # Tear down the mock DynamoDB table
        self.table.delete()
        self.table.wait_until_not_exists()

    def test_lambda_handler(self):
        # Create a mock event payload
        event = {
            "body": json.dumps(
                {
                    "UserID": "test-user",
                    "S3BucketARN": "arn:aws:s3:::my-test-bucket",
                    "JQExpression": ".platforms | length",
                }
            )
        }

        # Invoke the lambda handler
        response = lambda_handler(event, None)

        # Verify the response
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Configuration saved!", response["body"])


if __name__ == "__main__":
    unittest.main()
