import os
import boto3
import logging
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()


# Enable logging globally for boto3, botocore, s3transfer
logging.basicConfig(
    filename="boto_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

# Explicitly enable logging for boto3 and botocore
logging.getLogger("boto3").setLevel(logging.DEBUG)
logging.getLogger("botocore").setLevel(logging.DEBUG)
logging.getLogger("s3transfer").setLevel(logging.DEBUG)

# Optional: log to console too
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logging.getLogger().addHandler(console)

# Create an S3 client (DigitalOcean Spaces-compatible)
s3 = boto3.client(
    "s3",
    region_name="nyc3",
    endpoint_url="https://codetitan.nyc3.digitaloceanspaces.com",
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
)

# Make a simple API call to trigger logging
response = s3.list_buckets()
print(response)