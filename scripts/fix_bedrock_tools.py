#!/usr/bin/env python
"""
Bedrock Tool Validation Script

This script helps diagnose and fix issues with tools formatting for AWS Bedrock.
It can be used to test if tools are properly formatted for Claude models.
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

def format_bedrock_tool(tool):
    """Format a single tool for Bedrock."""
    # Ensure tool has a valid name
    if not tool.get("name"):
        tool_name = f"unknown_tool_{hash(json.dumps(tool, sort_keys=True)) % 1000}"
        print(f"⚠️ Found tool with empty name, assigning: {tool_name}")
    else:
        tool_name = tool.get("name")
    
    # Format in the structure Claude expects
    formatted_tool = {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool.get("description", ""),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": tool.get("parameters", {}).get("required", [])
            }
        }
    }
    
    # Add parameters to the schema
    parameters = tool.get("parameters", {}).get("properties", {})
    for param_name, param_details in parameters.items():
        formatted_tool["function"]["parameters"]["properties"][param_name] = {
            "type": param_details.get("type", "string"),
            "description": param_details.get("description", "")
        }
    
    return formatted_tool

def test_tool_with_bedrock(tool, model_id="anthropic.claude-3-haiku-20240307-v1:0", region="eu-central-1"):
    """Test if a tool can be properly used with Bedrock."""
    try:
        # Format the tool for Bedrock
        formatted_tool = format_bedrock_tool(tool)
        
        # Create Bedrock client
        bedrock = boto3.client('bedrock-runtime', region_name=region)
        
        # Create a simple request with the tool
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 50,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Can you help me calculate 2+2?"}]
                }
            ],
            "tools": [formatted_tool],
            "tool_choice": "auto"
        }
        
        print(f"Testing tool with Bedrock {model_id}...")
        print(f"Tool name: {formatted_tool['function']['name']}")
        
        # Attempt to invoke the model
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Process response to verify it worked
        response_body = json.loads(response['body'].read().decode('utf-8'))
        content = response_body.get('content', [])
        
        print("✅ Tool accepted by Bedrock!")
        return True, formatted_tool
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_msg = e.response.get('Error', {}).get('Message', '')
        
        if "ValidationException" in error_code:
            print(f"❌ Tool validation failed: {error_msg}")
            if "tools.0" in error_msg:
                print("  The tool format is invalid for Claude")
            elif "modelId" in error_msg:
                print(f"  Invalid model ID: {model_id}")
        else:
            print(f"❌ Bedrock error: {error_code} - {error_msg}")
        
        return False, formatted_tool
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False, formatted_tool

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_bedrock_tools.py <tool_json_file>")
        print("This script will validate if tools can be used with Bedrock/Claude")
        sys.exit(1)
        
    # Verify AWS credentials
    if not check_aws_credentials():
        print("Please run 'aws sso login' and try again")
        sys.exit(1)
    
    try:
        # Load tool definition from file
        tool_file = sys.argv[1]
        with open(tool_file, 'r') as f:
            tools = json.load(f)
        
        if isinstance(tools, dict):
            # Single tool
            tools = [tools]
        
        # Validate and fix each tool
        fixed_tools = []
        success_count = 0
        
        for i, tool in enumerate(tools):
            print(f"\nValidating tool {i+1}/{len(tools)}...")
            success, fixed_tool = test_tool_with_bedrock(tool)
            
            if success:
                success_count += 1
            
            fixed_tools.append(fixed_tool)
        
        # Save fixed tools to a new file
        output_file = tool_file.replace('.json', '_fixed.json')
        with open(output_file, 'w') as f:
            json.dump(fixed_tools, f, indent=2)
        
        print(f"\nResults: {success_count}/{len(tools)} tools validated successfully")
        print(f"Fixed tools saved to: {output_file}")
        
    except Exception as e:
        print(f"Error processing tools: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
