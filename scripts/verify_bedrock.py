#!/usr/bin/env python
"""
AWS Bedrock Model Verification Tool

This script checks AWS Bedrock access and provides guidance on resolving common issues.
"""

import os
import sys
import argparse
import json

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    from rich import print
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("Required dependencies not found. Please install them with:")
    print("pip install boto3 rich")
    sys.exit(1)

def verify_aws_credentials():
    """Verify AWS credentials and show identity information."""
    console = Console()
    
    try:
        with console.status("[bold green]Verifying AWS credentials...[/bold green]", spinner="dots"):
            # Use STS to get caller identity
            sts_client = boto3.client('sts')
            identity = sts_client.get_caller_identity()
            
            # Print identity information
            print(Panel.fit(
                f"[bold green]✅ AWS credentials valid[/bold green]\n\n"
                f"Account: [cyan]{identity.get('Account')}[/cyan]\n"
                f"User ID: [cyan]{identity.get('UserId')}[/cyan]\n"
                f"ARN: [cyan]{identity.get('Arn')}[/cyan]\n",
                title="AWS Identity Information",
                border_style="green"
            ))
        return True
            
    except NoCredentialsError:
        print(Panel.fit(
            "[bold red]❌ No AWS credentials found[/bold red]\n\n"
            "AWS credentials are not configured.\n\n"
            "[yellow]Possible solutions:[/yellow]\n"
            "- Run [bold]aws sso login[/bold] to authenticate with AWS SSO\n"
            "- Check your AWS configuration with [bold]aws configure list[/bold]\n"
            "- Set up credentials with [bold]aws configure[/bold]",
            title="AWS Credentials Error",
            border_style="red"
        ))
        return False
    except Exception as e:
        print(Panel.fit(
            f"[bold red]❌ Error verifying AWS credentials:[/bold red] {str(e)}\n\n"
            "[yellow]Troubleshooting steps:[/yellow]\n"
            "- Run [bold]aws sso login[/bold] to authenticate with AWS SSO\n"
            "- Check if your credentials have expired\n"
            "- Verify your AWS configuration with [bold]aws configure list[/bold]",
            title="AWS Credentials Error",
            border_style="red"
        ))
        return False

def check_bedrock_access(model_id, region):
    """Check if you have access to a specific AWS Bedrock model."""
    console = Console()
    
    try:
        with console.status(f"[bold green]Checking access to {model_id}...[/bold green]", spinner="dots"):
            # Create a Bedrock client
            bedrock_client = boto3.client('bedrock', region_name=region)
            
            # List models and check if the specified model exists and is accessible
            response = bedrock_client.list_foundation_models()
            
            model_found = False
            model_accessible = False
            model_details = {}
            
            for model in response.get('modelSummaries', []):
                if model.get('modelId') == model_id:
                    model_found = True
                    if model.get('throughputCapability') == 'ON_DEMAND':
                        model_accessible = True
                    model_details = model
                    break
            
            if model_found:
                if model_accessible:
                    print(f"[bold green]✅ You have access to {model_id}[/bold green]")
                    return True
                else:
                    print(f"[bold yellow]⚠️ Model {model_id} found but not accessible[/bold yellow]")
                    print("[yellow]You need to request access to this model in the AWS Bedrock console:[/yellow]")
                    print(f"  - Go to AWS Bedrock > Model access")
                    print(f"  - Find '{model_details.get('providerName')} - {model_details.get('modelName')}'")
                    print(f"  - Click 'Request model access'")
                    return False
            else:
                print(f"[bold red]❌ Model {model_id} not found in region {region}[/bold red]")
                print("[yellow]Available models in this region:[/yellow]")
                
                # Print available models
                table = Table()
                table.add_column("Model ID", style="cyan")
                table.add_column("Provider", style="green")
                
                for model in response.get('modelSummaries', []):
                    table.add_row(model.get('modelId', 'N/A'), model.get('providerName', 'N/A'))
                
                console.print(table)
                return False
                
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        
        print(f"[bold red]❌ AWS Bedrock API Error: {error_code}[/bold red]")
        print(f"[red]{error_msg}[/red]")
        
        if error_code == "AccessDeniedException":
            print("\n[yellow]You don't have permission to call the Bedrock API:[/yellow]")
            print("  - Ensure your IAM role/user has bedrock:ListFoundationModels permission")
            print("  - Check if your AWS account has been onboarded to Bedrock")
        return False
    except Exception as e:
        print(f"[bold red]❌ Error checking AWS Bedrock access:[/bold red] {str(e)}")
        print("[yellow]Possible solutions:[/yellow]")
        print("  - Check your AWS credentials (run 'aws sso login')")
        print("  - Verify you have correct IAM permissions")
        print("  - Confirm the model and region are correct")
        return False

