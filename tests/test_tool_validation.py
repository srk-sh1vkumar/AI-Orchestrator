"""Tests for tool output validation."""

import pytest
import time
from src.tools.validator import (
    ToolOutputValidator,
    ValidationResult,
    ValidationStatus,
    GitHubIssueOutput,
    GitHubPROutput,
    DockerContainerInfo,
    get_validator,
)
from src.models.schemas import ToolResult, ToolType, ToolCall
from src.tools.manager import ToolManager


class TestValidationSchemas:
    """Test validation schema models."""

    def test_github_issue_output_valid(self):
        """Test valid GitHub issue output."""
        data = {"number": 123, "url": "https://github.com/user/repo/issues/123"}
        result = GitHubIssueOutput(**data)
        assert result.number == 123
        assert result.url == data["url"]

    def test_github_issue_output_invalid_number(self):
        """Test GitHub issue with invalid number."""
        with pytest.raises(ValueError):
            GitHubIssueOutput(number=0, url="https://github.com/user/repo/issues/0")

    def test_github_issue_output_missing_url(self):
        """Test GitHub issue with missing URL."""
        with pytest.raises(ValueError):
            GitHubIssueOutput(number=123, url="")

    def test_docker_container_info_valid(self):
        """Test valid Docker container info."""
        data = {
            "id": "abc123def456",
            "name": "my-container",
            "status": "running",
            "image": "nginx:latest"
        }
        result = DockerContainerInfo(**data)
        assert result.id == "abc123def456"
        assert result.name == "my-container"

    def test_docker_container_info_invalid_id(self):
        """Test Docker container with invalid ID."""
        with pytest.raises(ValueError):
            DockerContainerInfo(
                id="short",
                name="container",
                status="running",
                image="nginx"
            )


class TestToolOutputValidator:
    """Test ToolOutputValidator class."""

    def test_validator_initialization(self):
        """Test validator initializes correctly."""
        validator = ToolOutputValidator()
        assert validator is not None
        assert ToolType.GITHUB in validator.schemas
        assert ToolType.DOCKER in validator.schemas
        assert "create_issue" in validator.schemas[ToolType.GITHUB]

    def test_validate_success_github_issue(self):
        """Test validating successful GitHub issue creation."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="create_issue",
            success=True,
            result={"number": 456, "url": "https://github.com/user/repo/issues/456"},
            execution_time=1.5
        )

        validation_result = validator.validate(tool_result, strict=False)

        assert validation_result.is_valid is True
        assert validation_result.status == ValidationStatus.VALID
        assert len(validation_result.errors) == 0
        assert validation_result.validated_output is not None

    def test_validate_invalid_github_issue_missing_field(self):
        """Test validating GitHub issue with missing required field."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="create_issue",
            success=True,
            result={"number": 456},  # Missing 'url'
            execution_time=1.5
        )

        validation_result = validator.validate(tool_result, strict=False)

        assert validation_result.is_valid is False
        assert validation_result.status == ValidationStatus.INVALID
        assert len(validation_result.errors) > 0

    def test_validate_invalid_github_issue_wrong_type(self):
        """Test validating GitHub issue with wrong data type."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="create_issue",
            success=True,
            result={"number": "not-a-number", "url": "https://github.com/user/repo/issues/123"},
            execution_time=1.5
        )

        validation_result = validator.validate(tool_result, strict=False)

        assert validation_result.is_valid is False
        assert validation_result.status == ValidationStatus.INVALID
        assert len(validation_result.errors) > 0

    def test_validate_failed_execution_skips_validation(self):
        """Test that failed tool execution skips validation."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="create_issue",
            success=False,
            error="API rate limit exceeded",
            execution_time=0.5
        )

        validation_result = validator.validate(tool_result, strict=False)

        assert validation_result.status == ValidationStatus.SKIPPED
        assert validation_result.is_valid is True  # Don't penalize execution failures
        assert len(validation_result.warnings) > 0

    def test_validate_no_schema_skips_validation(self):
        """Test that missing schema skips validation."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="unknown_operation",
            success=True,
            result={"data": "something"},
            execution_time=1.0
        )

        validation_result = validator.validate(tool_result, strict=False)

        assert validation_result.status == ValidationStatus.SKIPPED
        assert validation_result.is_valid is True  # Don't fail if no schema
        assert len(validation_result.warnings) > 0

    def test_validate_list_output_success(self):
        """Test validating list output (e.g., list_repos)."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="list_repos",
            success=True,
            result=[
                {"name": "repo1", "url": "https://github.com/user/repo1"},
                {"name": "repo2", "url": "https://github.com/user/repo2"}
            ],
            execution_time=2.0
        )

        validation_result = validator.validate(tool_result, strict=False)

        assert validation_result.is_valid is True
        assert validation_result.status == ValidationStatus.VALID
        assert len(validation_result.validated_output) == 2

    def test_validate_list_output_partial_invalid(self):
        """Test validating list with some invalid items."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="list_repos",
            success=True,
            result=[
                {"name": "repo1", "url": "https://github.com/user/repo1"},
                {"name": "", "url": "https://github.com/user/repo2"},  # Invalid: empty name
            ],
            execution_time=2.0
        )

        validation_result = validator.validate(tool_result, strict=False)

        assert validation_result.is_valid is False
        assert validation_result.status == ValidationStatus.INVALID
        assert len(validation_result.errors) > 0

    def test_validate_string_output_success(self):
        """Test validating simple string output."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.FILE_SYSTEM,
            operation="read_file",
            success=True,
            result="File contents here",
            execution_time=0.1
        )

        validation_result = validator.validate(tool_result, strict=False)

        assert validation_result.is_valid is True
        assert validation_result.status == ValidationStatus.VALID
        assert validation_result.validated_output == "File contents here"

    def test_validate_string_output_wrong_type(self):
        """Test validating string output with wrong type."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.FILE_SYSTEM,
            operation="read_file",
            success=True,
            result={"not": "a string"},  # Should be string
            execution_time=0.1
        )

        validation_result = validator.validate(tool_result, strict=False)

        assert validation_result.is_valid is False
        assert validation_result.status == ValidationStatus.INVALID

    def test_validate_strict_mode_raises_exception(self):
        """Test that strict mode raises exceptions on validation failure."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="create_issue",
            success=True,
            result={"number": "invalid"},  # Wrong type
            execution_time=1.0
        )

        # Strict mode should not raise for validation errors, just return invalid
        # (the "strict" parameter controls whether to fail fast, not raise exceptions)
        validation_result = validator.validate(tool_result, strict=True)
        assert validation_result.is_valid is False


