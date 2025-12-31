from app.config import settings
from typing import Optional

class S3Service:
    def __init__(self):
        self.enabled = settings.USE_S3
        if self.enabled:
            try:
                import boto3
                from botocore.exceptions import ClientError
                import uuid
                
                self.s3_client = boto3.client(
                    's3',
                    region_name=settings.AWS_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                self.bucket_name = settings.S3_BUCKET_NAME
                self.uuid = uuid
                self.ClientError = ClientError
            except ImportError:
                self.enabled = False

    async def upload_file(self, file_content: bytes, filename: str) -> Optional[str]:
        """Upload file to S3 in production, return local path in development"""
        if not self.enabled:
            # Local development - just return filename
            return filename
        
        try:
            # Production - upload to S3
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            s3_key = f"documents/{self.uuid.uuid4()}.{file_extension}" if file_extension else f"documents/{self.uuid.uuid4()}"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=self._get_content_type(filename)
            )
            
            return s3_key
        except Exception as e:
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
        """Generate presigned URL for production, return filename for development"""
        if not self.enabled:
            return f"/local/files/{s3_key}"
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=3600
            )
            return url
        except Exception:
            return ""

# Global instance
s3_service = S3Service()