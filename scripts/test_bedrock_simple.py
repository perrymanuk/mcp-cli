#!/usr/bin/env python
"""
Simple script to test AWS Bedrock Claude model with a basic message exchange.
This helps verify that authentication and model access are working correctly.
"""

import json
import boto3
import sys
from botocore.exceptions import ClientError, NoCredentialsError

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

def test_claude_models():
    """Test various Claude models to find one that works."""
    models_to_try = [
        # Standard foundation models
        "anthropic.claude-3-sonnet-20240229-v1:0",  # Claude 3 Sonnet
        "anthropic.claude-3-haiku-20240307-v1:0",   # Claude 3 Haiku
        "anthropic.claude-instant-v1",              # Claude Instant
        
        # Custom ARN (adjust as needed)
        "eu.anthropic.claude-3-7-sonnet-20250219-v1:0"  # Claude 3.7 Sonnet
    ]
    
    regions = ["eu-central-1", "us-east-1", "us-west-2"]
    
    for region in regions:
        print(f"\nTrying region: {region}")
        
        for model_id in models_to_try:
            print(f"\nTesting model: {model_id}")
            
            try:
                # Create Bedrock Runtime client
                client = boto3.client('bedrock-runtime', region_name=region)
                
                # Create a simple request
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 50,
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"type": "text", "text": "Hello, please say hello back!"}]
                        }
                    ]
                }
                
                # Invoke the model
                response = client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(request_body)
                )
                
                # Process the response
                response_body = json.loads(response['body'].read().decode('utf-8'))
                content = response_body.get('content', [])
                text = "".join([block.get("text", "") for block in content if block.get("type") == "text"])
                
                print(f"✅ SUCCESS! Model responded: {text.strip()}")
                print(f"✅ This model works: {model_id} in region {region}")
                
                # Show config format
                print("\nAdd this to your server_config.json:")
                print(f"""
"llmProviders": {{
  "bedrock": {{
    "region": "{region}",
    "models": {{
      "{model_id.split('.')[-2]}": {{
        "modelId": "{model_id}",
        "arn": "arn:aws:bedrock:{region}::foundation-model/{model_id}"
      }}
    }}
  }}
}}
                """)
                
                print("\nTry running:")
                print(f"uv run mcp-cli chat --server sqlite --provider bedrock --model {model_id.split('.')[-2]}")
                
                # Return with successful model
                return True, model_id, region
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                error_msg = e.response.get('Error', {}).get('Message', '')
                
                print(f"❌ ERROR: {error_code} - {error_msg}")
                
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
    
    print("\n❌ None of the models worked in any region.")
    return False, None, None

def main():
    print("AWS Bedrock Claude Simple Test")
    print("==============================")
    
    if not check_aws_credentials():
        print("\nPlease run 'aws sso login' and try again.")
        sys.exit(1)
    
    success, model_id, region = test_claude_models()
    
    if success:
        print("\n🎉 Test successful! Found a working model.")
        print(f"Region: {region}")
        print(f"Model: {model_id}")
    else:
        print("\n❌ Test failed. Could not find a working Claude model.")
        print("Please check:")
        print("1. You have enabled models in the AWS Bedrock console")
        print("2. Your IAM role has bedrock:InvokeModel permission")
        print("3. Your AWS SSO session is active")

if __name__ == "__main__":
    main()
