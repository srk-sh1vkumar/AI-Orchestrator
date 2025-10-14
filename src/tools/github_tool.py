"""GitHub integration tool."""

from typing import Any, Dict, List
from github import Github, GithubException
from src.tools.base import BaseTool
from src.core.config import settings


class GitHubTool(BaseTool):
    """Tool for GitHub operations."""

    def __init__(self) -> None:
        """Initialize GitHub tool."""
        super().__init__("github")
        self.client = Github(settings.github_token) if settings.github_token else None

    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Any:
        """Execute GitHub operation.

        Args:
            operation: Operation name
            parameters: Operation parameters

        Returns:
            Operation result
        """
        if not self.client:
            raise ValueError("GitHub token not configured")

        if operation == "create_issue":
            return await self._create_issue(parameters)
        elif operation == "create_pr":
            return await self._create_pr(parameters)
        elif operation == "list_repos":
            return await self._list_repos(parameters)
        elif operation == "get_repo_info":
            return await self._get_repo_info(parameters)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub issue."""
        repo = self.client.get_repo(params["repo"])
        issue = repo.create_issue(
            title=params["title"],
            body=params.get("body", ""),
            labels=params.get("labels", []),
        )
        return {"number": issue.number, "url": issue.html_url}

    async def _create_pr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pull request."""
        repo = self.client.get_repo(params["repo"])
        pr = repo.create_pull(
            title=params["title"],
            body=params.get("body", ""),
            head=params["head"],
            base=params.get("base", "main"),
        )
        return {"number": pr.number, "url": pr.html_url}

    async def _list_repos(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List repositories."""
        repos = self.client.get_user().get_repos()
        return [{"name": repo.name, "url": repo.html_url} for repo in repos[:10]]

    async def _get_repo_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository information."""
        repo = self.client.get_repo(params["repo"])
        return {
            "name": repo.name,
            "description": repo.description,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "url": repo.html_url,
        }

    def get_definitions(self) -> List[Dict[str, Any]]:
        """Get function definitions."""
        return [
            {
                "name": "create_issue",
                "description": "Create a GitHub issue",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo": {"type": "string", "description": "Repository (owner/name)"},
                        "title": {"type": "string", "description": "Issue title"},
                        "body": {"type": "string", "description": "Issue body"},
                        "labels": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["repo", "title"],
                },
            },
            {
                "name": "create_pr",
                "description": "Create a pull request",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo": {"type": "string", "description": "Repository (owner/name)"},
                        "title": {"type": "string", "description": "PR title"},
                        "body": {"type": "string", "description": "PR body"},
                        "head": {"type": "string", "description": "Head branch"},
                        "base": {"type": "string", "description": "Base branch (default: main)"},
                    },
                    "required": ["repo", "title", "head"],
                },
            },
        ]

    async def health_check(self) -> bool:
        """Check GitHub API connectivity."""
        try:
            if not self.client:
                return False
            self.client.get_user()
            return True
        except GithubException:
            return False
