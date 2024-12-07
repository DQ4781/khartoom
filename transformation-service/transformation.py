import json
import subprocess
import boto3
import shlex

lambda_client = boto3.client("lambda")
s3_client = boto3.client("s3")


def lambda_handler(event, context):
    try:
        print(f"Received event: {json.dumps(event, indent=4)}")

        # Check for SQS-style "Records" structure
        if "Records" in event:
            print("Processing SQS-triggered event")
            for record in event["Records"]:
                process_message(json.loads(record["body"]))
        else:
            # Handle single event for debugging or direct invocation
            print("Processing single event (non-SQS)")
            process_message(event)

    except Exception as e:
        print(f"Error during transformation: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error during transformation: {str(e)}"),
        }


def process_message(message_body):
    """Process an individual message from SQS or direct event."""
    try:
        print(f"Processing message: {message_body}")

        email = message_body.get("Email")
        api_key = message_body.get("APIKey")
        s3_url = message_body.get("S3Url")
        data = message_body.get("Data")

        if not email or not api_key:
            print("Missing required fields: Email or APIKey in the message.")
            return

        # Fetch data from S3 if S3 URL is provided
        if s3_url:
            print(f"Fetching data from S3 URL: {s3_url}")
            data = fetch_data_from_s3(s3_url)
            if not data:
                print(f"Failed to fetch data from S3 for URL: {s3_url}")
                return
        elif not data:
            print("Message is missing both raw Data and S3Url. Skipping.")
            return

        # Extract required fields for transformation
        jq_expression = message_body.get("JQExpression")
        s3_bucket_arn = message_body.get("S3BucketARN")

        if not jq_expression or not s3_bucket_arn:
            print("Error: Missing required JQExpression or S3BucketARN in the message.")
            return

        print(f"Using jq expression: {jq_expression}")

        # Escape the JSON data for safe execution in shell
        json_data = json.dumps(data)
        escaped_json_data = shlex.quote(json_data)

        # Execute the jq expression using subprocess
        try:
            jq_command = f"echo {escaped_json_data} | jq '{jq_expression}'"
            print(f"Executing jq command: {jq_command}")
            transformed_data = subprocess.check_output(
                jq_command, shell=True, stderr=subprocess.STDOUT
            ).decode("utf-8")
        except subprocess.CalledProcessError as e:
            error_message = e.output.decode("utf-8") if e.output else str(e)
            print(f"Error executing jq command: {error_message}")
            return

        # Log the transformed data
        print(f"Transformed data: {transformed_data}")

        # Ensure transformed data is JSON-serializable
        try:
            transformed_data_json = json.loads(transformed_data)
        except json.JSONDecodeError:
            print("Transformed data is not valid JSON.")
            return

        # Prepare payload for delivery lambda
        delivery_payload = {
            "TransformedData": transformed_data_json,
            "S3BucketARN": s3_bucket_arn,
        }

        # Invoke Delivery lambda
        try:
            lambda_response = lambda_client.invoke(
                FunctionName="deliveryFunction",
                InvocationType="RequestResponse",
                Payload=json.dumps(delivery_payload),
            )

            # Log response from Delivery Lambda
            delivery_result = json.loads(
                lambda_response["Payload"].read().decode("utf-8")
            )
            print(f"Delivery result: {delivery_result}")
        except Exception as e:
            print(f"Error invoking Delivery Lambda: {str(e)}")
    except Exception as e:
        print(f"Error processing message: {str(e)}")


def fetch_data_from_s3(s3_url):
    """Fetch data from S3 given its URL."""
    try:
        print(f"Fetching data from S3 URL: {s3_url}")
        bucket_name, key = parse_s3_url(s3_url)
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        data = response["Body"].read().decode("utf-8")
        print(f"Data successfully fetched from S3: {s3_url}")
        return json.loads(data)
    except Exception as e:
        print(f"Error fetching data from S3 URL: {s3_url}. Error: {str(e)}")
        return None


def parse_s3_url(s3_url):
    """Parse the S3 URL into bucket name and key."""
    if s3_url.startswith("s3://"):
        _, _, bucket_name, *key_parts = s3_url.split("/")
        key = "/".join(key_parts)
        return bucket_name, key
    raise ValueError(f"Invalid S3 URL: {s3_url}")
