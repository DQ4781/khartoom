import json
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("UserConfiguration")


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
        s3_bucket = config["S3BucketName"]
        jq_expression = config["JQExpression"]

        # Log the data and configuration for now
        print(f"Received data: {data}")
        print(f"User config: S3 Bucket = {s3_bucket}, JQ Expression = {jq_expression}")

        return {
            "statusCode": 200,
            "body": json.dumps("Data received and config fetched!"),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error fetching config: {str(e)}"),
        }
