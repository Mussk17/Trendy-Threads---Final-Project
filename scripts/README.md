# Scripts

## upload_knowledge_base_to_s3.py

Uploads knowledge base files from the Database folder to S3 for AWS Bedrock Knowledge Base.

**Prerequisites:**
- AWS credentials configured in `.env` (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`)
- `S3_POLICY_BUCKET` set in `.env`
- S3 bucket created

**Usage:**
```bash
python scripts/upload_knowledge_base_to_s3.py
```

The script will upload all `.txt` files from `Database/academic_ecommerce_rag_pack_txt/knowledge_base/` to your S3 bucket under the `knowledge_base/` prefix.

**After uploading:**
1. Go to AWS Bedrock Console → Knowledge bases
2. Create a new Knowledge Base
3. Set data source to your S3 bucket
4. Sync the Knowledge Base
5. Copy the Knowledge Base ID to `BEDROCK_KNOWLEDGE_BASE_ID` in `.env`
