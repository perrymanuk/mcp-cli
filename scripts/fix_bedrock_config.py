#!/usr/bin/env python
"""
AWS Bedrock Configuration Fixer

This script automatically tests AWS Bedrock model access and updates
the server_config.json with working models.
"""

import os
import json
import boto3
import sys
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

def update_config_file(working_models, config_path="server_config.json", region="eu-central-1"):
    """Update server_config.json with working models."""
    try:
        # Load existing config
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {"mcpServers": {}, "llmProviders": {}}
        
        # Ensure llmProviders and bedrock sections exist
        if "llmProviders" not in config:
            config["llmProviders"] = {}
        
        if "bedrock" not in config["llmProviders"]:
            config["llmProviders"]["bedrock"] = {"region": region, "models": {}}
        
        # Update models section
        for model in working_models:
            model_name = model.split('.')[-2]  # Extract model name from ID
            model_id = model
            
            # Handle special case for eu.anthropic models
            if model.startswith("eu."):
                arn = f"arn:aws:bedrock:{region}:890672996299:inference-profile/{model}"
            else:
                arn = f"arn:aws:bedrock:{region}::foundation-model/{model}"
            
            config["llmProviders"]["bedrock"]["models"][model_name] = {
                "modelId": model_id,
                "arn": arn
            }
        
        # Add shorter model names for convenience
        working_models_dict = {}
        for model in working_models:
            if "claude-3-sonnet" in model:
                working_models_dict["claude"] = {
                    "modelId": model,
                    "arn": f"arn:aws:bedrock:{region}::foundation-model/{model}" if not model.startswith("eu.") else f"arn:aws:bedrock:{region}:890672996299:inference-profile/{model}"
                }
            if "claude-3-haiku" in model:
                working_models_dict["claude-fast"] = {
                    "modelId": model,
                    "arn": f"arn:aws:bedrock:{region}::foundation-model/{model}"
                }
        
        # Add the shorter names
        config["llmProviders"]["bedrock"]["models"].update(working_models_dict)
        
        # Write updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"✅ Updated {config_path} with working models")
        print("You can now use these models with MCP-CLI:")
        for model in working_models:
            model_name = model.split('.')[-2]
            print(f"  - {model_name}: uv run mcp-cli chat --server sqlite --provider bedrock --model {model_name}")
        if "claude" in working_models_dict:
            print(f"  - claude: uv run mcp-cli chat --server sqlite --provider bedrock --model claude")
        if "claude-fast" in working_models_dict:
            print(f"  - claude-fast: uv run mcp-cli chat --server sqlite --provider bedrock --model claude-fast")
        
        return True
    except Exception as e:
        print(f"❌ Failed to update config: {str(e)}")
        return False

def main():
    print("AWS Bedrock Configuration Fixer")
    print("==============================")
    
    if not check_aws_credentials():
        print("\nPlease run 'aws sso login' and try again.")
        sys.exit(1)
    
    print("\nTesting models to find ones that work...")
    regions_to_try = ["eu-central-1", "us-east-1", "us-west-2"]
    working_models = []
    working_region = None
    
    # Try each region until we find models that work
    for region in regions_to_try:
        print(f"\nTrying region: {region}")
        region_working_models = []
        
        for model in CLAUDE_MODELS:
            if test_model(model, region):
                region_working_models.append(model)
        
        if region_working_models:
            working_models = region_working_models
            working_region = region
            print(f"✅ Found {len(working_models)} working models in {region}")
            break
    
    if working_models:
        update_config_file(working_models, region=working_region)
        print("\n🎉 Setup complete! You can now use AWS Bedrock with MCP-CLI.")
    else:
        print("\n❌ No working models found in any region.")
        print("Please check:")
        print("1. You have enabled models in the AWS Bedrock console")
        print("2. Your IAM role has the correct permissions:")
        print("   - bedrock:InvokeModel")
        print("3. Your AWS SSO session is still active")

if __name__ == "__main__":
    main()
