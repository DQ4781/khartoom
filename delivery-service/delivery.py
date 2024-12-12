########
#  V2 Delivery TEST
#########
import boto3
import json
import uuid


s3_client = boto3.client("s3")


def lambda_handler(event, context):
    try:
        # Extract transformed data and S3 bucket name from the event
        transformed_data = event["TransformedData"]
        s3_bucket = event["S3BucketARN"]

        # Extract bucket name from ARN
        s3_name = s3_bucket.split(":::")[-1]

        # Log the details
        print(f"Storing transformed data in S3 bucket: {s3_bucket}")

        # Generate unique object key for each data upload
        object_key = f"transformed_data_{uuid.uuid4()}.json"

        # Upload transformed data to S3
        s3_client.put_object(
            Bucket=s3_name, Key=object_key, Body=json.dumps(transformed_data)
        )

        # Log success
        print(
            f"Data successfully stored in S3 bucket {s3_name} with object key {object_key}"
        )

        return {"statusCode": 200, "body": json.dumps("Data successfully stored in S3")}
    except Exception as e:
        print(f"Error storing data in S3: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error storing data in S3: {str(e)}"),
        }
