"""Base tool interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
import structlog

logger = structlog.get_logger()


class BaseTool(ABC):
    """Base class for tools."""

    def __init__(self, tool_name: str) -> None:
        """Initialize the tool.

        Args:
            tool_name: Name of the tool
        """
        self.tool_name = tool_name
        self.logger = logger.bind(tool=tool_name)

    @abstractmethod
    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool operation.

        Args:
            operation: Operation to perform
            parameters: Operation parameters

        Returns:
            Operation result
        """
        pass

    @abstractmethod
    def get_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for LLM function calling.

        Returns:
            List of function definitions
        """
        pass

    async def health_check(self) -> bool:
        """Check if the tool is healthy.

        Returns:
            True if healthy
        """
        return True
