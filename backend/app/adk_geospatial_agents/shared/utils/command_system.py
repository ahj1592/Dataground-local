"""
Command System for Chat Reset and Navigation
"""

import time
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

class ResetType(Enum):
    """Types of reset operations"""
    FULL_RESET = "full"      # Complete reset
    PARAMETER_RESET = "param"  # Parameters only reset
    STEP_BACK = "step"       # One step back
    HOME = "home"           # Return to home

@dataclass
class Command:
    """Command data structure"""
    type: str
    original_message: str
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class CommandParser:
    """Parser for slash commands"""
    
    def __init__(self):
        # Supported commands (English only)
        self.command_map = {
            "/reset": ResetType.FULL_RESET,
            "/home": ResetType.HOME,
            "/back": ResetType.STEP_BACK,
            "/clear": ResetType.PARAMETER_RESET,
            "/help": "help",
            "/status": "status"
        }
        
        # Command descriptions
        self.command_descriptions = {
            "/reset": "Complete reset - start a new chat session",
            "/home": "Return to home - show welcome message",
            "/back": "Go back one step in parameter collection",
            "/clear": "Clear current parameters only",
            "/help": "Show available commands",
            "/status": "Show current analysis status"
        }
    
    def parse_command(self, message: str) -> Optional[Command]:
        """Parse message to detect commands"""
        message_lower = message.lower().strip()
        
        # Only process slash commands
        if message_lower.startswith('/'):
            return self._parse_slash_command(message_lower)
        
        return None
    
    def _parse_slash_command(self, message: str) -> Optional[Command]:
        """Parse slash command"""
        if message in self.command_map:
            return Command(
                type=self.command_map[message],
                original_message=message
            )
        
        return None
    
    def get_help_message(self) -> str:
        """Get help message with all available commands"""
        help_lines = ["Available commands:"]
        for cmd, desc in self.command_descriptions.items():
            help_lines.append(f"{cmd} - {desc}")
        return "\n".join(help_lines)

class CommandExecutor:
    """Executor for commands"""
    
    def __init__(self):
        # Reset messages
        self.reset_messages = {
            ResetType.FULL_RESET: "Chat has been reset. How can I help you with your analysis?",
            ResetType.HOME: "Welcome back! What would you like to analyze?",
            ResetType.STEP_BACK: "Returned to the previous step.",
            ResetType.PARAMETER_RESET: "Parameters have been cleared. Let's start collecting them again.",
            "help": None,  # Will be set dynamically
            "status": None  # Will be set dynamically
        }
    
    async def execute_command(self, command: Command, user_id: int, 
                            callback_context: Any) -> Dict[str, Any]:
        """Execute a command"""
        print(f"🔧 [CommandExecutor] Executing command: {command.type}")
        
        if command.type == "help":
            return await self._execute_help_command()
        elif command.type == "status":
            return await self._execute_status_command(user_id, callback_context)
        elif isinstance(command.type, ResetType):
            return await self._execute_reset_command(command.type, user_id, callback_context)
        else:
            return {
                "message": f"Unknown command: {command.original_message}",
                "status": "error"
            }
    
    async def _execute_help_command(self) -> Dict[str, Any]:
        """Execute help command"""
        parser = CommandParser()
        help_message = parser.get_help_message()
        
        return {
            "message": help_message,
            "status": "command_help"
        }
    
    async def _execute_status_command(self, user_id: int, callback_context: Any) -> Dict[str, Any]:
        """Execute status command"""
        user_states = callback_context.state.get("user_states", {})
        user_state = user_states.get(user_id, {})
        
        analysis_type = user_state.get("analysis_type", "None")
        status = user_state.get("status", "idle")
        collected_params = user_state.get("collected_params", {})
        
        # Format collected parameters
        params_text = "None"
        if collected_params:
            param_items = []
            for key, value in collected_params.items():
                if key not in ['suggestion_message', 'suggested_city', 'suggested_country', 'location_error']:
                    param_items.append(f"{key}: {value}")
            if param_items:
                params_text = ", ".join(param_items)
        
        status_message = f"Current analysis type: {analysis_type}\n"
        status_message += f"Status: {status}\n"
        status_message += f"Collected parameters: {params_text}"
        
        return {
            "message": status_message,
            "status": "command_status"
        }
    
    async def _execute_reset_command(self, reset_type: ResetType, user_id: int, 
                                   callback_context: Any) -> Dict[str, Any]:
        """Execute reset command"""
        print(f"🔧 [CommandExecutor] Executing reset: {reset_type.value}")
        
        user_states = callback_context.state.get("user_states", {})
        if user_id not in user_states:
            user_states[user_id] = {}
        
        user_state = user_states[user_id]
        
        # Execute reset based on type
        if reset_type == ResetType.FULL_RESET:
            await self._full_reset(user_state)
        elif reset_type == ResetType.HOME:
            await self._home_reset(user_state)
        elif reset_type == ResetType.STEP_BACK:
            await self._step_back_reset(user_state)
        elif reset_type == ResetType.PARAMETER_RESET:
            await self._parameter_reset(user_state)
        
        # Add command to conversation context
        if "conversation_context" not in user_state:
            user_state["conversation_context"] = []
        
        user_state["conversation_context"].append({
            "role": "user",
            "content": f"Command: {reset_type.value}",
            "timestamp": "now"
        })
        
        return {
            "message": self.reset_messages[reset_type],
            "status": "command_reset",
            "reset_type": reset_type.value
        }
    
    async def _full_reset(self, user_state: Dict[str, Any]):
        """Perform full reset"""
        user_state.update({
            "status": "idle",
            "analysis_type": None,
            "collected_params": {},
            "conversation_context": [],
            "last_reset_time": time.time()
        })
        print(f"🔧 [CommandExecutor] Full reset completed")
    
    async def _home_reset(self, user_state: Dict[str, Any]):
        """Perform home reset"""
        user_state.update({
            "status": "idle",
            "analysis_type": None,
            "collected_params": {},
            "last_reset_time": time.time()
        })
        print(f"🔧 [CommandExecutor] Home reset completed")
    
    async def _step_back_reset(self, user_state: Dict[str, Any]):
        """Perform step back reset"""
        # Keep analysis_type but reset parameters
        user_state["collected_params"] = {}
        if user_state.get("status") == "awaiting_confirmation":
            user_state["status"] = "collecting_parameters"
        print(f"🔧 [CommandExecutor] Step back reset completed")
    
    async def _parameter_reset(self, user_state: Dict[str, Any]):
        """Perform parameter reset"""
        user_state["collected_params"] = {}
        if user_state.get("status") in ["collecting_parameters", "awaiting_confirmation"]:
            user_state["status"] = "collecting_parameters"
        print(f"🔧 [CommandExecutor] Parameter reset completed")

# Global instances
command_parser = CommandParser()
command_executor = CommandExecutor()