def test_model_invocation(model_id, region):
    """Test if you can invoke the model with a simple prompt."""
    console = Console()
    
    try:
        with console.status(f"[bold green]Testing model invocation for {model_id}...[/bold green]", spinner="dots"):
            # Create a Bedrock Runtime client
            bedrock_client = boto3.client('bedrock-runtime', region_name=region)
            
            # Prepare simple request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 50,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": "Hello, can you hear me?"}]
                    }
                ]
            }
            
            # Invoke the model
            response = bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            # Process the response
            response_body = json.loads(response['body'].read().decode('utf-8'))
            
            # Extract content
            content = response_body.get('content', [{"type": "text", "text": "No response"}])
            text_content = ""
            
            # Process different content blocks
            for block in content:
                if block.get("type") == "text":
                    text_content += block.get("text", "")
            
            print(Panel.fit(
                f"[bold green]✅ Successfully invoked model {model_id}[/bold green]\n\n"
                f"[cyan]Response from model:[/cyan]\n"
                f"{text_content}",
                title="Model Invocation Test",
                border_style="green"
            ))
            return True
            
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        
        print(Panel.fit(
            f"[bold red]❌ Failed to invoke model: {error_code}[/bold red]\n"
            f"[red]{error_msg}[/red]\n\n"
            "[yellow]Troubleshooting:[/yellow]\n"
            "1. Check that you've enabled access to the model in AWS Bedrock console\n"
            "2. Verify your IAM permissions include bedrock:InvokeModel\n"
            "3. Make sure your account has appropriate quota for this model\n"
            "4. Confirm the model ID is correct and available in your region",
            title="Model Invocation Error",
            border_style="red"
        ))
        return False
    except Exception as e:
        print(Panel.fit(
            f"[bold red]❌ Error during model invocation:[/bold red] {str(e)}\n\n"
            "[yellow]Possible issues:[/yellow]\n"
            "- AWS credentials may have expired\n"
            "- Network connectivity problems\n"
            "- Missing IAM permissions\n"
            "- Incorrect model ID or region",
            title="Model Invocation Error",
            border_style="red"
        ))
        return False

