import json
import subprocess
import boto3

lambda_client = boto3.client("lambda")


def lambda_handler(event, context):
    try:
        # Extract the incoming data and transformation expression from the event
        data = event["data"]
        jq_expression = event["JQExpression"]
        s3_arn = event["S3BucketARN"]

        # Log the incoming data
        print(f"Received data: {data}")

        # Execute the jq expression using subprocess
        try:
            jq_command = f"echo '{json.dumps(data)}' | jq '{jq_expression}'"
            transformed_data = subprocess.check_output(jq_command, shell=True).decode(
                "utf-8"
            )
        except subprocess.CalledProcessError as e:
            return {
                "statusCode": 500,
                "body": json.dumps(f"Error executing jq: {str(e)}"),
            }

        # Log the transformed data
        print(f"Transformed data: {transformed_data}")

        # Prepare payload for delivery lambda
        delivery_payload = {"TransformedData": transformed_data, "S3BucketARN": s3_arn}

        # Invoke Delivery lambda
        lambda_response = lambda_client.invoke(
            FunctionName="deliveryFunction",
            InvocationType="RequestResponse",
            Payload=json.dumps(delivery_payload),
        )

        # Log response from Delivery Lambda
        delivery_result = json.loads(lambda_response["Payload"].read().decode("utf-8"))
        print(f"Delivery result: {delivery_result}")

        return {"statusCode": 200, "body": transformed_data}

    except Exception as e:
        print(f"Error during transformation: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error during transformation: {str(e)}"),
        }
