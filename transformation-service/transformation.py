import json
import boto3
import jmespath


def lambda_handler(event, context):
    try:
        # Extract the incoming data and transformation expression from the event
        data = event["data"]
        jq_expression = event["JQExpression"]

        # Log the incoming data
        print(f"Received data: {data}")

        # Apply the transformation with given JQ expression
        transformed_data = jmespath.search(jq_expression, data)

        # Log the transformed data
        print(f"Transformed data: {transformed_data}")

        return {"statusCode": 200, "body": json.dumps("Transformation successful")}

    except Exception as e:
        print(f"Error during transformation: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error during transformation: {str(e)}"),
        }
