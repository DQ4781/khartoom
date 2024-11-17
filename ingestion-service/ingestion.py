########
#  V2 Ingestion (Updated)
########
import json
import boto3

# Initialize resources
dynamodb = boto3.resource("dynamodb")
user_config_table = dynamodb.Table("UserConfigurationTable")
s3_client = boto3.client("s3")
lambda_client = boto3.client("lambda")


def lambda_handler(event, context):
    for record in event["Records"]:
        try:
            print("Processing SQS message ID:", record.get("messageId", "No ID"))

            # Parse the message body
            message_body = json.loads(record["body"])
            print("Message body:", message_body)

            # Extract email and data or S3 URL
            email = message_body.get("Email")
            data = message_body.get("Data")
            s3_url = message_body.get("S3Url")  # New logic to handle S3 URL

            if not email:
                print("Error: Missing required field 'Email' in message body")
                continue

            # If data is not in the message body, fetch it from S3
            if not data and s3_url:
                print(f"Fetching data from S3 URL: {s3_url}")
                try:
                    bucket_name, key = parse_s3_url(s3_url)
                    s3_response = s3_client.get_object(Bucket=bucket_name, Key=key)
                    data = json.loads(s3_response["Body"].read().decode("utf-8"))
                except Exception as e:
                    print(f"Error fetching data from S3 for URL {s3_url}: {str(e)}")
                    continue

            if not data:
                print("Error: Missing 'Data' and no valid S3 URL provided")
                continue

            # Fetch user configuration from DynamoDB
            print(f"Fetching configuration for email: {email}")
            response = user_config_table.get_item(Key={"Email": email})
            if "Item" not in response:
                print(f"Configuration not found for email: {email}")
                continue

            config = response["Item"]
            s3_bucket = config.get("S3BucketARN")
            jq_expression = config.get("JQExpression")
            print(
                f"Fetched config - S3BucketARN: {s3_bucket}, JQExpression: {jq_expression}"
            )

            # Check if required configuration fields are present
            if not s3_bucket or not jq_expression:
                print(f"Error: Missing S3 bucket or JQ expression for email: {email}")
                continue

            # Prepare payload for transformation Lambda
            transformation_payload = {
                "data": data,
                "JQExpression": jq_expression,
                "S3BucketARN": s3_bucket,
            }
            print("Transformation payload:", transformation_payload)

            # Invoke transformation Lambda
            lambda_response = lambda_client.invoke(
                FunctionName="transformationFunctionImage",
                InvocationType="RequestResponse",
                Payload=json.dumps(transformation_payload),
            )
            print(
                "Transformation Lambda response metadata:",
                lambda_response["ResponseMetadata"],
            )

            # Parse and log the result from the transformation Lambda
            transformation_result = json.loads(
                lambda_response["Payload"].read().decode("utf-8")
            )
            print(f"Transformation result for email {email}: {transformation_result}")

        except Exception as e:
            print(
                f"Error processing message (SQS message ID: {record.get('messageId', 'No ID')}): {str(e)}"
            )
            print("Exception details:", e, type(e))


def parse_s3_url(s3_url):
    """
    Helper function to parse an S3 URL into bucket name and key.
    :param s3_url: The S3 URL to parse (e.g., s3://bucket-name/object-key)
    :return: Tuple containing bucket name and key
    """
    if not s3_url.startswith("s3://"):
        raise ValueError(f"Invalid S3 URL: {s3_url}")
    parts = s3_url[5:].split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid S3 URL format: {s3_url}")
    return parts[0], parts[1]
