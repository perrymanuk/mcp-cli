# src/cli/commands/bedrock_info.py
"""Command to check AWS Bedrock access and available models."""

import typer
import boto3
import json
from rich import print
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
import logging
from typing import Optional

app = typer.Typer(help="Bedrock information commands")

@app.command("list-models")
def list_models(region: str = "eu-central-1"):
    """List available AWS Bedrock models in a region."""
    console = Console()
    
    try:
        with console.status("[bold green]Checking AWS Bedrock models...[/bold green]", spinner="dots"):
            # Create a Bedrock client to list foundation models
            bedrock_client = boto3.client('bedrock', region_name=region)
            models = bedrock_client.list_foundation_models()
            
            # Create a table for displaying models
            table = Table(title=f"AWS Bedrock Models in {region}")
            table.add_column("Model ID", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Model Name", style="yellow")
            table.add_column("Access", style="blue")
            
            for model in models.get('modelSummaries', []):
                model_id = model.get('modelId', 'N/A')
                provider = model.get('providerName', 'N/A') 
                model_name = model.get('modelName', 'N/A')
                access = "✅" if model.get('throughputCapability') == 'ON_DEMAND' else "❌"
                
                table.add_row(model_id, provider, model_name, access)
            
            console.print(table)
            
    except Exception as e:
        print(f"[bold red]Error accessing AWS Bedrock:[/bold red] {str(e)}")
        print("[yellow]Common issues:[/yellow]")
        print("  - AWS credentials not configured or expired")
        print("  - Missing IAM permissions to list Bedrock models")
        print("  - AWS region not correctly specified")
        print("\n[yellow]Troubleshooting:[/yellow]")
        print("  - Run 'aws configure' to set up credentials")
        print("  - Run 'aws sts get-caller-identity' to verify your identity")
        print("  - Make sure you have the needed IAM permissions")

@app.command("check-access")
def check_access(
    model_id: str = "eu.anthropic.claude-3-7-sonnet-20250219-v1:0", 
    region: str = "eu-central-1"
):
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
                else:
                    print(f"[bold yellow]⚠️ Model {model_id} found but not accessible[/bold yellow]")
                    print("[yellow]You need to request access to this model in the AWS Bedrock console:[/yellow]")
                    print(f"  - Go to AWS Bedrock > Model access")
                    print(f"  - Find '{model_details.get('providerName')} - {model_details.get('modelName')}'")
                    print(f"  - Click 'Request model access'")
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
                
    except Exception as e:
        print(f"[bold red]Error checking AWS Bedrock access:[/bold red] {str(e)}")
        print("[yellow]Possible solutions:[/yellow]")
        print("  - Check your AWS credentials (run 'aws sso login')")
        print("  - Verify you have correct IAM permissions")
        print("  - Confirm the model and region are correct")

@app.command("verify-credentials")
def verify_credentials():
    """Verify AWS credentials and show information about the current identity."""
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
            
    except Exception as e:
        print(f"[bold red]Error verifying AWS credentials:[/bold red] {str(e)}")
        print("[yellow]Troubleshooting steps:[/yellow]")
        print("  - Run 'aws sso login' to authenticate with AWS SSO")
        print("  - Check if your credentials have expired")
        print("  - Verify your AWS configuration with 'aws configure list'")
