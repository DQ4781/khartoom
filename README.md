# **Khartoom**

## Overview
The AWS Lambda Transformation Service applies **JQ expressions** to JSON data. It processes data based on size and delivers the transformed output to a specified S3 bucket.

### Key Features
- Handles **small payloads (≤ 256 KB)** inline.
- Processes **large payloads (> 256 KB)** stored in S3.
- Decouples services using SQS for scalability and reliability.

---

## Architecture

1. **Customer**  
   Customers interact with the system through an **API Gateway** by sending POST requests:  
   - `/ingestion` → Sends JSON data.  
   - `/configuration` → Saves or updates configurations (like JQ expressions).  
   - `/apikey` → Generates/retrieves API keys.

2. **Preprocessor Service**  
   - Determines data size:  
     - If **data ≤ 256 KB** → Sends data directly to **SQS**.  
     - If **data > 256 KB** → Uploads the data to **Preprocessor S3** and sends the S3 URL to SQS.

3. **Ingestion Service**  
   - Pulls messages from SQS.  
   - Fetches user-specific configuration (e.g., JQ expressions) from **Configuration DynamoDB**.  
   - Sends the data and configuration to the **Transformation Service**.

4. **Transformation Service**  
   - Applies the JQ expression to the data:  
     - For inline JSON (small payloads) → Processes directly.  
     - For S3 URL (large payloads) → Downloads data from S3 and applies the JQ transformation.  
   - Outputs the transformed data.

5. **Delivery Service**  
   - Receives the transformed data from the Transformation Service.  
   - Uploads the result to the **Customer's S3 bucket**.

6. **API Key Services**  
   - **API Key Auth Service**: Validates API keys stored in **API Key DynamoDB**.  
   - **API Key Generator Service**: Generates API keys for new users upon sign-up via **Cognito**.

---

## Workflow Summary

The system processes JSON data with the following workflow:

1. **API Gateway**:  
   Customers send requests to the API Gateway to:  
   - Submit JSON data (`/ingestion`).  
   - Save or update JQ expressions (`/configuration`).  
   - Retrieve or generate API keys (`/apikey`).

2. **Preprocessor Service**:  
   - Determines the size of incoming JSON data:  
     - **Small Data (≤ 256 KB)**:  
       - Sends the payload directly to **SQS**.  
     - **Large Data (> 256 KB)**:  
       - Uploads the data to **Preprocessor S3**.  
       - Sends the **S3 URL** to SQS.

3. **Ingestion Service**:  
   - Pulls messages (either inline JSON or S3 URL) from SQS.  
   - Retrieves user-specific **JQ expressions** from the **Configuration DynamoDB**.  
   - Sends the data and configuration to the **Transformation Service**.

4. **Transformation Service**:  
   - Processes the data:  
     - Inline JSON: Processes directly with JQ.  
     - S3 URL: Fetches the JSON data from S3, applies the JQ expression.  
   - Sends the transformed data to the **Delivery Service**.

5. **Delivery Service**:  
   - Uploads the transformed data to the **Customer's S3 bucket**.

---

## Key Components

1. **API Gateway**  
   - Serves as the entry point for customers to interact with the system.  
   - Routes requests to respective Lambda services:
     - `/ingestion` → Preprocessor Service.  
     - `/configuration` → Configuration Service.  
     - `/apikey` → API Key Auth Service.

2. **Preprocessor Service**  
   - Evaluates the size of the incoming JSON payload.  
   - Handles:  
     - Direct SQS delivery for **small data** (≤ 256 KB).  
     - Uploads large data to **Preprocessor S3** and sends the S3 URL to SQS.

3. **Ingestion Service**  
   - Pulls messages from SQS.  
   - Retrieves JQ expressions from **Configuration DynamoDB**.  
   - Prepares data and invokes the **Transformation Service**.

4. **Transformation Service**  
   - Processes data using the specified JQ expression:  
     - Applies transformations inline for small payloads.  
     - Downloads and processes large payloads from S3.  
   - Outputs the transformed data to the Delivery Service.

5. **Delivery Service**  
   - Receives the transformed data.  
   - Uploads the results to the **Customer's S3 bucket**.

6. **Configuration Service**  
   - Manages customer-specific configurations, such as JQ expressions.  
   - Stores configurations in **Configuration DynamoDB**.

7. **API Key Services**  
   - **API Key Auth Service**: Validates API keys against **API Key DynamoDB**.  
   - **API Key Generator Service**: Generates API keys for customers after sign-up.

8. **Data Storage**  
   - **Preprocessor S3**: Temporary storage for large JSON payloads.  
   - **Customer S3**: Final storage for transformed data.  
   - **Configuration DynamoDB**: Stores customer configurations.  
   - **API Key DynamoDB**: Stores customer API keys.

9. **SQS (Amazon Simple Queue Service)**  
   - Decouples services to improve scalability and reliability.  
   - Queues messages for the Ingestion Service.

10. **Cognito**  
    - Handles customer authentication and triggers API key generation.

---
