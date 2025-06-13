from typing import List, Optional, Union
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult

class MessageTool(BaseTool):
    """Message tool class, providing message sending functions for user interaction"""

    name: str = "message"
    
    def __init__(self):
        """Initialize message tool class"""
        super().__init__()
        
    @tool(
        name="message_notify_user",
        description="Send a message to user without requiring a response. Use for acknowledging receipt of messages, providing progress updates, reporting task completion, or explaining changes in approach.",
        parameters={
            "text": {
                "type": "string",
                "description": "Message text to display to user"
            }
        },
        required=["text"]
    )
    async def message_notify_user(
        self,
        text: str
    ) -> ToolResult:
        """Send notification message to user, no response needed
        
        Args:
            text: Message text to display to user
            
        Returns:
            Message sending result
        """
            
        # Return success result, actual UI display logic implemented by caller
        return ToolResult(
            success=True,
            data=text
        )
    