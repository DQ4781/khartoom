########
#  V2 Ingestion
#########
import json
import boto3

# Initialize resources
dynamodb = boto3.resource("dynamodb")
user_config_table = dynamodb.Table("UserConfigurationTable")
lambda_client = boto3.client("lambda")


def lambda_handler(event, context):
    for record in event["Records"]:
        try:
            print(
                "Processing SQS message ID:", record.get("messageId", "No ID")
            )  # Log the SQS message ID

            # Parse the message body
            message_body = json.loads(record["body"])
            print("Message body:", message_body)  # Log the parsed message body

            # Extract email and data from the message
            email = message_body.get("Email")
            data = message_body.get("Data")
            print(f"Extracted Email: {email}, Data: {data}")  # Log extracted fields

            # Check for missing fields
            if not email or not data:
                print("Error: Missing required fields (Email or Data) in message body")
                continue

            # Fetch user configuration from DynamoDB
            print(f"Fetching configuration for email: {email}")
            response = user_config_table.get_item(Key={"Email": email})
            print(
                "DynamoDB get_item response:", response
            )  # Log the raw response from DynamoDB

            if "Item" not in response:
                print(f"Configuration not found for email: {email}")
                continue

            config = response["Item"]
            s3_bucket = config.get("S3BucketARN")
            jq_expression = config.get("JQExpression")
            print(
                f"Fetched config - S3BucketARN: {s3_bucket}, JQExpression: {jq_expression}"
            )  # Log the configuration details

            # Check if required configuration fields are present
            if not s3_bucket or not jq_expression:
                print(f"Error: Missing S3 bucket or JQ expression for email: {email}")
                continue

            # Log the data and configuration for processing
            print(f"Starting transformation for email: {email}")
            print(f"Data: {data}")
            print(f"S3 Bucket ARN: {s3_bucket}, JQ Expression: {jq_expression}")

            # Prepare payload for transformation Lambda
            transformation_payload = {
                "data": data,
                "JQExpression": jq_expression,
                "S3BucketARN": s3_bucket,
            }
            print(
                "Transformation payload:", transformation_payload
            )  # Log the payload sent to the transformation Lambda

            # Invoke transformation Lambda
            lambda_response = lambda_client.invoke(
                FunctionName="transformationFunctionImage",
                InvocationType="RequestResponse",
                Payload=json.dumps(transformation_payload),
            )
            print(
                "Transformation Lambda response metadata:",
                lambda_response["ResponseMetadata"],
            )  # Log metadata of the Lambda response

            # Parse and log the result from the transformation Lambda
            transformation_result = json.loads(
                lambda_response["Payload"].read().decode("utf-8")
            )
            print(f"Transformation result for email {email}: {transformation_result}")

        except Exception as e:
            print(
                f"Error processing message (SQS message ID: {record.get('messageId', 'No ID')}): {str(e)}"
            )
            print(
                "Exception details:", e, type(e)
            )  # Additional detail about the exception type
