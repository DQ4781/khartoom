import json
import subprocess
import boto3
import shlex

lambda_client = boto3.client("lambda")
s3_client = boto3.client("s3")


def lambda_handler(event, context):
    try:
        # Log SNS event/message
        print(f"Receieved event: {event}")

        if "S3Url" in event:
            print(f"S3 URL detected in message: {event['S3Url']}")
            data = fetch_data_from_s3(event["S3Url"])
        else:
            print("No S3 URL detected. Using raw data from event")
            data = event["data"]

        jq_expression = event["JQExpression"]
        s3_arn = event["S3BucketARN"]

        if not jq_expression or s3_arn:
            raise ValueError("Missing required JQExpression or S3BucketARN")

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
            return {
                "statusCode": 500,
                "body": json.dumps(f"Error executing jq: {error_message}"),
            }

        # Log the transformed data
        print(f"Transformed data: {transformed_data}")

        # Ensure transformed data is JSON-serializable
        try:
            transformed_data_json = json.loads(transformed_data)
        except json.JSONDecodeError:
            print("Transformed data is not valid JSON")
            return {
                "statusCode": 500,
                "body": json.dumps("Transformed data is not valid JSON."),
            }

        # Prepare payload for delivery lambda
        delivery_payload = {"TransformedData": transformed_data, "S3BucketARN": s3_arn}

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
            return {
                "statusCode": 500,
                "body": json.dumps(f"Error invoking delivery lambda: {str(e)}"),
            }

        return {"statusCode": 200, "body": transformed_data_json}

    except Exception as e:
        print(f"Error during transformation: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error during transformation: {str(e)}"),
        }


def fetch_data_from_s3(s3_url):
    try:
        print(f"Fetching data from S3 URL: {s3_url}")

        bucket_name, key = parse_s3_url(s3_url)
        print(f"Bucket: {bucket_name}, Key: {key}")

        # Download file from S3
        local_file_path = "/tmp/s3_data.json"
        s3_client.download_file(bucket_name, key, local_file_path)
        print(f"File downloaded to {local_file_path}")

        # Load JSON from file
        with open(local_file_path, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error fetching data from S3: {str(e)}")
        raise


def parse_s3_url(s3_url):
    """Parse the S3 URL into bucket name and object key."""
    if not s3_url.startswith("s3://"):
        raise ValueError("Invalid S3 URL format")
    _, _, bucket_name, *key_parts = s3_url.split("/")
    key = "/".join(key_parts)
    return bucket_name, key
