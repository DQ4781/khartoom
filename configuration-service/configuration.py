########
#  V2 Configuration
#########
import os
import json
import boto3

dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-west-2"))
user_config_table = dynamodb.Table("UserConfigurationTable")
api_key_table = dynamodb.Table("UserAPIKeyTable")


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        email = body.get("Email")
        api_key = body.get("APIKey")
        s3_bucket = body.get("S3BucketARN")
        jq_expression = body.get("JQExpression")

        if not email or not api_key or not s3_bucket or not jq_expression:
            return {
                "statusCode": 400,
                "body": json.dumps(f"Missing required configuration fields."),
            }
    except (json.JSONDecodeError, KeyError) as e:
        return {
            "statusCode": 400,
            "body": json.dumps(f"Invalid request format: {str(e)}"),
        }

    # Validate the API key
    if not validate_api_key(api_key, email):
        return {"statusCode": 403, "body": json.dumps(f"Invalid API key.")}

    # Store configuration
    try:
        user_config_table.put_item(
            Item={
                "Email": email,
                "S3BucketARN": s3_bucket,
                "JQExpression": jq_expression,
            }
        )
        return {"statusCode": 200, "body": json.dumps("Configuration saved!")}
    except Exception as e:
        print(f"Error putting configuration for email {email}: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error saving configuration: {str(e)}"),
        }


def validate_api_key(api_key, email):
    try:
        response = api_key_table.get_item(Key={"Email": email})
        if "Item" in response and response["Item"].get("APIKey") == api_key:
            return True
        return False
    except Exception as e:
        print(f"Error validating API key: {e}")
        return False
