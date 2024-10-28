import unittest
import json
from ingestion import lambda_handler


class TestIngestionLambda(unittest.TestCase):

    def test_successful_ingestion(self):
        event = {"body": json.dumps({"UserID": "test-user", "data": {"key": "value"}})}
        response = lambda_handler(event, None)
        self.assertEqual(response["statusCode"], 404)  # Assuming user not found

    def test_missing_user_id(self):
        event_with_missing_user = {"body": json.dumps({"data": {"key": "value"}})}
        response = lambda_handler(event_with_missing_user, None)
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid request", response["body"])

    def test_invalid_json_body(self):
        invalid_event = {"body": "{invalid json"}
        response = lambda_handler(invalid_event, None)
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid request", response["body"])


if __name__ == "__main__":
    unittest.main()