def check_iam_permissions():
    """Check if the current identity has the necessary IAM permissions."""
    console = Console()
    
    try:
        with console.status("[bold green]Checking IAM permissions...[/bold green]", spinner="dots"):
            # Create an IAM client
            iam_client = boto3.client('iam')
            sts_client = boto3.client('sts')
            
            # Get caller identity
            identity = sts_client.get_caller_identity()
            
            # Simulate bedrock:InvokeModel permission
            # This may not always work with assumed roles, but can help in some cases
            try:
                response = iam_client.simulate_principal_policy(
                    PolicySourceArn=identity.get('Arn'),
                    ActionNames=['bedrock:InvokeModel', 'bedrock:ListFoundationModels']
                )
                
                all_allowed = True
                table = Table(title="IAM Permission Check")
                table.add_column("Action", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Decision Reason", style="yellow")
                
                for result in response.get('EvaluationResults', []):
                    action = result.get('EvalActionName')
                    decision = result.get('EvalDecision')
                    reasons = ", ".join([r.get('EvalDecisionDetail', '') 
                                        for r in result.get('EvalDecisionDetails', [])])
                    
                    status = "✅" if decision == "allowed" else "❌"
                    if decision != "allowed":
                        all_allowed = False
                    
                    table.add_row(action, status, reasons or "N/A")
                
                console.print(table)
                
                if all_allowed:
                    print("[bold green]You have all required permissions![/bold green]")
                else:
                    print("[bold yellow]Some required permissions are missing.[/bold yellow]")
                    print("[yellow]Recommendation:[/yellow] Add the following IAM policy to your role/user:")
                    print("""
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
                    """)
                    
            except ClientError as e:
                if "SimulatePrincipalPolicy" in str(e):
                    print("[yellow]Unable to simulate policy permissions.[/yellow]")
                    print("[yellow]This usually happens with federated users or assumed roles.[/yellow]")
                    print("[yellow]Recommendation:[/yellow] Make sure your role has these permissions:")
                    print("  - bedrock:InvokeModel")
                    print("  - bedrock:ListFoundationModels")
                else:
                    raise e
                
    except Exception as e:
        print(f"[bold red]❌ Error checking IAM permissions:[/bold red] {str(e)}")
        print("[yellow]This is usually normal for users using AWS SSO or assumed roles.[/yellow]")
        print("[yellow]Recommendation:[/yellow] Ensure your role includes these permissions:")
        print("  - bedrock:InvokeModel")
        print("  - bedrock:ListFoundationModels")

def main():
    parser = argparse.ArgumentParser(description='AWS Bedrock Model Verification Tool')
    parser.add_argument('--model-id', default="eu.anthropic.claude-3-7-sonnet-20250219-v1:0", 
                        help='The model ID to check access for')
    parser.add_argument('--region', default="eu-central-1", help='AWS region')
    parser.add_argument('--test-invocation', action='store_true', 
                        help='Test model invocation with a simple prompt')
    parser.add_argument('--check-all', action='store_true',
                        help='Run all checks')
    
    args = parser.parse_args()
    
    print(Panel.fit(
        f"[bold cyan]AWS Bedrock Model Verification Tool[/bold cyan]\n\n"
        f"Model: [yellow]{args.model_id}[/yellow]\n"
        f"Region: [yellow]{args.region}[/yellow]",
        border_style="cyan"
    ))

    # Verify AWS credentials first
    creds_ok = verify_aws_credentials()
    if not creds_ok:
        print("\n[bold red]Cannot proceed without valid AWS credentials.[/bold red]")
        sys.exit(1)
    
    print("\n[bold]Checking IAM permissions...[/bold]")
    check_iam_permissions()
    
    print("\n[bold]Checking model access...[/bold]")
    model_ok = check_bedrock_access(args.model_id, args.region)
    
    if model_ok and (args.test_invocation or args.check_all):
        print("\n[bold]Testing model invocation...[/bold]")
        invocation_ok = test_model_invocation(args.model_id, args.region)
        
        if invocation_ok:
            print("\n[bold green]✅ All checks passed! You can use this model with MCP-CLI.[/bold green]")
            print("\nCommand to use:")
            print(f"[cyan]uv run mcp-cli chat --server sqlite --provider bedrock --model {args.model_id.split('.')[-2].split('-')[-1]}[/cyan]")
        else:
            print("\n[bold red]⚠️ Model access verified but invocation failed.[/bold red]")
            print("[yellow]Please check the error messages above for troubleshooting steps.[/yellow]")
    elif not model_ok:
        print("\n[bold red]❌ Cannot access this model. Please fix the issues above before proceeding.[/bold red]")
        print("[yellow]If you're having permission issues, make sure your IAM role includes:[/yellow]")
        print("  - bedrock:InvokeModel")
        print("  - bedrock:ListFoundationModels")
    else:
        print("\n[bold yellow]⚠️ Basic checks passed, but model invocation was not tested.[/bold yellow]")
        print("[yellow]Run with --test-invocation to verify you can actually use the model.[/yellow]")
        print("\nTry running:")
        print(f"[cyan]uv run mcp-cli chat --server sqlite --provider bedrock --model {args.model_id.split('.')[-2].split('-')[-1]}[/cyan]")

if __name__ == "__main__":
    main()
