"""File system operations tool."""

from typing import Any, Dict, List
import os
import aiofiles
from src.tools.base import BaseTool


class FileSystemTool(BaseTool):
    """Tool for file system operations."""

    def __init__(self) -> None:
        """Initialize file system tool."""
        super().__init__("file_system")

    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Any:
        """Execute file system operation."""
        if operation == "read_file":
            return await self._read_file(parameters)
        elif operation == "write_file":
            return await self._write_file(parameters)
        elif operation == "list_directory":
            return await self._list_directory(parameters)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file."""
        path = params["path"]
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
        return {"path": path, "content": content, "size": len(content)}

    async def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write to a file."""
        path = params["path"]
        content = params["content"]
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
        return {"path": path, "size": len(content), "success": True}

    async def _list_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List directory contents."""
        path = params.get("path", ".")
        entries = os.listdir(path)
        return {
            "path": path,
            "entries": entries,
            "count": len(entries),
        }

    def get_definitions(self) -> List[Dict[str, Any]]:
        """Get function definitions."""
        return [
            {
                "name": "read_file",
                "description": "Read contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "File path"}},
                    "required": ["path"],
                },
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "Content to write"},
                    },
                    "required": ["path", "content"],
                },
            },
        ]
