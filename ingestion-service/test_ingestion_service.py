import os
import json
from ingestion import lambda_handler

os.environ["AWS_REGION"] = "us-west-2"
os.environ["AWS_DEFAULT_REGION"] = "us-west-2"


def test_ingestion_service():
    event = {
        "body": json.dumps({"UserID": "test-user", "data": {"message": "Hello World"}})
    }

    # Invoke Lambda Handler
    response = lambda_handler(event, None)

    assert response["statusCode"] == 200
    assert "Data received and config fetched" in response["body"]
