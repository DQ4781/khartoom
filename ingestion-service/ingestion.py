########
#  V2 Ingestion
#########
import json
import boto3

dynamodb = boto3.resource("dynamodb")
user_config_table = dynamodb.Table("UserConfiguration")
api_key_table = dynamodb.Table("UserAPIKeyTable")


# Initialize AWS Lambda client
lambda_client = boto3.client("lambda")


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        email = body.get("Email")
        api_key = body.get("APIKey")
        data = body.get("Data")

        if not email or not api_key or not data:
            return {
                "statusCode": 400,
                "body": json.dumps(f"Missing required ingestion fields."),
            }
    except (json.JSONDecodeError, KeyError) as e:
        return {"statusCode": 400, "body": json.dumps(f"Invalid request: {str(e)}")}

    # Validate the API key
    if not validate_api_key(api_key, email):
        return {"statusCode": 403, "body": json.dumps(f"Invalid API key.")}

    # Fetch configuration from our DynamoDB table
    try:
        response = user_config_table.get_item(Key={"Email": email})
        if "Item" not in response:
            return {
                "statusCode": 404,
                "body": json.dumps("User configuration not found"),
            }

        try:
            config = response["Item"]
            s3_bucket = config.get("S3BucketARN")
            jq_expression = config.get("JQExpression")

            if not s3_bucket or not jq_expression:
                return {
                    "statusCode": 400,
                    "body": json.dumps(f"Missing required config table fields."),
                }
        except (json.JSONDecodeError, KeyError) as e:
            return {
                "statusCode": 400,
                "body": json.dumps(f"Invalid configuration: {str(e)}"),
            }

        # Log the data and configuration for now
        print(f"Received data: {data}")
        print(
            f"Email: {email}\nS3 Bucket ARN = {s3_bucket}\nJQ Expression = {jq_expression}"
        )

        # Prepare payload for transformation lambda
        transformation_payload = {
            "data": data,
            "JQExpression": jq_expression,
            "S3BucketARN": s3_bucket,
        }

        # Invoke transformation lambda
        lambda_response = lambda_client.invoke(
            FunctionName="transformationFunctionImage",
            InvocationType="RequestResponse",
            Payload=json.dumps(transformation_payload),
        )

        # Log response from Transformation Lambda
        transformation_result = json.loads(
            lambda_response["Payload"].read().decode("utf-8")
        )
        print(f"Transformation result: {transformation_result}")

        return {
            "statusCode": 200,
            "body": json.dumps("Data received and config fetched!"),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error fetching config: {str(e)}"),
        }


def validate_api_key(api_key, email):
    try:
        response = api_key_table.get_item(Key={"Email": email})
        if "Item" in response and response["Item"].get("APIKey") == api_key:
            return True
        return False
    except Exception as e:
        print(f"Error validating API key for email: {email}: {e}")
        return False
