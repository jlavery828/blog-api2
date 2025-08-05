import uuid
from django.core.management.base import BaseCommand
import boto3
from django.conf import settings


class Command(BaseCommand):
    help = 'Uploads a test file to the configured S3 (DigitalOcean Spaces) bucket.'

    def handle(self, *args, **kwargs):
        # Fetch S3 settings from Django settings.py
        access_key = settings.AWS_ACCESS_KEY_ID
        secret_key = settings.AWS_SECRET_ACCESS_KEY
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        endpoint_url = settings.AWS_S3_ENDPOINT_URL
        cdn_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', f"{bucket_name}.nyc3.cdn.digitaloceanspaces.com")

        # Initialize boto3 client
        s3 = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
        )

        # Create and upload a test file
        file_key = f"s3test/{uuid.uuid4()}.txt"
        body = b"This is a test file from Django management command!"

        try:
            s3.put_object(
                Bucket=bucket_name,
                Key=file_key,
                Body=body,
                ContentType="text/plain"
            )
            file_url = f"https://{cdn_domain}/{file_key}"
            self.stdout.write(self.style.SUCCESS("✅ Upload successful!"))
            self.stdout.write(f"📄 File URL: {file_url}")

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Upload failed: {str(e)}"))