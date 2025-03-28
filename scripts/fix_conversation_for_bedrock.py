#!/usr/bin/env python
"""
Tool to fix conversation history issues that might cause empty responses from Claude.

This script creates a basic exchange with Claude that should work, and serves as a
template for resetting your conversation when needed.
"""

import json
import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def create_basic_conversation(model_id, region="eu-central-1"):
    """Create a basic conversation with Claude that should work."""
    try:
        # Create Bedrock Runtime client
        client = boto3.client('bedrock-runtime', region_name=region)
        
        # Create a simple request (minimal but should work)
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hello Claude, I'm testing if you're able to respond. Please say hello back."}]
                }
            ]
        }
        
        print("Sending request to Bedrock...")
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Process the response body
        response_body = json.loads(response['body'].read().decode('utf-8'))
        content = response_body.get('content', [])
        text = "".join([block.get("text", "") for block in content if block.get("type") == "text"])
        
        if text.strip():
            print(f"✅ SUCCESS! Claude responded: {text.strip()}")
            return True, request_body, response_body
        else:
            print("❌ Got empty response from Claude")
            return False, request_body, response_body
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None, None

def create_debug_system_prompt():
    """Create a system prompt for debugging Bedrock."""
    return """You are Claude, a helpful AI assistant. You're currently helping debug a connection issue 
between a Python application and the AWS Bedrock service. Please respond to all messages, even
simple ones like 'hello' or 'test'. Provide a response to anything the user sends.

If the user mentions AWS, Bedrock, or debugging, provide information about what might be causing
issues with AWS Bedrock Claude models."""

def create_fixed_config(model_id, region):
    """Create a fixed server_config.json for Bedrock."""
    model_name = model_id.split(".")[-2]
    
    config = {
        "mcpServers": {
            "sqlite": {
                "command": "uvx",
                "args": ["mcp-server-sqlite", "--db-path", "test.db"]
            }
        },
        "llmProviders": {
            "bedrock": {
                "region": region,
                "models": {
                    f"{model_name}": {
                        "modelId": model_id,
                        "arn": f"arn:aws:bedrock:{region}::foundation-model/{model_id}"
                    }
                }
            }
        }
    }
    
    return config

def fix_system_prompt():
    """Find and fix the system prompt in src/cli/chat/system_prompt.py if it exists."""
    try:
        file_path = 'src/cli/chat/system_prompt.py'
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Simple check if we need to fix it
        if "claude" in content.lower() and "bedrock" in content.lower():
            print("System prompt already contains Claude/Bedrock references")
            return True
        
        # Create a backup
        with open(f"{file_path}.bak", 'w') as f:
            f.write(content)
            print(f"Created backup: {file_path}.bak")
        
        # Find where to inject our debug instruction
        if "def generate_system_prompt" in content:
            # Insert debug instruction for Claude
            new_content = content.replace(
                "def generate_system_prompt(tools):",
                f"""def generate_system_prompt(tools):
    # Check if using Bedrock Claude and add specific instructions
    if os.environ.get("LLM_PROVIDER") == "bedrock" and "claude" in os.environ.get("LLM_MODEL", "").lower():
        debug_prompt = \"\"\"{create_debug_system_prompt()}\"\"\"
        normal_prompt = ""
"""
            )
            
            # Add the rest of the function
            new_content = new_content.replace(
                "    # generate the system prompt",
                """    # Decide which prompt to use
    prompt = debug_prompt if os.environ.get("LLM_PROVIDER") == "bedrock" else ""
    
    # generate the system prompt"""
            )
            
            # Add import os
            if "import os" not in content:
                new_content = "import os\n" + new_content
            
            # Write the updated file
            with open(file_path, 'w') as f:
                f.write(new_content)
                print(f"Updated system prompt in {file_path}")
            
            return True
        else:
            print(f"Could not find system prompt function in {file_path}")
            return False
        
    except Exception as e:
        print(f"Error updating system prompt: {str(e)}")
        return False

def main():
    print("=== Claude Conversation Fixer ===\n")
    
    # Choose a model to test with
    models_to_try = [
        "anthropic.claude-3-haiku-20240307-v1:0",  # Most likely to work
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-instant-v1"
    ]
    
    regions = ["eu-central-1", "us-east-1"]
    
    working_model = None
    working_region = None
    
    # Find a working model
    for region in regions:
        for model_id in models_to_try:
            print(f"\nTesting {model_id} in {region}...")
            success, request, response = create_basic_conversation(model_id, region)
            if success:
                working_model = model_id
                working_region = region
                break
        
        if working_model:
            break
    
    if not working_model:
        print("\n❌ Could not find a working Claude model")
        print("Please check your AWS credentials and Bedrock model access")
        sys.exit(1)
    
    print(f"\n✅ Found working model: {working_model} in {working_region}")
    
    # Fix the system prompt
    print("\n=== Updating System Prompt ===")
    fix_system_prompt()
    
    # Create a fixed server_config.json
    config = create_fixed_config(working_model, working_region)
    config_path = "fixed_server_config.json"
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
        print(f"\nCreated fixed server config at {config_path}")
    
    # Output instructions
    print("\n=== Instructions ===")
    print("1. Try running with the fixed config:")
    print(f"   uv run mcp-cli chat --server sqlite --provider bedrock --model {working_model.split('.')[-2]} --config-file {config_path}")
    print("\n2. If that doesn't work, try using the Claude test directly:")
    print(f"   python debug_empty_response.py")

if __name__ == "__main__":
    main()
