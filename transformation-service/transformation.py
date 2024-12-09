import json
import subprocess
import boto3
import shlex

lambda_client = boto3.client("lambda")
s3_client = boto3.client("s3")


def lambda_handler(event, context):
    try:
        print(
            f"Received event: {json.dumps(event)[:1000]}..."
        )  # Truncate for readability

        # Process the incoming payload
        process_message(event)

        return {"statusCode": 200, "body": "Transformation completed successfully"}

    except Exception as e:
        print(f"Error during transformation: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error during transformation: {str(e)}"),
        }


def process_message(message_body):
    try:
        print(
            f"Processing message: {json.dumps(message_body)[:1000]}..."
        )  # Truncated log

        # Extract necessary fields
        email = message_body.get("Email")
        s3_url = message_body.get("S3Url")
        data = message_body.get("Data")
        jq_expression = message_body.get("JQExpression")
        s3_bucket_arn = message_body.get("S3BucketARN")

        # Validate fields
        if not email or not jq_expression or not s3_bucket_arn:
            print("Error: Missing required fields in the message.")
            return

        # Run jq on S3 data if S3 URL is provided
        if s3_url:
            print(f"Message includes S3 URL: {s3_url}. Running jq transformation.")
            transformed_data = run_jq(jq_expression, s3_url=s3_url)
        elif data:
            # Otherwise, handle inline data
            print("Message includes raw Data. Running jq transformation.")
            transformed_data = run_jq(jq_expression, data=data)
        else:
            print("Error: Message is missing both raw Data and S3Url.")
            return

        if not transformed_data:
            print("Failed to execute jq transformation.")
            return

        # Log the transformed data for verification
        print(
            f"Successfully transformed data: {json.dumps(transformed_data)[:1000]}..."
        )

        # Prepare payload for the delivery lambda
        delivery_payload = {
            "TransformedData": transformed_data,
            "S3BucketARN": s3_bucket_arn,
        }

        # Invoke the delivery lambda
        invoke_delivery_lambda(delivery_payload)

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


def run_jq(jq_expression, data=None, s3_url=None):
    try:
        if s3_url:
            # S3 URL functionality: download the file and process with jq
            print(f"Processing data from S3 URL: {s3_url}")
            bucket_name, key = parse_s3_url(s3_url)
            local_file_path = "/tmp/s3_data.json"

            # Download the S3 object to a local file
            s3_client.download_file(bucket_name, key, local_file_path)
            print(f"Data downloaded from S3 to: {local_file_path}")

            # Log the first part of the file for debugging
            with open(local_file_path, "r") as file:
                file_contents = file.read(1000)  # Log the first 1000 characters
                print(f"File contents (truncated): {file_contents}")
                if not file_contents.strip():
                    print("Error: S3 file is empty.")
                    return None

            # Execute jq directly on the file
            jq_command = (
                f"jq {shlex.quote(jq_expression)} {shlex.quote(local_file_path)}"
            )
            print(f"Executing jq command on file: {jq_command}")

        elif data:
            # Inline data functionality: process JSON directly
            print(f"Processing inline data with jq.")
            wrapped_data = {"users": data} if isinstance(data, list) else data
            json_data = json.dumps(wrapped_data)
            escaped_json_data = shlex.quote(json_data)

            # Execute jq with the JSON data piped directly
            jq_command = f"echo {escaped_json_data} | jq {shlex.quote(jq_expression)}"
            print(f"Executing jq command on data: {jq_command}")

        else:
            print("Error: No valid data or S3 URL provided for jq execution.")
            return None

        # Run the jq command
        transformed_data = (
            subprocess.check_output(jq_command, shell=True, stderr=subprocess.STDOUT)
            .decode("utf-8")
            .strip()
        )

        # Log the transformed data
        print(f"Transformed data: {transformed_data}")

        # Ensure the result is valid JSON
        return json.loads(transformed_data)

    except subprocess.CalledProcessError as e:
        error_message = e.output.decode("utf-8") if e.output else str(e)
        print(f"Error executing jq command: {error_message}")
        return None
    # except json.JSONDecodeError as e:
    #    print(f"Transformed data is not valid JSON: {e}")
    #    return None
    # except Exception as e:
    #    print(f"Unexpected error during jq transformation: {str(e)}")
    #    return None


def invoke_delivery_lambda(payload):
    """Invoke the delivery Lambda function."""
    try:
        lambda_client = boto3.client("lambda")
        lambda_response = lambda_client.invoke(
            FunctionName="deliveryFunction",
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )
        delivery_result = json.loads(lambda_response["Payload"].read().decode("utf-8"))
        print(f"Delivery result: {delivery_result}")
    except Exception as e:
        print(f"Error invoking Delivery Lambda: {str(e)}")
