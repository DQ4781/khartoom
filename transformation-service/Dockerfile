# Use AWS Lambda base image for python3.8
FROM public.ecr.aws/lambda/python:3.8

# Install JQ
RUN yum -y install jq

# Copy lambda function code to container
COPY transformation.py ${LAMBDA_TASK_ROOT}

# Allow lambda to run transformation function
CMD ["transformation.lambda_handler"]