import json
from configuration import lambda_handler


def test_save_configuration():
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
