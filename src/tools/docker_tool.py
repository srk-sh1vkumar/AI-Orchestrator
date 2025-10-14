"""Docker integration tool."""

from typing import Any, Dict, List
import docker
from docker.errors import DockerException
from src.tools.base import BaseTool
from src.core.config import settings


class DockerTool(BaseTool):
    """Tool for Docker operations."""

    def __init__(self) -> None:
        """Initialize Docker tool."""
        super().__init__("docker")
        try:
            self.client = docker.DockerClient(base_url=settings.docker_host)
        except DockerException:
            self.client = None
            self.logger.warning("docker_client_unavailable")

    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Any:
        """Execute Docker operation."""
        if not self.client:
            raise ValueError("Docker client not available")

        if operation == "list_containers":
            return await self._list_containers(parameters)
        elif operation == "start_container":
            return await self._start_container(parameters)
        elif operation == "stop_container":
            return await self._stop_container(parameters)
        elif operation == "build_image":
            return await self._build_image(parameters)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _list_containers(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List Docker containers."""
        all_containers = params.get("all", False)
        containers = self.client.containers.list(all=all_containers)
        return [
            {
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "none",
            }
            for c in containers
        ]

    async def _start_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a container."""
        container = self.client.containers.get(params["container_id"])
        container.start()
        return {"status": "started", "id": container.short_id}

    async def _stop_container(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a container."""
        container = self.client.containers.get(params["container_id"])
        container.stop()
        return {"status": "stopped", "id": container.short_id}

    async def _build_image(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build a Docker image."""
        image, logs = self.client.images.build(
            path=params["path"], tag=params.get("tag", "latest"), rm=True
        )
        return {"image_id": image.short_id, "tag": params.get("tag", "latest")}

    def get_definitions(self) -> List[Dict[str, Any]]:
        """Get function definitions."""
        return [
            {
                "name": "list_containers",
                "description": "List Docker containers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "all": {
                            "type": "boolean",
                            "description": "List all containers (default: false)",
                        }
                    },
                },
            },
            {
                "name": "start_container",
                "description": "Start a Docker container",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_id": {"type": "string", "description": "Container ID or name"}
                    },
                    "required": ["container_id"],
                },
            },
        ]

    async def health_check(self) -> bool:
        """Check Docker connectivity."""
        try:
            if not self.client:
                return False
            self.client.ping()
            return True
        except DockerException:
            return False
