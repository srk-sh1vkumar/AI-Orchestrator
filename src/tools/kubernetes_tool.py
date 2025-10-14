"""Kubernetes integration tool."""

from typing import Any, Dict, List
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from src.tools.base import BaseTool
from src.core.config import settings


class KubernetesTool(BaseTool):
    """Tool for Kubernetes operations."""

    def __init__(self) -> None:
        """Initialize Kubernetes tool."""
        super().__init__("kubernetes")
        try:
            config.load_kube_config(config_file=settings.kubernetes_config_path)
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
        except Exception as e:
            self.logger.warning("kubernetes_client_unavailable", error=str(e))
            self.v1 = None
            self.apps_v1 = None

    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Any:
        """Execute Kubernetes operation."""
        if not self.v1:
            raise ValueError("Kubernetes client not available")

        if operation == "list_pods":
            return await self._list_pods(parameters)
        elif operation == "list_deployments":
            return await self._list_deployments(parameters)
        elif operation == "scale_deployment":
            return await self._scale_deployment(parameters)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _list_pods(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List pods."""
        namespace = params.get("namespace", "default")
        pods = self.v1.list_namespaced_pod(namespace)
        return [
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "ip": pod.status.pod_ip,
            }
            for pod in pods.items
        ]

    async def _list_deployments(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List deployments."""
        namespace = params.get("namespace", "default")
        deployments = self.apps_v1.list_namespaced_deployment(namespace)
        return [
            {
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "replicas": dep.spec.replicas,
                "available_replicas": dep.status.available_replicas,
            }
            for dep in deployments.items
        ]

    async def _scale_deployment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scale a deployment."""
        namespace = params.get("namespace", "default")
        name = params["name"]
        replicas = params["replicas"]

        deployment = self.apps_v1.read_namespaced_deployment(name, namespace)
        deployment.spec.replicas = replicas
        self.apps_v1.patch_namespaced_deployment(name, namespace, deployment)

        return {"name": name, "replicas": replicas, "status": "scaled"}

    def get_definitions(self) -> List[Dict[str, Any]]:
        """Get function definitions."""
        return [
            {
                "name": "list_pods",
                "description": "List Kubernetes pods",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string", "description": "Namespace (default: default)"}
                    },
                },
            },
            {
                "name": "scale_deployment",
                "description": "Scale a Kubernetes deployment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Deployment name"},
                        "replicas": {"type": "integer", "description": "Number of replicas"},
                        "namespace": {"type": "string", "description": "Namespace (default: default)"},
                    },
                    "required": ["name", "replicas"],
                },
            },
        ]

    async def health_check(self) -> bool:
        """Check Kubernetes connectivity."""
        try:
            if not self.v1:
                return False
            self.v1.list_namespace()
            return True
        except ApiException:
            return False
