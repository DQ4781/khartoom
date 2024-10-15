import json
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("UserConfiguration")

# Initialize AWS Lambda client
lambda_client = boto3.client("lambda")


def lambda_handler(event, context):
    body = json.loads(event["body"])
    user_id = body["UserID"]
    data = body["data"]

    # Fetch configuration from our DynamoDB table
    try:
        response = table.get_item(Key={"UserID": user_id})
        if "Item" not in response:
            return {
                "statusCode": 404,
                "body": json.dumps("User configuration not found"),
            }

        config = response["Item"]
        s3_bucket = config["S3BucketARN"]
        jq_expression = config["JQExpression"]

        # Log the data and configuration for now
        print(f"Received data: {data}")
        print(
            f"User config: S3 Bucket ARN = {s3_bucket}, JQ Expression = {jq_expression}"
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
