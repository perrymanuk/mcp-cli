#!/usr/bin/env python
"""
Quick script to debug AWS Bedrock model access.
Run this directly to verify if you can access a specific model.
"""

import json
import boto3
import argparse
from botocore.exceptions import ClientError, NoCredentialsError

def check_credentials():
    """Verify AWS credentials are valid."""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"AWS Credentials Valid. User: {identity['Arn']}")
        return True
    except NoCredentialsError:
        print("ERROR: No AWS credentials found")
        print("Run 'aws sso login' to authenticate")
        return False
    except Exception as e:
        print(f"ERROR: AWS credentials check failed: {str(e)}")
        return False

def list_accessible_models(region):
    """List models that are accessible in the specified region."""
    try:
        bedrock = boto3.client('bedrock', region_name=region)
        models = bedrock.list_foundation_models()
        
        print(f"\nAccessible models in {region}:")
        print("-" * 50)
        
        accessible_models = []
        for model in models.get('modelSummaries', []):
            model_id = model.get('modelId')
            provider = model.get('providerName')
            model_name = model.get('modelName')
            accessible = model.get('throughputCapability') == 'ON_DEMAND'
            
            status = "ENABLED" if accessible else "DISABLED"
            print(f"{model_id} - {provider} - {status}")
            
            if accessible and 'anthropic' in model_id.lower() and 'claude' in model_id.lower():
                accessible_models.append(model_id)
        
        return accessible_models
    except ClientError as e:
        print(f"ERROR: Failed to list models: {str(e)}")
        return []
    except Exception as e:
        print(f"ERROR: Unexpected error listing models: {str(e)}")
        return []

def test_model_invocation(model_id, region):
    """Test invoking a model with a simple message."""
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 50,
            "messages": [
                {
                    "role": "user", 
                    "content": [{"type": "text", "text": "Hello, are you working?"}]
                }
            ]
        }
        
        print(f"\nTesting model invocation for {model_id}...")
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read().decode('utf-8'))
        content = response_body.get('content', [])
        text = "".join([block.get("text", "") for block in content if block.get("type") == "text"])
        
        print("SUCCESS: Model responded!")
        print(f"Response preview: {text[:100]}...")
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_msg = e.response.get('Error', {}).get('Message', '')
        
        print(f"ERROR: Model invocation failed - {error_code}")
        print(f"Error details: {error_msg}")
        
        if error_code == "AccessDeniedException":
            print("\nTROUBLESHOOTING:")
            print("1. Go to AWS Console > Bedrock > Model access")
            print("2. Find the Claude model and click 'Request model access'")
            print("3. Check that your IAM role has bedrock:InvokeModel permission")
        
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error invoking model: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Debug AWS Bedrock Model Access")
    parser.add_argument("--model-id", default="eu.anthropic.claude-3-7-sonnet-20250219-v1:0", 
                      help="Model ID to test")
    parser.add_argument("--region", default="eu-central-1",
                      help="AWS region")
    args = parser.parse_args()
    
    print("AWS Bedrock Model Access Checker")
    print("================================")
    
    # Check credentials
    if not check_credentials():
        return
    
    # List accessible models
    accessible_models = list_accessible_models(args.region)
    
    # Check if target model is accessible
    if args.model_id in accessible_models:
        print(f"\nGOOD NEWS: Model {args.model_id} is accessible!")
    else:
        print(f"\nWARNING: Model {args.model_id} is not in your accessible models list!")
    
    # Test model invocation regardless
    test_model_invocation(args.model_id, args.region)
    
    print("\nCONFIGURATION HELP:")
    print("Make sure your server_config.json includes:")
    print("""
{
  "llmProviders": {
    "bedrock": {
      "region": "eu-central-1",
      "models": {
        "claude-3-7-sonnet": {
          "modelId": "eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
          "arn": "arn:aws:bedrock:eu-central-1:890672996299:inference-profile/eu.anthropic.claude-3-7-sonnet-20250219-v1:0"
        }
      }
    }
  }
}
    """)

    print("\nTo run MCP-CLI with Bedrock, you need these commands:")
    print(f"uv run mcp-cli chat --server sqlite --provider bedrock --model claude-3-7-sonnet --debug")
    
if __name__ == "__main__":
    main()
