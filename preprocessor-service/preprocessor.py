import json
import boto3
import uuid
import os
from dotenv import load_dotenv

s3_bucket = boto3.client("s3")
sqs = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
api_key_table = dynamodb.Table("UserAPIKeyTable")

load_dotenv()

QUEUE_URL = os.getenv("QUEUE_URL")
BUCKET = os.getenv("BUCKET")


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        email = body.get("Email")
        api_key = body.get("APIKey")
        data = body.get("Data")

        if not email or not api_key or not data:
            return {
                "statusCode": 400,
                "body": json.dumps("Missing required ingestion fields."),
            }
    except (json.JSONDecodeError, KeyError) as e:
        return {"statusCode": 400, "body": json.dumps(f"Invalid request: {str(e)}")}

    # Validate the API key
    if not validate_api_key(api_key, email):
        return {"statusCode": 403, "body": json.dumps(f"Invalid API key.")}

    # Serialize request body to JSON string & check byte size
    request_json = json.dumps(body)
    request_size = len(request_json.encode("utf-8"))  # size in BYTES

    # If less than 256KB, send entire request to SQS
    if request_size < 256 * 1024:
        send_to_sqs(request_json)
        return {"statusCode": 200, "body": json.dumps("Data sent to SQS.")}

    # If not, store in S3 bucket & pass S3 URL to SQS
    else:
        s3_url = generate_s3_url(request_json, email)
        if s3_url:
            if send_to_sqs(
                json.dumps({"Email": email, "APIKey": api_key, "S3Url": s3_url})
            ):
                return {
                    "statusCode": 200,
                    "body": json.dumps("Data stored in S3 and URL sent to SQS."),
                }
            else:
                return {
                    "statusCode": 500,
                    "body": json.dumps("Error sending S3 URL to SQS."),
                }
        else:
            return {"statusCode": 500, "body": json.dumps("Error storing data in S3")}


def validate_api_key(api_key, email):
    try:
        response = api_key_table.get_item(Key={"Email": email})
        if "Item" in response and response["Item"].get("APIKey") == api_key:
            return True
        return False
    except Exception as e:
        print(f"Error validating API key for email: {email}: {e}")
        return False


def send_to_sqs(message_body):
    try:
        response = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=message_body)
        print(f"Message successfuly sent. Response: {response}")
        return True
    except sqs.exceptions.InvalidMessageContents as e:
        print(
            f"Invalid message contents when sending to SQS: {e}\nMessage found: {response}"
        )
        return False
    except Exception as e:
        print(f"Error sending message to SQS: {e}")
        return False


def generate_s3_url(body, email):
    try:
        key = f"ingestion_data/{email}/{uuid.uuid4()}.json"
        response = s3_bucket.put_object(Bucket=BUCKET, Key=key, Body=body)
        return f"s3://{BUCKET}/{key}"
    except Exception as e:
        print(f"Error storing data for email: {email} in S3: {e}\nFor message: {body}")
        return None
