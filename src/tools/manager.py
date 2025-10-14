"""Tool manager for executing operations across systems."""

from typing import List, Dict, Any, Optional
from src.models.schemas import ToolCall, ToolResult, ToolType
from src.tools.github_tool import GitHubTool
from src.tools.docker_tool import DockerTool
from src.tools.kubernetes_tool import KubernetesTool
from src.tools.terminal_tool import TerminalTool
from src.tools.file_system_tool import FileSystemTool
import structlog
import time

logger = structlog.get_logger()


class ToolManager:
    """Manages and executes tools."""

    def __init__(self) -> None:
        """Initialize tool manager."""
        self.logger = logger.bind(component="tool_manager")
        self.tools: Dict[ToolType, Any] = {}
        self._init_tools()

    def _init_tools(self) -> None:
        """Initialize available tools."""
        try:
            self.tools[ToolType.GITHUB] = GitHubTool()
            self.tools[ToolType.DOCKER] = DockerTool()
            self.tools[ToolType.KUBERNETES] = KubernetesTool()
            self.tools[ToolType.TERMINAL] = TerminalTool()
            self.tools[ToolType.FILE_SYSTEM] = FileSystemTool()
            self.logger.info("tools_initialized", count=len(self.tools))
        except Exception as e:
            self.logger.error("tool_initialization_failed", error=str(e))

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for LLM function calling.

        Returns:
            List of tool definitions
        """
        definitions = []

        for tool_type, tool_instance in self.tools.items():
            if hasattr(tool_instance, "get_definitions"):
                definitions.extend(tool_instance.get_definitions())

        return definitions

    async def execute_tools(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """Execute a list of tool calls.

        Args:
            tool_calls: List of tool calls

        Returns:
            List of tool results
        """
        results: List[ToolResult] = []

        for tool_call in tool_calls:
            result = await self.execute_tool(tool_call)
            results.append(result)

        return results

    async def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a single tool call.

        Args:
            tool_call: Tool call to execute

        Returns:
            ToolResult
        """
        start_time = time.time()

        try:
            if tool_call.tool_type not in self.tools:
                raise ValueError(f"Tool type not available: {tool_call.tool_type}")

            tool_instance = self.tools[tool_call.tool_type]

            # Execute the operation
            result = await tool_instance.execute(
                operation=tool_call.operation,
                parameters=tool_call.parameters,
            )

            execution_time = time.time() - start_time

            self.logger.info(
                "tool_executed",
                tool_type=tool_call.tool_type,
                operation=tool_call.operation,
                success=True,
                time=execution_time,
            )

            return ToolResult(
                tool_type=tool_call.tool_type,
                operation=tool_call.operation,
                success=True,
                result=result,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time

            self.logger.error(
                "tool_execution_failed",
                tool_type=tool_call.tool_type,
                operation=tool_call.operation,
                error=str(e),
            )

            return ToolResult(
                tool_type=tool_call.tool_type,
                operation=tool_call.operation,
                success=False,
                error=str(e),
                execution_time=execution_time,
            )

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all tools.

        Returns:
            Dict mapping tool types to health status
        """
        health: Dict[str, bool] = {}

        for tool_type, tool_instance in self.tools.items():
            try:
                if hasattr(tool_instance, "health_check"):
                    is_healthy = await tool_instance.health_check()
                    health[tool_type.value] = is_healthy
                else:
                    health[tool_type.value] = True  # Assume healthy if no check
            except Exception as e:
                self.logger.error("tool_health_check_failed", tool_type=tool_type, error=str(e))
                health[tool_type.value] = False

        return health
