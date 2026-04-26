"""
app/services/s3_service.py
──────────────────────────
S3 file upload and management service.

Handles:
- Uploading documents to S3 with KYC folder structure
- Generating secure S3 URLs for document access
- Document expiry and cleanup
"""

import os
from io import BytesIO
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException


class S3Service:
    """S3 file upload and retrieval service."""

    def __init__(self):
        self.bucket_name = os.getenv("AWS_S3_BUCKET_NAME", "voyza-documents")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.endpoint_url = os.getenv("AWS_S3_ENDPOINT")  # For MinIO or S3-compatible services

        # Build boto3 client with optional endpoint_url for MinIO
        client_kwargs = {
            "region_name": self.aws_region,
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        }

        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        self.s3_client = boto3.client("s3", **client_kwargs)

    async def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        user_id: str,
        document_type: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload a file to S3 and return the URL.

        Args:
            file_content: Raw file bytes
            file_name: Original filename
            user_id: User uploading the document
            document_type: Type of document (e.g., "driving_license")
            content_type: MIME type of the file

        Returns:
            S3 URL of the uploaded file

        Raises:
            HTTPException: If upload fails
        """
        try:
            # Build S3 key with organized folder structure
            # s3://bucket/kyc/user_id/document_type/filename
            s3_key = f"kyc/{user_id}/{document_type}/{file_name}"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    "user-id": user_id,
                    "document-type": document_type,
                },
            )

            # Return S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            return s3_url

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            raise HTTPException(
                500,
                f"Failed to upload document to S3: {error_code}",
            )
        except Exception as e:
            raise HTTPException(500, f"Unexpected error uploading file: {str(e)}")

    async def get_signed_url(
        self,
        s3_url: str,
        expiration: int = 3600,
    ) -> str:
        """
        Generate a signed URL for secure document access.

        Args:
            s3_url: Full S3 URL of the document
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Signed URL that can be used to access the document

        Raises:
            HTTPException: If URL generation fails
        """
        try:
            # Extract S3 key from URL
            # URL format: https://bucket.s3.region.amazonaws.com/key
            bucket = self.bucket_name
            if bucket in s3_url:
                s3_key = s3_url.split(f"{bucket}.s3.{self.aws_region}.amazonaws.com/")[1]
            else:
                raise ValueError("Invalid S3 URL format")

            # Generate signed URL
            signed_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": s3_key},
                ExpiresIn=expiration,
            )

            return signed_url

        except Exception as e:
            raise HTTPException(
                500,
                f"Failed to generate signed URL: {str(e)}",
            )

    async def delete_file(self, s3_url: str) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_url: Full S3 URL of the document to delete

        Returns:
            True if deletion was successful

        Raises:
            HTTPException: If deletion fails
        """
        try:
            # Extract S3 key from URL
            bucket = self.bucket_name
            if bucket in s3_url:
                s3_key = s3_url.split(f"{bucket}.s3.{self.aws_region}.amazonaws.com/")[1]
            else:
                raise ValueError("Invalid S3 URL format")

            self.s3_client.delete_object(Bucket=bucket, Key=s3_key)
            return True

        except Exception as e:
            raise HTTPException(500, f"Failed to delete file: {str(e)}")


# Singleton instance
_s3_service: Optional[S3Service] = None


def get_s3_service() -> S3Service:
    """Get or create S3 service instance."""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
