import boto3
import json
import os
from dotenv import load_dotenv

cognito_client = boto3.client("cognito-idp")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("UserAPIKeyTable")

load_dotenv()

USER_POOL_ID = os.getenv("USER_POOL_ID")
APP_CLIENT_ID = os.getenv("APP_CLIENT_ID")


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return {
            "statusCode": 400,
            "body": json.dumps(
                "Invalid request format. Please provide valid JSON in body"
            ),
        }
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return {
            "statusCode": 400,
            "body": json.dumps("Email and password are required"),
        }

    # Authenticate user w/ Cognito
    try:
        response = cognito_client.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=APP_CLIENT_ID,
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters={"USERNAME": email, "PASSWORD": password},
        )

        api_key = get_api_key(email)
        print(f"Here is the apikey: {api_key}")
        if api_key:
            return {"statusCode": 200, "body": json.dumps({"apiKey": api_key})}
        else:
            return {
                "statusCode": 404,
                "body": json.dumps("API key not found for the user."),
            }
    except cognito_client.exceptions.NotAuthorizedException:
        return {"statusCode": 401, "body": json.dumps("Invalid Credentials")}
    except cognito_client.exceptions.UserNotConfirmedException:
        return {
            "statusCode": 403,
            "body": json.dumps("User not confirmed. Please confirm your email"),
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"Error during auth: {str(e)}")}


def get_api_key(email):
    try:
        response = table.get_item(Key={"Email": email})
        print(response)
        if "Item" in response:
            return response["Item"].get("APIKey")
        return None
    except Exception as e:
        print(f"Error fetching API key from DDB: {e}")
        return None
