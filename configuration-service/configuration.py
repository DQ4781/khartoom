import os
import json
import boto3

dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-west-2"))
table = dynamodb.Table("UserConfiguration")


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        user_id = body["UserID"]
        s3_bucket = body["S3BucketARN"]
        jq_expression = body["JQExpression"]

        table.put_item(
            Item={
                "UserID": user_id,
                "S3BucketARN": s3_bucket,
                "JQExpression": jq_expression,
            }
        )
        return {"statusCode": 200, "body": json.dumps("Configuration saved!")}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error saving configuration: {str(e)}"),
        }
