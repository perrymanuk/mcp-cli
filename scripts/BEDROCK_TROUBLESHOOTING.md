# AWS Bedrock Troubleshooting Guide

If you're experiencing issues accessing AWS Bedrock models with MCP-CLI, follow this troubleshooting guide.

## Quick Diagnostic Tool

A diagnostic script is included to help identify model access issues:

```bash
python debug_bedrock.py
```

This script will:
1. Verify your AWS credentials
2. Test multiple Claude models to find ones you can access
3. Provide configuration suggestions based on working models

## Common Issues & Solutions

### 1. AccessDeniedException

**Error Message:**
```
Error during conversation processing: Bedrock API Error: An error occurred (AccessDeniedException) when calling the InvokeModel operation: You don't have access to the model with the specified model ID.
```

**Solutions:**

a) **Enable the model in AWS Bedrock console:**
   - Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
   - Navigate to "Model access" in left sidebar
   - Find the Claude model you want to use
   - Click "Request model access" and follow the prompts
   - Wait for access to be granted (usually immediate)

b) **Check IAM permissions:**
   - Ensure your IAM role/user has the required permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel",
           "bedrock:ListFoundationModels"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

c) **Try a different model:**
   - Some Claude models are more widely available than others
   - Try one of these common models:
     - `anthropic.claude-3-haiku-20240307-v1:0` (fastest)
     - `anthropic.claude-3-sonnet-20240229-v1:0` (balanced)

d) **Check your AWS session:**
   - Your AWS SSO session may have expired
   - Run `aws sts get-caller-identity` to verify credentials
   - Run `aws sso login` to re-authenticate

### 2. Invalid or Outdated Model ID

**Solution:**
- Model IDs occasionally change with new releases
- Run the diagnostic script to find current available models:
  ```bash
  python debug_bedrock.py
  ```
- Update your server_config.json with the suggested models

### 3. Region Issues

**Solution:**
- Ensure the region in your config matches where you have model access
- Try switching to a different region (us-east-1, us-west-2, eu-central-1)
- Update the region in server_config.json:
  ```json
  "bedrock": {
    "region": "us-east-1",
    "models": {
      ...
    }
  }
  ```

### 4. Proper Configuration Format

Ensure your server_config.json contains the correct format for Bedrock:

```json
{
  "llmProviders": {
    "bedrock": {
      "region": "eu-central-1",
      "models": {
        "claude-3-sonnet": {
          "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
          "arn": "arn:aws:bedrock:eu-central-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
        },
        "claude-3-haiku": {
          "modelId": "anthropic.claude-3-haiku-20240307-v1:0",
          "arn": "arn:aws:bedrock:eu-central-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
        }
      }
    }
  }
}
```

## Using MCP-CLI with Bedrock

Once you've resolved access issues, use these commands:

```bash
# Using standard Claude 3 Sonnet
uv run mcp-cli chat --server sqlite --provider bedrock --model claude-3-sonnet

# Using Claude 3 Haiku (fastest)
uv run mcp-cli chat --server sqlite --provider bedrock --model claude-3-haiku

# With debug mode for more logging
uv run mcp-cli chat --server sqlite --provider bedrock --model claude-3-haiku --debug
```

## Still Having Issues?

If you continue to face problems:

1. Verify your AWS account has been onboarded to Amazon Bedrock
2. Check for AWS service quotas or limits in your account
3. Run `aws iam get-user` or `aws iam list-roles` to verify your identity
4. Try another AWS account if available
