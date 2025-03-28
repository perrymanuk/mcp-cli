# src/cli/commands/register_commands.py
import typer
from cli.commands import ping, chat, prompts, tools, resources, interactive
from cli.commands import bedrock_info

# Remove the import for conversation_history_command as it's not needed at this level
# from cli.chat.commands.conversation_history import conversation_history_command

def ping_command(
    config_file: str = "server_config.json",
    server: str = None,
    provider: str = "openai",
    model: str = None,
    disable_filesystem: bool = False,
):
    """Simple ping command."""
    from cli.main import process_options, run_command
    servers, user_specified = process_options(server, disable_filesystem, provider, model)
    run_command(ping.ping_run, config_file, servers, user_specified)
    return 0

def chat_command(
    config_file: str = "server_config.json",
    server: str = None,
    provider: str = "openai",
    model: str = None,
    disable_filesystem: bool = False,
    debug: bool = False,
):
    """Start a chat session."""
    from cli.main import process_options, run_command
    servers, user_specified = process_options(server, disable_filesystem, provider, model)
    run_command(chat.chat_run, config_file, servers, user_specified, debug=debug)
    return 0

def interactive_command(
    config_file: str = "server_config.json",
    server: str = None,
    provider: str = "openai",
    model: str = None,
    disable_filesystem: bool = False,
):
    """Enter interactive mode with a command prompt."""
    from cli.main import process_options, run_command
    servers, user_specified = process_options(server, disable_filesystem, provider, model)
    run_command(interactive.interactive_mode, config_file, servers, user_specified)
    return 0

def prompts_list_command(
    config_file: str = "server_config.json",
    server: str = None,
    provider: str = "openai",
    model: str = None,
    disable_filesystem: bool = False,
):
    """List available prompts."""
    from cli.main import process_options, run_command
    servers, user_specified = process_options(server, disable_filesystem, provider, model)
    run_command(prompts.prompts_list, config_file, servers, user_specified)
    return 0

def tools_list_command(
    config_file: str = "server_config.json",
    server: str = None,
    provider: str = "openai",
    model: str = None,
    disable_filesystem: bool = False,
):
    """List available tools."""
    from cli.main import process_options, run_command
    servers, user_specified = process_options(server, disable_filesystem, provider, model)
    run_command(tools.tools_list, config_file, servers, user_specified)
    return 0

def tools_call_command(
    config_file: str = "server_config.json",
    server: str = None,
    provider: str = "openai",
    model: str = None,
    disable_filesystem: bool = False,
):
    """Call a tool with JSON arguments."""
    from cli.main import process_options, run_command
    servers, user_specified = process_options(server, disable_filesystem, provider, model)
    run_command(tools.tools_call, config_file, servers, user_specified)
    return 0

def resources_list_command(
    config_file: str = "server_config.json",
    server: str = None,
    provider: str = "openai",
    model: str = None,
    disable_filesystem: bool = False,
):
    """List available resources."""
    from cli.main import process_options, run_command
    servers, user_specified = process_options(server, disable_filesystem, provider, model)
    run_command(resources.resources_list, config_file, servers, user_specified)
    return 0

def bedrock_list_models_command(
    config_file: str = "server_config.json",
    server: str = None,
    provider: str = "openai",
    model: str = None,
    disable_filesystem: bool = False,
    region: str = "eu-central-1",
):
    """List available AWS Bedrock models."""
    bedrock_info.list_models(region)
    return 0

def bedrock_check_access_command(
    config_file: str = "server_config.json",
    server: str = None,
    provider: str = "openai",
    model: str = None,
    disable_filesystem: bool = False,
    model_id: str = "eu.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region: str = "eu-central-1",
):
    """Check if you have access to a specific AWS Bedrock model."""
    bedrock_info.check_access(model_id, region)
    return 0

def bedrock_verify_credentials_command(
    config_file: str = "server_config.json",
    server: str = None,
    provider: str = "openai",
    model: str = None,
    disable_filesystem: bool = False,
):
    """Verify AWS credentials and show identity information."""
    bedrock_info.verify_credentials()
    return 0

def register_commands(app: typer.Typer, process_options, run_command):
    """Register all commands on the provided Typer app."""
    app.command("ping")(ping_command)
    app.command("chat")(chat_command)
    app.command("interactive")(interactive_command)
    
    # Create sub-typer apps for prompts, tools, and resources.
    prompts_app = typer.Typer(help="Prompts commands")
    tools_app = typer.Typer(help="Tools commands")
    resources_app = typer.Typer(help="Resources commands")
    bedrock_app = typer.Typer(help="AWS Bedrock commands")
    
    prompts_app.command("list")(prompts_list_command)
    tools_app.command("list")(tools_list_command)
    tools_app.command("call")(tools_call_command)
    resources_app.command("list")(resources_list_command)
    
    # Register Bedrock commands
    bedrock_app.command("list-models")(bedrock_list_models_command)
    bedrock_app.command("check-access")(bedrock_check_access_command)
    bedrock_app.command("verify-credentials")(bedrock_verify_credentials_command)
    
    app.add_typer(prompts_app, name="prompts")
    app.add_typer(tools_app, name="tools")
    app.add_typer(resources_app, name="resources")
    app.add_typer(bedrock_app, name="bedrock")

# Export chat_command so it can be imported in main.py.
__all__ = ["register_commands", "chat_command"]