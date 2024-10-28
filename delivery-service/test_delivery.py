import unittest
import json
from unittest.mock import patch, MagicMock
from delivery import lambda_handler


class TestDeliveryLambda(unittest.TestCase):

    @patch("delivery.s3_client.put_object")
    def test_successful_delivery(self, mock_put_object):
        # Simulate a successful put_object call
        mock_put_object.return_value = MagicMock()

        event = {
            "TransformedData": {"key": "value"},
            "S3BucketARN": "arn:aws:s3:::my-test-bucket",
        }
        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Data successfully stored", response["body"])

    @patch("delivery.s3_client.put_object")
    def test_empty_transformed_data(self, mock_put_object):
        # Simulate a successful put_object call
        mock_put_object.return_value = MagicMock()

        event = {"TransformedData": {}, "S3BucketARN": "arn:aws:s3:::my-test-bucket"}
        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Data successfully stored", response["body"])

    @patch("delivery.s3_client.put_object", side_effect=Exception("Access Denied"))
    def test_missing_transformed_data(self, mock_put_object):
        event = {"S3BucketARN": "arn:aws:s3:::my-test-bucket"}
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Error storing data in S3", response["body"])

    @patch("delivery.s3_client.put_object", side_effect=Exception("NoSuchBucket"))
    def test_invalid_s3_bucket_arn_format(self, mock_put_object):
        event = {
            "TransformedData": {"key": "value"},
            "S3BucketARN": "invalid-arn-format",
        }
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Error storing data in S3", response["body"])

    @patch(
        "delivery.s3_client.put_object", side_effect=Exception("Missing S3BucketARN")
    )
    def test_missing_s3_bucket_arn(self, mock_put_object):
        event = {"TransformedData": {"key": "value"}}
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Error storing data in S3", response["body"])


if __name__ == "__main__":
    unittest.main()
