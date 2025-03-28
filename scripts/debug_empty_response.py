#!/usr/bin/env python
"""
Debug script to trace the exact response from AWS Bedrock when it returns empty content.
"""

import json
import boto3
import sys
from botocore.exceptions import ClientError, NoCredentialsError

def print_verbose(response_body):
    """Print the entire response body in a readable format."""
    print("Raw Response Body:")
    print(json.dumps(response_body, indent=2))
    
    # Check specific fields that might contain useful info
    if 'content' in response_body:
        print("\nContent field:")
        print(json.dumps(response_body['content'], indent=2))
    
    if 'error' in response_body:
        print("\nError field:")
        print(json.dumps(response_body['error'], indent=2))
    
    if 'message' in response_body:
        print("\nMessage field:")
        print(response_body['message'])
    
    if 'stop_reason' in response_body:
        print("\nStop reason:")
        print(response_body['stop_reason'])

def test_bedrock_with_trace(model_id, region="eu-central-1"):
    """Test a Bedrock model with complete tracing of the API interaction."""
    print(f"Testing {model_id} in {region}...")
    
    try:
        # Create Bedrock Runtime client
        client = boto3.client('bedrock-runtime', region_name=region)
        
        # Create a simple request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": "Hello, please say hello back and identify yourself."}]
                }
            ]
        }
        
        print("\nRequest Body:")
        print(json.dumps(request_body, indent=2))
        
        # Invoke the model
        try:
            print("\nSending request to Bedrock...")
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            # Get raw response details including headers
            print("\nResponse Headers:")
            for key, value in response['ResponseMetadata'].items():
                print(f"  {key}: {value}")
            
            try:
                # Process the response body
                print("\nReading response body...")
                response_body_bytes = response['body'].read()
                print(f"Response body size: {len(response_body_bytes)} bytes")
                
                if len(response_body_bytes) == 0:
                    print("WARNING: Empty response body received!")
                    return False
                
                response_body = json.loads(response_body_bytes.decode('utf-8'))
                print("\nParsed response body successfully")
                
                # Print verbose response details
                print_verbose(response_body)
                
                # Extract content specifically
                content = response_body.get('content', [])
                if not content:
                    print("\nWARNING: Empty content array in response")
                    return False
                
                text = "".join([block.get("text", "") for block in content if block.get("type") == "text"])
                
                if text.strip():
                    print(f"\nExtracted text response: {text.strip()}")
                    print("SUCCESS: Got a valid text response")
                    return True
                else:
                    print("\nWARNING: No text content found in response")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse response as JSON: {e}")
                print(f"Raw response: {response_body_bytes}")
                return False
            
        except ClientError as e:
            print("\nAWS Client Error:")
            error_code = e.response.get('Error', {}).get('Code', '')
            error_msg = e.response.get('Error', {}).get('Message', '')
            print(f"  Code: {error_code}")
            print(f"  Message: {error_msg}")
            return False
            
    except Exception as e:
        print(f"ERROR: Unexpected exception: {str(e)}")
        return False

def check_all_models():
    """Check all commonly available Claude models to find one that works."""
    models_to_try = [
        # Foundation models
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "anthropic.claude-instant-v1",
        "anthropic.claude-v2:1",
        
        # Try both formats for Claude 3.7 Sonnet
        "anthropic.claude-3-7-sonnet-20250219-v1:0",
        "eu.anthropic.claude-3-7-sonnet-20250219-v1:0"
    ]
    
    regions = ["eu-central-1", "us-east-1", "us-west-2"]
    
    for region in regions:
        print(f"\n=== Testing region: {region} ===\n")
        
        for model_id in models_to_try:
            print(f"\n--- Testing model: {model_id} ---\n")
            if test_bedrock_with_trace(model_id, region):
                print(f"\n✅ SUCCESS with {model_id} in {region}")
                return True, model_id, region
            print(f"\n❌ FAILED with {model_id} in {region}")
            
    return False, None, None

def main():
    print("=== AWS Bedrock Empty Response Debugging ===")
    
    # Check all models
    success, model_id, region = check_all_models()
    
    if success:
        print("\n=== SUMMARY ===")
        print("Found working model:")
        print(f"  Region: {region}")
        print(f"  Model ID: {model_id}")
        print("\nUpdate your server_config.json to use this model.")
    else:
        print("\n=== SUMMARY ===")
        print("All models failed. Recommend checking:")
        print("1. AWS credentials (aws sts get-caller-identity)")
        print("2. IAM permissions for Bedrock")
        print("3. Model access in AWS Bedrock console")

if __name__ == "__main__":
    main()
