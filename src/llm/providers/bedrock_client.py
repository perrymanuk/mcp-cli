# src/llm/providers/bedrock_client.py
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

# Base client
from llm.providers.base import BaseLLMClient

class BedrockLLMClient(BaseLLMClient):
    def __init__(self, model: str = "claude-3-sonnet", region: str = "eu-central-1", 
                 model_id: str = None, arn: str = None, **kwargs):
        self.model = model
        self.region = region
        self.model_id = model_id
        self.arn = arn
        self.debug = kwargs.get('debug', False)
        
        # Load config if needed
        if not self.model_id or not self.arn:
            self._load_model_config()
            
        # Initialize AWS Bedrock client
        try:
            # Import boto3 only when needed to avoid issues if it's not installed
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            logging.info(f"Initializing AWS Bedrock client in region {self.region}")
            
            try:
                self.client = boto3.client('bedrock-runtime', region_name=self.region)
                if self.debug:
                    # Try to verify credentials if in debug mode
                    sts = boto3.client('sts')
                    identity = sts.get_caller_identity()
                    logging.info(f"AWS credentials valid")
            except NoCredentialsError:
                logging.error("No AWS credentials found. Run 'aws sso login' to authenticate.")
                raise ValueError("No AWS credentials found. Run 'aws sso login' to authenticate.")
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                logging.error(f"AWS Bedrock client error: {error_code}")
                raise ValueError(f"AWS Bedrock client error: {str(e)}")
                
        except ImportError:
            raise ValueError("boto3 is not installed. Please install it using 'pip install boto3' or 'uv sync --reinstall'")
        except Exception as e:
            logging.error(f"Failed to initialize AWS Bedrock client: {str(e)}")
            raise ValueError(f"AWS Bedrock client initialization error: {str(e)}")
    
    def _load_model_config(self):
        """Load model configuration from config.json if available"""
        try:
            with open("server_config.json", "r") as f:
                config = json.load(f)
                
            bedrock_config = config.get("llmProviders", {}).get("bedrock", {})
            model_config = bedrock_config.get("models", {}).get(self.model, {})
            
            if not self.model_id:
                self.model_id = model_config.get("modelId")
            if not self.region:
                self.region = bedrock_config.get("region", "eu-central-1")
            if not self.arn:
                self.arn = model_config.get("arn")
                
        except Exception as e:
            logging.warning(f"Failed to load Bedrock model config: {str(e)}")
    
    def create_completion(self, messages: List[Dict], tools: List = None) -> Dict[str, Any]:
        try:
            # Ensure boto3 is imported
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            # Format messages for the Claude model
            formatted_messages = self._format_messages(messages)
            
            # Format tools for Claude if provided
            if tools and len(tools) > 0:
                formatted_tools = self._format_tools(tools)
            else:
                formatted_tools = None
            
            # Prepare the request body
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": formatted_messages
            }
            
            # Add tools if available
            if formatted_tools:
                request_body["tool_choice"] = "auto"  # Let Claude choose when to use tools
                request_body["tools"] = formatted_tools
            
            # Invoke the model
            try:
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body)
                )
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                error_msg = e.response.get('Error', {}).get('Message', str(e))
                
                if error_code == "AccessDeniedException":
                    logging.error(f"Access denied to Bedrock model: {self.model_id}")
                    logging.error("Please check:")
                    logging.error("1. You have enabled this model in your AWS Bedrock console")
                    logging.error("2. Your IAM role has bedrock:InvokeModel permission")
                    logging.error("3. You have an active AWS session (run 'aws sts get-caller-identity')")
                elif error_code == "ValidationException":
                    if "messages" in error_msg:
                        logging.error(f"Message format validation error: {error_msg}")
                        logging.error("Try the /reset command to clear conversation history")
                    else:
                        logging.error(f"Validation error: {error_msg}")
                else:
                    logging.error(f"Bedrock API Error ({error_code}): {error_msg}")
                
                raise ValueError(f"Bedrock API Error: {error_code} - {error_msg}")
            except NoCredentialsError:
                logging.error("No AWS credentials found.")
                logging.error("Run 'aws sso login' to authenticate with AWS.")
                raise ValueError("No AWS credentials found. Run 'aws sso login' to authenticate.")
            except Exception as e:
                logging.error(f"Unexpected error invoking Bedrock model: {str(e)}")
                raise ValueError(f"Bedrock API Error: {str(e)}")
            
            # Process the response
            response_body = json.loads(response['body'].read().decode('utf-8'))
            
            # Extract content and tool calls
            content = response_body.get('content', [{"type": "text", "text": "No response"}])
            text_content = ""
            tool_calls = []
            
            # Process different content blocks
            for block in content:
                if block.get("type") == "text":
                    text_content += block.get("text", "")
                elif block.get("type") == "tool_use":
                    tool_use = block.get("tool_use", {})
                    if not tool_use.get("name"):
                        logging.warning(f"Received tool_use without name")
                        continue
                        
                    tool_id = f"call_{tool_use.get('name')}_{str(uuid.uuid4())[:8]}"
                    tool_inputs = tool_use.get("input", {}) 
                    
                    # Create a tool call in the format expected by the tool processor
                    tool_call = {
                        "id": tool_id,
                        "type": "function",
                        "function": {
                            "name": tool_use.get("name"),
                            "arguments": json.dumps(tool_inputs, ensure_ascii=False)
                        }
                    }
                    
                    tool_calls.append(tool_call)
            
            # Return standardized response format
            return {
                "response": text_content,
                "tool_calls": tool_calls,
            }
            
        except Exception as e:
            logging.error(f"Bedrock API Error: {str(e)}")
            raise ValueError(f"Bedrock API Error: {str(e)}")
    
    def _format_messages(self, messages: List[Dict]) -> List[Dict]:
        """Format messages for Bedrock API"""
        formatted_messages = []
        
        # First, filter out empty messages and sanitize content
        filtered_messages = []
        for i, message in enumerate(messages):
            role = message.get("role")
            content = message.get("content")
            
            # Skip empty messages, except for the final assistant message which can be empty
            if content is None or content == "":
                continue
            
            # Ensure content is a string
            if not isinstance(content, str):
                content = str(content)
            
            filtered_messages.append({"role": role, "content": content})
        
        # Process the filtered messages
        for i, message in enumerate(filtered_messages):
            role = message.get("role")
            content = message.get("content")
            
            if role == "system":
                # System messages handled differently in Claude
                formatted_messages.append({
                    "role": "user",
                    "content": [{"type": "text", "text": f"<s>\n{content}\n</s>"}]
                })
                # Add an assistant response to complete the turn
                formatted_messages.append({
                    "role": "assistant",
                    "content": [{"type": "text", "text": "I'll help you with that."}]
                })
            elif role == "user":
                formatted_messages.append({
                    "role": "user",
                    "content": [{"type": "text", "text": content}]
                })
            elif role == "assistant":
                # Handle potential tool calls in assistant messages
                formatted_content = []
                
                # Add text content if present
                if content:
                    formatted_content.append({"type": "text", "text": content})
                
                # Only add assistant message if there's actual content or it's the last message
                if formatted_content:
                    formatted_messages.append({
                        "role": "assistant",
                        "content": formatted_content
                    })
        
        # Ensure the conversation follows Claude's requirements:
        # 1. Must start with a user message
        # 2. Must alternate between user and assistant messages
        # 3. All messages must have content (except optional final assistant message)
        
        # Fix first message - must be a user message
        if not formatted_messages:
            # If no messages at all, add a default user message
            formatted_messages.append({
                "role": "user",
                "content": [{"type": "text", "text": "Hello"}]
            })
        elif formatted_messages[0]["role"] != "user":
            # Prepend a user message if first message is not from user
            formatted_messages.insert(0, {
                "role": "user",
                "content": [{"type": "text", "text": "Hello"}]
            })
        
        # Ensure all messages alternate correctly and have content
        # Claude expects pattern: user->assistant->user->assistant...
        valid_messages = [formatted_messages[0]]  # Start with first message (which is now guaranteed to be from user)
        
        for i in range(1, len(formatted_messages)):
            curr_msg = formatted_messages[i]
            prev_msg = valid_messages[-1]
            
            if curr_msg["role"] != prev_msg["role"]:
                # Role is alternating correctly, check content
                if len(curr_msg["content"]) > 0:
                    valid_messages.append(curr_msg)
            else:
                # Same role as previous message, need to insert a dummy message
                if curr_msg["role"] == "user":
                    # Insert assistant message before this user message
                    valid_messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": "I understand."}]
                    })
                else:  # assistant
                    # Insert user message before this assistant message
                    valid_messages.append({
                        "role": "user",
                        "content": [{"type": "text", "text": "Please continue."}]
                    })
                # Now add the current message
                if len(curr_msg["content"]) > 0:
                    valid_messages.append(curr_msg)
        
        # Ensure the conversation ends with an assistant message if it ends with user
        if valid_messages and valid_messages[-1]["role"] == "user":
            valid_messages.append({
                "role": "assistant",
                "content": [{"type": "text", "text": "I'll help you with that."}]
            })
        
        return valid_messages
    
    def _format_tools(self, tools: List) -> List[Dict]:
        """Format tools for Bedrock API"""
        formatted_tools = []
        
        for i, tool in enumerate(tools):
            # Validate tool has a name
            if not tool.get("name"):
                logging.warning(f"Tool missing name - skipping")
                continue
            
            # Claude 3 uses 'tools' array with 'function' objects
            formatted_tool = {
                "type": "function",
                "function": {
                    "name": tool.get("name", f"tool_{i}"),  # Ensure name is never empty
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
            
            formatted_tools.append(formatted_tool)
        
        return formatted_tools