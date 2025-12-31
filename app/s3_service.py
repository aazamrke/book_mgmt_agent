import boto3
from botocore.exceptions import ClientError
from app.config import settings
import uuid
from typing import Optional

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    async def upload_file(self, file_content: bytes, filename: str) -> Optional[str]:
        """Upload file to S3 and return the S3 key"""
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            s3_key = f"documents/{uuid.uuid4()}.{file_extension}" if file_extension else f"documents/{uuid.uuid4()}"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=self._get_content_type(filename)
            )
            
            return s3_key
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return None

    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        extension = filename.split('.')[-1].lower() if '.' in filename else ''
        content_types = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }
        return content_types.get(extension, 'application/octet-stream')

    def get_file_url(self, s3_key: str) -> str:
        """Generate presigned URL for file access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=3600  # 1 hour
            )
            return url
        except ClientError:
            return ""

# Global instance
s3_service = S3Service()