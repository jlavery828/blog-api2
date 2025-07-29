import boto3
import logging

# Enable logging
logging.basicConfig(filename='boto_test.log', level=logging.DEBUG)

s3 = boto3.client('s3', endpoint_url='https://nyc3.digitaloceanspaces.com')

response = s3.list_buckets()
print(response)