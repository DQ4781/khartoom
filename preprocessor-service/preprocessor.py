########
#  V2 Preprocessor TEST
#########
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
    print("Lambda invoked with event:", event)  # Log incoming event

    try:
        body = json.loads(event["body"])
        print("Parsed request body:", body)  # Log parsed body

        email = sanitize_email(body.get("Email"))
        api_key = body.get("APIKey")
        data = body.get("Data")

        if not email or not api_key or not data:
            print("Missing required fields: Email, APIKey, or Data")
            return {
                "statusCode": 400,
                "body": json.dumps("Missing required ingestion fields."),
            }

        print(
            f"Sanitized Email: {email}, APIKey: {api_key}, Data size: {len(json.dumps(data).encode('utf-8'))} bytes"
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Error parsing request body: {str(e)}")
        return {"statusCode": 400, "body": json.dumps(f"Invalid request: {str(e)}")}

    # Validate the API key
    print(f"Validating API key for email: {email}")
    if not validate_api_key(api_key, email):
        print(f"Invalid API key for email: {email}")
        return {"statusCode": 403, "body": json.dumps(f"Invalid API key.")}

    # Serialize request body to JSON string & check byte size
    request_json = json.dumps({"Email": email, "APIKey": api_key, "Data": data})
    request_size = len(request_json.encode("utf-8"))  # size in BYTES
    print(f"Request size: {request_size} bytes")

    # If less than 256KB, send entire request to SQS
    if request_size < 256 * 1024:
        print(f"Request size is less than 256KB. Sending to SQS.")
        if send_to_sqs(request_json):
            print("Data successfully sent to SQS.")
            return {"statusCode": 200, "body": json.dumps("Data sent to SQS.")}
        else:
            print("Error sending data to SQS.")
            return {"statusCode": 500, "body": json.dumps("Error sending data to SQS.")}

    # If not, store in S3 bucket & pass S3 URL to SQS
    else:
        print(f"Request size exceeds 256KB. Storing in S3.")
        s3_url = generate_s3_url(request_json, email)
        if s3_url:
            print(f"Data successfully stored in S3 at URL: {s3_url}")
            if send_to_sqs(
                json.dumps({"Email": email, "APIKey": api_key, "S3Url": s3_url})
            ):
                print("S3 URL successfully sent to SQS.")
                return {
                    "statusCode": 200,
                    "body": json.dumps("Data stored in S3 and URL sent to SQS."),
                }
            else:
                print("Error sending S3 URL to SQS.")
                return {
                    "statusCode": 500,
                    "body": json.dumps("Error sending S3 URL to SQS."),
                }
        else:
            print("Error storing data in S3.")
            return {"statusCode": 500, "body": json.dumps("Error storing data in S3.")}


def validate_api_key(api_key, email):
    try:
        print(f"Fetching API key for email: {email}")
        response = api_key_table.get_item(Key={"Email": email})
        print("DynamoDB response:", response)
        if "Item" in response and response["Item"].get("APIKey") == api_key:
            print("API key validation succeeded.")
            return True
        print("API key validation failed.")
        return False
    except Exception as e:
        print(f"Error validating API key for email: {email}: {e}")
        return False


def send_to_sqs(message_body):
    try:
        print(f"Sending message to SQS. Message body: {message_body}")
        response = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=message_body)
        print(f"Message successfully sent to SQS. Response: {response}")
        return True
    except sqs.exceptions.InvalidMessageContents as e:
        print(
            f"Invalid message contents when sending to SQS: {e}\nMessage found: {message_body}"
        )
        return False
    except Exception as e:
        print(f"Error sending message to SQS: {e}")
        return False


def generate_s3_url(body, email):
    try:
        key = f"ingestion_data/{email}/{uuid.uuid4()}.json"
        print(f"Storing data in S3. Bucket: {BUCKET}, Key: {key}")
        response = s3_bucket.put_object(Bucket=BUCKET, Key=key, Body=body)
        print("S3 put_object response:", response)
        s3_url = f"s3://{BUCKET}/{key}"
        print(f"S3 URL generated: {s3_url}")
        return s3_url
    except Exception as e:
        print(f"Error storing data for email: {email} in S3: {e}\nFor message: {body}")
        return None


def sanitize_email(email):
    if not email:
        print("No email provided for sanitization.")
        return None
    email = email.strip()
    try:
        local_part, domain_part = email.rsplit("@", 1)
        sanitized_email = f"{local_part}@{domain_part.lower()}"
        print(f"Sanitized email: {sanitized_email}")
        return sanitized_email
    except ValueError as e:
        print(f"Error sanitizing email: {email}. Error: {str(e)}")
        return None
