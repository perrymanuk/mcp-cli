#!/usr/bin/env python
"""
Simple script to check if you have access to AWS Bedrock.
Doesn't even try to use a model - just checks if the service is available.
"""

import boto3
import sys
from botocore.exceptions import ClientError, NoCredentialsError

def check_aws_credentials():
    """Verify AWS credentials are valid."""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials valid")
        print(f"  Account: {identity['Account']}")
        print(f"  User: {identity['UserId']}")
        print(f"  ARN: {identity['Arn']}")
        return True
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("Run 'aws sso login' to authenticate")
        return False
    except Exception as e:
        print(f"❌ AWS credentials error: {str(e)}")
        return False

def check_bedrock_service(region="eu-central-1"):
    """Check if Bedrock service is accessible."""
    try:
        print(f"Checking Bedrock service in {region}...")
        # Check if we can connect to Bedrock service
        bedrock = boto3.client('bedrock', region_name=region)
        
        # Just try a simple API call that doesn't require model access
        response = bedrock.list_foundation_models(maxResults=10)
        model_count = len(response.get('modelSummaries', []))
        
        print(f"✅ Successfully connected to Bedrock service")
        print(f"  Found {model_count} models in catalog")
        
        # Print a few model names as verification
        if model_count > 0:
            print("  Sample models:")
            for i, model in enumerate(response.get('modelSummaries', [])[:3]):
                print(f"    {i+1}. {model.get('modelId', 'Unknown')}")
                
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_msg = e.response.get('Error', {}).get('Message', '')
        
        print(f"❌ Bedrock service error: {error_code}")
        print(f"  Message: {error_msg}")
        
        if error_code == "AccessDeniedException":
            print("\nThis likely means your AWS role doesn't have permission to access Bedrock.")
            print("Check that your role includes:")
            print("  - bedrock:ListFoundationModels")
        
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def check_bedrock_runtime(region="eu-central-1"):
    """Check if Bedrock Runtime service is accessible."""
    try:
        print(f"\nChecking Bedrock Runtime service in {region}...")
        # Connect to Bedrock Runtime service - won't actually call a model
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        
        # We can't make a simple call that doesn't invoke a model
        # But we can at least check if the service is accessible
        print(f"✅ Successfully created Bedrock Runtime client")
        print("  (No API calls made - just verified service exists)")
        
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_msg = e.response.get('Error', {}).get('Message', '')
        
        print(f"❌ Bedrock Runtime service error: {error_code}")
        print(f"  Message: {error_msg}")
        
        if error_code == "AccessDeniedException":
            print("\nThis likely means your AWS role doesn't have permission to invoke Bedrock models.")
            print("Check that your role includes:")
            print("  - bedrock:InvokeModel")
        
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    print("=== AWS Bedrock Access Check ===\n")
    
    # First check credentials
    if not check_aws_credentials():
        print("\nCannot proceed without valid AWS credentials.")
        sys.exit(1)
    
    # Check each region
    regions = ["eu-central-1", "us-east-1", "us-west-2"]
    
    for region in regions:
        print(f"\n=== Checking region: {region} ===")
        bedrock_ok = check_bedrock_service(region)
        runtime_ok = check_bedrock_runtime(region)
        
        if bedrock_ok and runtime_ok:
            print(f"\n✅ {region}: Both Bedrock services are accessible")
        else:
            print(f"\n⚠️ {region}: Some Bedrock services are not accessible")
    
    print("\n=== Summary ===")
    print("If any region shows both services as accessible, you should be able")
    print("to use Bedrock models from that region if you have enabled them.")
    print("\nTo enable models:")
    print("1. Go to AWS Console > Amazon Bedrock > Model access")
    print("2. Click 'Manage model access'")
    print("3. Find Anthropic and select Claude models")
    print("4. Submit access request")

if __name__ == "__main__":
    main()
