"""
Script to upload knowledge base files to S3 for AWS Bedrock Knowledge Base.
Run this after setting up your S3 bucket and AWS credentials in .env
"""
import os
import boto3
from pathlib import Path
from django.conf import settings
import django

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


def upload_knowledge_base():
    """Upload knowledge base files from Database folder to S3"""
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        print("Error: AWS credentials not configured in .env")
        return
    
    if not settings.S3_POLICY_BUCKET:
        print("Error: S3_POLICY_BUCKET not configured in .env")
        return
    
    # Path to knowledge base files
    kb_dir = BASE_DIR.parent / 'Database' / 'academic_ecommerce_rag_pack_txt' / 'knowledge_base'
    
    if not kb_dir.exists():
        print(f"Error: Knowledge base directory not found at {kb_dir}")
        return
    
    # Initialize S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
    
    bucket_name = settings.S3_POLICY_BUCKET
    
    # Upload all .txt files recursively
    uploaded_count = 0
    for txt_file in kb_dir.rglob('*.txt'):
        # Get relative path from knowledge_base directory
        relative_path = txt_file.relative_to(kb_dir)
        s3_key = f"knowledge_base/{relative_path.as_posix()}"
        
        try:
            s3_client.upload_file(str(txt_file), bucket_name, s3_key)
            print(f"Uploaded: {s3_key}")
            uploaded_count += 1
        except Exception as e:
            print(f"Error uploading {txt_file}: {e}")
    
    print(f"\nUpload complete! {uploaded_count} files uploaded to s3://{bucket_name}/knowledge_base/")
    print("\nNext steps:")
    print("1. Go to AWS Bedrock Console → Knowledge bases")
    print("2. Create a new Knowledge Base")
    print("3. Set data source to your S3 bucket (s3://{}/knowledge_base/)".format(bucket_name))
    print("4. Sync the Knowledge Base")
    print("5. Copy the Knowledge Base ID to BEDROCK_KNOWLEDGE_BASE_ID in .env")


if __name__ == '__main__':
    upload_knowledge_base()