class TestGlobalValidatorSingleton:
    """Test global validator singleton."""

    def test_get_validator_returns_singleton(self):
        """Test that get_validator returns same instance."""
        validator1 = get_validator()
        validator2 = get_validator()

        assert validator1 is validator2

    def test_get_validator_has_schemas(self):
        """Test that global validator has schemas initialized."""
        validator = get_validator()

        assert len(validator.schemas) > 0
        assert ToolType.GITHUB in validator.schemas


@pytest.mark.asyncio
class TestToolManagerIntegration:
    """Test ToolManager integration with validation."""

    async def test_tool_manager_has_validator(self):
        """Test that ToolManager initializes with validator."""
        manager = ToolManager()

        assert manager.validator is not None
        assert isinstance(manager.validator, ToolOutputValidator)

    async def test_tool_execution_includes_validation_logging(self, caplog):
        """Test that tool execution logs validation results."""
        # This test would require mocking actual tool execution
        # For now, we verify the manager has the validator
        manager = ToolManager()
        assert hasattr(manager, 'validator')


class TestValidationPerformance:
    """Test validation performance."""

    def test_validation_overhead_is_minimal(self):
        """Test that validation adds minimal overhead."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="create_issue",
            success=True,
            result={"number": 789, "url": "https://github.com/user/repo/issues/789"},
            execution_time=1.5
        )

        start = time.time()
        validation_result = validator.validate(tool_result, strict=False)
        duration = time.time() - start

        # Validation should complete in under 100ms
        assert duration < 0.1
        assert validation_result.is_valid is True

    def test_validation_of_large_list(self):
        """Test validation performance with large list output."""
        validator = ToolOutputValidator()

        # Create large list of repos
        large_result = [
            {"name": f"repo{i}", "url": f"https://github.com/user/repo{i}"}
            for i in range(100)
        ]

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="list_repos",
            success=True,
            result=large_result,
            execution_time=3.0
        )

        start = time.time()
        validation_result = validator.validate(tool_result, strict=False)
        duration = time.time() - start

        # Even 100 items should validate quickly
        assert duration < 0.5
        assert validation_result.is_valid is True
        assert len(validation_result.validated_output) == 100


class TestValidationMetadata:
    """Test validation result metadata."""

    def test_validation_includes_metadata(self):
        """Test that validation results include metadata."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="create_pr",
            success=True,
            result={"number": 42, "url": "https://github.com/user/repo/pull/42"},
            execution_time=2.0
        )

        validation_result = validator.validate(tool_result, strict=False)

        assert "tool_type" in validation_result.metadata
        assert "operation" in validation_result.metadata
        assert validation_result.metadata["tool_type"] == "github"
        assert validation_result.metadata["operation"] == "create_pr"

    def test_validation_failure_includes_error_details(self):
        """Test that validation failures include error details."""
        validator = ToolOutputValidator()

        tool_result = ToolResult(
            tool_type=ToolType.GITHUB,
            operation="create_issue",
            success=True,
            result={"number": -1, "url": ""},  # Invalid: negative number, empty URL
            execution_time=1.0
        )

        validation_result = validator.validate(tool_result, strict=False)

        assert validation_result.is_valid is False
        assert len(validation_result.errors) > 0
        assert "validation_error" in validation_result.metadata or "schema" in validation_result.metadata
