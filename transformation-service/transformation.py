import json
import subprocess
import boto3
import shlex

lambda_client = boto3.client("lambda")


def lambda_handler(event, context):
    try:
        # Extract the incoming data and transformation expression from the event
        data = event["data"]
        jq_expression = event["JQExpression"]
        s3_arn = event["S3BucketARN"]

        # Log the incoming data
        print(f"Received data: {data}")
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
