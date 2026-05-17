import boto3
import json
import urllib.parse
from requests_aws4auth import AWS4Auth
import requests

# -------------------
# CONFIG
# -------------------
region = "us-east-2"
service = "es"

host = "https://vpc-opensearch-5evuya563j3xznwj5dqkoxcjre.us-east-2.es.amazonaws.com"
index = "mygoogle"
doc_type = "_doc"

headers = {"Content-Type": "application/json"}

s3 = boto3.client("s3")


# -------------------
# AWS AUTH
# -------------------
credentials = boto3.Session().get_credentials()

awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token
)


# -------------------
# HELPERS
# -------------------
def bytes_to_text(data):
    return data.decode("utf-8", errors="ignore")


# -------------------
# MAIN LAMBDA
# -------------------
def lambda_handler(event, context):

    print("EVENT:", json.dumps(event))
    print("HOST:", host)

    for record in event["Records"]:

        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        print("Bucket:", bucket)
        print("Key:", key)

        # -------------------
        # GET S3 OBJECT
        # -------------------
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj["Body"].read().decode("utf-8", errors="ignore")

        lines = body.splitlines()

        if len(lines) < 1:
            print("Empty file, skipping")
            return

        title = lines[0] if len(lines) > 0 else ""
        author = lines[1] if len(lines) > 1 else ""
        date = lines[2] if len(lines) > 2 else ""

        content = "\n".join(lines[3:])

        # -------------------
        # BUILD DOCUMENT
        # -------------------
        document = {
            "filename": key,
            "title": title,
            "author": author,
            "date": date,
            "content": content
        }

        # -------------------
        # SAFE DOCUMENT ID
        # -------------------
        doc_id = urllib.parse.quote_plus(key)

        url = f"{host}/{index}/{doc_type}/{doc_id}"

        # -------------------
        # INDEX INTO OPENSEARCH
        # -------------------
        response = requests.post(
            url,
            auth=awsauth,
            json=document,
            headers=headers
        )

        print("OpenSearch response:", response.status_code, response.text)