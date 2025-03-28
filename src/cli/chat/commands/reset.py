# src/cli/chat/commands/reset.py
"""Command to reset the conversation history."""

from rich import print
from rich.panel import Panel
from rich.console import Console

# Import the registration function from your commands package
from cli.chat.commands import register_command

async def reset_command(args, context):
    """
    Reset the conversation history, keeping only the system prompt.
    
    Usage:
      /reset         - Reset the conversation history, keeping only the system prompt.
      /reset --all   - Reset the conversation history completely, including the system prompt.
    """
    console = Console()
    
    try:
        # Check for --all flag
        all_flag = "--all" in args
        
        # Get the conversation history
        conversation_history = context.get("conversation_history", [])
        
        if not conversation_history:
            console.print("[italic yellow]No conversation history to reset.[/italic yellow]")
            return True
        
        # Reset the conversation history
        if all_flag:
            # Reset completely - including system prompt
            context["conversation_history"] = []
            console.print(Panel(
                "[bold green]✓ Conversation history completely reset[/bold green]",
                border_style="green"
            ))
        else:
            # Keep the system prompt if present
            if conversation_history and conversation_history[0].get("role") == "system":
                system_prompt = conversation_history[0]
                context["conversation_history"] = [system_prompt]
                console.print(Panel(
                    "[bold green]✓ Conversation history reset, keeping only system prompt[/bold green]",
                    border_style="green"
                ))
            else:
                # No system prompt found, reset completely
                context["conversation_history"] = []
                console.print(Panel(
                    "[bold yellow]⚠ No system prompt found. Conversation history completely reset.[/bold yellow]",
                    border_style="yellow"
                ))
        
    except Exception as e:
        console.print(f"[bold red]ERROR: Failed to reset conversation history: {str(e)}[/bold red]")
    
    return True

# Register the reset command
register_command("/reset", reset_command, ["--all"])
register_command("/clear-history", reset_command, ["--all"])  # Alias