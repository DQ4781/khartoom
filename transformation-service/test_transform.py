import unittest
import json
from transformation import lambda_handler


class TestTransformationLambda(unittest.TestCase):

    def test_successful_transform(self):
        event = {
            "data": {"key": "value"},
            "JQExpression": ".key",
            "S3BucketARN": "arn:aws:s3:::my-test-bucket",
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("value", response["body"])

    def test_missing_data(self):
        event = {"JQExpression": ".key", "S3BucketARN": "arn:aws:s3:::my-test-bucket"}
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Error during transformation: 'data'", response["body"])

    def test_missing_jq_expression(self):
        event = {"data": {"key": "value"}, "S3BucketARN": "arn:aws:s3:::my-test-bucket"}
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Error during transformation: 'JQExpression'", response["body"])

    def test_missing_s3_arn(self):
        event = {"data": {"key": "value"}, "JQExpression": ".key"}
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Error during transformation: 'S3BucketARN'", response["body"])

    def test_jq_execution_error(self):
        event = {
            "data": {"key": "value"},
            "JQExpression": "thisisnotavalidjqexpression",
            "S3BucketARN": "arn:aws:s3:::my-test-bucket",
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Error executing jq", response["body"])


if __name__ == "__main__":
    unittest.main()
