# Model Context Provider CLI
This repository contains a protocol-level CLI designed to interact with a Model Context Provider server. The client allows users to send commands, query data, and interact with various resources provided by the server.

## Features
- Protocol-level communication with the Model Context Provider.
- Dynamic tool and resource exploration.
- Support for multiple providers and models:
  - Providers: OpenAI, Ollama, AWS Bedrock.
  - Default models: `gpt-4o-mini` for OpenAI, `qwen2.5-coder` for Ollama, `claude-3-7-sonnet` for Bedrock.
- Enhanced modular chat system with server-aware tools.
- Rich command system with context-aware completions.
- **Conversation History**:
  - Track and review all messages exchanged during a session.
  - Filter to view specific messages or ranges.
  - Export or analyze conversation logs for debugging or reference.
- Two operational modes:
  - **Chat Mode**: Conversational interface with LLM
  - **Interactive Mode**: Command-line interface with slash commands

## Prerequisites
- Python 3.8 or higher.
- Required dependencies (see [Installation](#installation))
- If using ollama you should have ollama installed and running.
- If using openai you should have an api key set in your environment variables (OPENAI_API_KEY=yourkey)
- If using AWS Bedrock, you need valid AWS credentials configured (e.g., via aws sso login)

## Installation
1. Clone the repository:

```bash
git clone https://github.com/chrishayuk/mcp-cli
cd mcp-cli
```

2. Install UV:

```bash
pip install uv
```

3. Resynchronize dependencies:

```bash
uv sync --reinstall
```

## Command-line Arguments
- `--server`: Specifies the server configuration to use. Required.
- `--config-file`: (Optional) Path to the JSON configuration file. Defaults to `server_config.json`.
- `--provider`: (Optional) Specifies the provider to use (`openai`, `ollama`, or `bedrock`). Defaults to `openai`.
- `--model`: (Optional) Specifies the model to use. Defaults depend on the provider.
- `--debug`: (Optional) Enable debug mode for additional logging and troubleshooting.

## Chat Mode
Chat mode provides a conversational interface with the LLM and is the primary way to interact with the client:

```bash
uv run mcp-cli chat --server sqlite
```

You can specify the provider and model to use in chat mode:

```bash
uv run mcp-cli chat --server sqlite --provider openai --model gpt-4o
```

```bash
uv run mcp-cli chat --server sqlite --provider ollama --model llama3.2
```

```bash
uv run mcp-cli chat --server sqlite --provider bedrock --model claude-3-7-sonnet
```

### Using Chat Mode
In chat mode, you can interact with the model in natural language, and it will automatically use the available tools when needed. The LLM can execute queries, access data, and leverage other capabilities provided by the server.

### Conversation History
The client maintains a complete conversation history, which records every message exchanged during a session. This feature allows you to:

- **Review Previous Interactions**: Retrieve a complete log of the conversation to track context and decisions.
- **Analyze Dialogue Flow**: Use the conversation history to analyze how queries were resolved or to re-run commands.
- **Save Sessions**: Export conversation history to JSON files for later reference or analysis.
- **Filter Messages**: Display specific messages or ranges to focus on particular parts of the conversation.

To work with conversation history, use the following commands:

- `/conversation` or its alias `/ch`: Displays the entire conversation history.
- `/conversation <N>` or `/ch <N>`: Shows only message #N from the history (e.g., `/ch 4` shows only message #4).
- `/conversation <N> --json` or `/ch <N> --json`: Outputs a specific message in JSON format.
- `/conversation --json`: Outputs the entire conversation history in raw JSON format.
- `/conversation -n 5`: Shows only the last 5 messages.
- `/save <filename>`: Saves the current conversation history to a JSON file.
- `/compact`: Condenses conversation history into a summary to maintain context while reducing token usage.

### Tool History
The client also keeps track of tool calls made during the session, providing insight into how the model interacts with available tools:

- `/toolhistory` or `/th`: Shows all tool calls made during the session.
- `/toolhistory <N>` or `/th <N>`: Displays details for a specific tool call (e.g., `/th 3` shows only tool call #3).
- `/toolhistory -n 5` or `/th -n 5`: Shows only the last 5 tool calls.
- `/toolhistory --json` or `/th --json`: Outputs all tool calls in JSON format.

### Changing Provider and Model in Chat Mode
You can specify the provider and model when starting chat mode:

```bash
uv run mcp-cli chat --server sqlite --provider openai --model gpt-4o
```

You can also change the provider and model during a chat session using the following commands:

- `/provider <n>`: Change the current LLM provider (e.g., `openai`, `ollama`, `bedrock`)
- `/model <n>`: Change the current LLM model (e.g., `gpt-4o`, `llama3.2`, `claude-3-7-sonnet`)

### Chat Commands
In chat mode, you can use the following slash commands:

#### General Commands
- `/help`: Show available commands
- `/help <command>`: Show detailed help for a specific command
- `/quickhelp` or `/qh`: Display a quick reference of common commands
- `exit` or `quit`: Exit chat mode

#### Tool Commands
- `/tools`: Display all available tools with their server information
  - `/tools --all`: Show detailed tool information including parameters
  - `/tools --raw`: Show raw tool definitions
- `/toolhistory` or `/th`: Show history of tool calls in the current session
  - `/th <N>`: Show details for a specific tool call
  - `/th -n 5`: Show only the last 5 tool calls
  - `/th --json`: Show tool calls in JSON format

#### Conversation Commands
- `/conversation` or `/ch`: Show the conversation history
  - `/ch <N>`: Show a specific message from history
  - `/ch -n 5`: Show only the last 5 messages
  - `/ch <N> --json`: Show a specific message in JSON format
  - `/ch --json`: View the entire conversation history in raw JSON format
- `/save <filename>`: Save conversation history to a JSON file
- `/compact`: Condense conversation history into a summary

#### Other Commands
- `/cls`: Clear the screen while keeping conversation history
- `/clear`: Clear both the screen and conversation history
- `/interrupt`, `/stop`, or `/cancel`: Interrupt running tool execution
- `/provider <n>`: Change the current LLM provider 
- `/model <n>`: Change the current LLM model

## Interactive Mode
Interactive mode provides a command-line interface with slash commands for direct interaction with the server:

```bash
uv run mcp-cli interactive --server sqlite
```

You can also specify provider and model in interactive mode:

```bash
uv run mcp-cli interactive --server sqlite --provider ollama --model llama3.2
```

### Interactive Commands
In interactive mode, you can use the following slash commands:

- `/ping`: Check if server is responsive
- `/prompts`: List available prompts
- `/tools`: List available tools
- `/tools-all`: Show detailed tool information with parameters
- `/tools-raw`: Show raw tool definitions in JSON
- `/resources`: List available resources
- `/chat`: Enter chat mode
- `/cls`: Clear the screen
- `/clear`: Clear the screen and show welcome message
- `/help`: Show this help message
- `/exit` or `/quit`: Exit the program

You can also exit by typing `exit` or `quit` without the slash prefix.

## Using OpenAI Provider
If you wish to use OpenAI models, you should:

- Set the `OPENAI_API_KEY` environment variable before running the client, either in .env or as an environment variable.

## Using AWS Bedrock Provider
If you wish to use AWS Bedrock models, you should:

1. Configure AWS credentials (using AWS SSO or standard AWS credential methods)
   ```bash
   aws sso login
   ```

2. Configure the `server_config.json` file with Bedrock settings:
   ```json
   "llmProviders": {
     "bedrock": {
       "region": "eu-central-1",
       "models": {
         "claude-3-haiku": {
           "modelId": "anthropic.claude-3-haiku-20240307-v1:0",
           "arn": "arn:aws:bedrock:eu-central-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
         }
       }
     }
   }
   ```

3. Run the CLI with the Bedrock provider:
   ```bash
   uv run mcp-cli chat --server sqlite --provider bedrock --model claude-3-haiku
   ```

### Troubleshooting Bedrock

If you encounter an "AccessDeniedException" error when using Bedrock, check the following:

1. Make sure you have enabled the model in your AWS Bedrock account:
   - Go to the AWS Management Console > Amazon Bedrock > Model access
   - Find the Claude model and request access if not already enabled

2. Verify that your IAM role has the proper permissions:
   - The role you assume via SSO needs `bedrock:InvokeModel` permissions

3. Make sure your AWS SSO session is active:
   - Run `aws sts get-caller-identity` to verify your current credentials

## Project Structure

The project follows a modular architecture:

```
src/
├── cli/
│   ├── chat/
│   │   ├── commands/         # Chat slash commands
│   │   │   ├── conversation_history.py   # Conversation history command
│   │   │   ├── help.py                   # Help commands
│   │   │   ├── quickhelp.py              # Quick help command
│   │   │   └── tool_history.py           # Tool history command
│   │   ├── chat_context.py   # Chat state management
│   │   ├── chat_handler.py   # Main chat logic
│   │   ├── conversation.py   # Conversation processing
│   │   ├── ui_helpers.py     # UI utilities
│   │   └── ui_manager.py     # User interface management
│   ├── commands/             # Main CLI commands (including interactive mode)
│   └── ...
├── llm/                      # LLM client and tools
│   ├── providers/            # LLM providers
│   │   ├── base.py           # Base LLM client interface
│   │   ├── openai_client.py  # OpenAI provider
│   │   ├── ollama_client.py  # Ollama provider
│   │   └── bedrock_client.py # AWS Bedrock provider
└── ...
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request with your proposed changes.

## License
This project is licensed under the [MIT License](license.md).