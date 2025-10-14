"""Terminal command execution tool."""

from typing import Any, Dict, List
import asyncio
from src.tools.base import BaseTool


class TerminalTool(BaseTool):
    """Tool for executing terminal commands."""

    def __init__(self) -> None:
        """Initialize terminal tool."""
        super().__init__("terminal")

    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Any:
        """Execute terminal operation."""
        if operation == "run_command":
            return await self._run_command(parameters)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _run_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a shell command."""
        command = params["command"]
        timeout = params.get("timeout", 30)

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            return {
                "command": command,
                "returncode": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "success": process.returncode == 0,
            }

        except asyncio.TimeoutError:
            return {
                "command": command,
                "error": "Command timed out",
                "success": False,
            }
        except Exception as e:
            return {
                "command": command,
                "error": str(e),
                "success": False,
            }

    def get_definitions(self) -> List[Dict[str, Any]]:
        """Get function definitions."""
        return [
            {
                "name": "run_command",
                "description": "Execute a shell command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to execute"},
                        "timeout": {
                            "type": "integer",
                            "description": "Command timeout in seconds (default: 30)",
                        },
                    },
                    "required": ["command"],
                },
            }
        ]
