import boto3
import uuid
import json

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("UserAPIKeys")


def lambda_handler(event, context):
    try:
        # Extract user email from the event
        user_email = event["request"]["userAttributes"]["email"]
    except (json.JSONDecodeError, KeyError) as e:
        return {
            "statusCode": 400,
            "body": json.dumps(
                f"Unable to retrieve email" + "Invalid request: {str(e)}"
            ),
        }

    # Generate a unique API key
    api_key = str(uuid.uuid4())

    try:
        # Store the API key in DynamoDB
        table.put_item(Item={"Email": user_email, "APIKey": api_key})
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error storing API key in DDB. Error : {str(e)}"),
        }

    # Log the API Key Email pair in CloudWatch
    print(f"API key generated for {user_email}: {api_key}")
