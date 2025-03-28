#!/usr/bin/env python
"""
Simple script to test AWS Bedrock model access.
"""

import os
import sys
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Base Claude models that are commonly available
CLAUDE_MODELS = [
    "anthropic.claude-3-sonnet-20240229-v1:0",  # Claude 3 Sonnet (standard version)
    "anthropic.claude-3-haiku-20240307-v1:0",   # Claude 3 Haiku (fastest version)
    "anthropic.claude-instant-v1",              # Claude Instant (older model)
    "eu.anthropic.claude-3-7-sonnet-20250219-v1:0"  # Claude 3.7 Sonnet (custom ARN)
]

def check_aws_credentials():
    """Verify AWS credentials are working."""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials valid: {identity['Arn']}")
        return True
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("Run 'aws sso login' to authenticate")
        return False
    except Exception as e:
        print(f"❌ AWS credentials error: {str(e)}")
        return False

def test_model(model_id, region="eu-central-1"):
    """Test if a specific model can be invoked."""
    try:
        bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 10,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Say hello"}]
                }
            ]
        }
        
        print(f"Testing model: {model_id}...")
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read().decode('utf-8'))
        content = response_body.get('content', [])
        text = "".join([block.get("text", "") for block in content if block.get("type") == "text"])
        
        print(f"✅ SUCCESS: Model {model_id}")
        print(f"  Response: {text.strip()}\n")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_msg = e.response.get('Error', {}).get('Message', '')
        
        print(f"❌ FAILED: Model {model_id} - {error_code}")
        print(f"  Error: {error_msg}\n")
        return False
    except Exception as e:
        print(f"❌ FAILED: Model {model_id}")
        print(f"  Error: {str(e)}\n")
        return False

def main():
    print("AWS Bedrock Model Tester")
    print("=======================")
    
    if not check_aws_credentials():
        print("\nPlease run 'aws sso login' and try again.")
        sys.exit(1)
    
    print("\nTrying to access different Claude models...")
    successes = []
    
    for model in CLAUDE_MODELS:
        if test_model(model):
            successes.append(model)
    
    if successes:
        print("\n✅ WORKING MODELS FOUND!")
        print("You can use these models with MCP-CLI:")
        for model in successes:
            model_name = model.split('.')[-2]  # Extract model name from ID
            print(f"  - {model} : Run with --model {model_name}")
        
        # Update server_config.json suggestion
        print("\nAdd these models to your server_config.json:")
        config_block = {"region": "eu-central-1", "models": {}}
        
        for model in successes:
            model_name = model.split('.')[-2]
            model_id = model
            arn = f"arn:aws:bedrock:eu-central-1::foundation-model/{model}"
            
            config_block["models"][model_name] = {
                "modelId": model_id,
                "arn": arn
            }
        
        print(json.dumps({"llmProviders": {"bedrock": config_block}}, indent=2))
    else:
        print("\n❌ NO WORKING MODELS FOUND")
        print("Please check:")
        print("1. You have enabled models in the AWS Bedrock console")
        print("2. Your IAM role has the correct permissions:")
        print("   - bedrock:InvokeModel")
        print("   - bedrock:ListFoundationModels (optional)")
        print("3. Your AWS SSO session is still active")

if __name__ == "__main__":
    main()
