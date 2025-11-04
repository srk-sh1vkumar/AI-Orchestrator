"""Tool output validation with schema checking."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ValidationError, field_validator
from src.models.schemas import ToolType, ToolResult
from enum import Enum
import structlog

logger = structlog.get_logger()


class ValidationStatus(str, Enum):
    """Validation status."""
    VALID = "valid"
    INVALID = "invalid"
    PARTIAL = "partial"  # Some fields valid, some invalid
    SKIPPED = "skipped"  # Validation skipped (e.g., no schema)


class ValidationResult(BaseModel):
    """Result of output validation."""
    status: ValidationStatus
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_output: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# OUTPUT SCHEMAS FOR EACH TOOL TYPE
# ============================================================================

class GitHubIssueOutput(BaseModel):
    """Schema for GitHub create_issue output."""
    number: int = Field(..., ge=1, description="Issue number")
    url: str = Field(..., min_length=1, description="Issue URL")


class GitHubPROutput(BaseModel):
    """Schema for GitHub create_pr output."""
    number: int = Field(..., ge=1, description="PR number")
    url: str = Field(..., min_length=1, description="PR URL")


class GitHubRepoInfo(BaseModel):
    """Schema for GitHub repository info."""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    stars: int = Field(..., ge=0)
    forks: int = Field(..., ge=0)
    url: str = Field(..., min_length=1)


class GitHubRepoListItem(BaseModel):
    """Schema for GitHub repository list item."""
    name: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)


class DockerContainerInfo(BaseModel):
    """Schema for Docker container information."""
    id: str = Field(..., min_length=12, max_length=64, description="Container ID")
    name: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    image: str = Field(..., min_length=1)


class DockerImageInfo(BaseModel):
    """Schema for Docker image information."""
    id: str = Field(..., min_length=12, max_length=64)
    tags: List[str] = Field(default_factory=list)
    size: int = Field(..., ge=0)


class KubernetesPodInfo(BaseModel):
    """Schema for Kubernetes pod information."""
    name: str = Field(..., min_length=1)
    namespace: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    ready: bool


class KubernetesDeploymentInfo(BaseModel):
    """Schema for Kubernetes deployment information."""
    name: str = Field(..., min_length=1)
    namespace: str = Field(..., min_length=1)
    replicas: int = Field(..., ge=0)
    ready_replicas: int = Field(..., ge=0)


class FileOperationResult(BaseModel):
    """Schema for file system operation results."""
    success: bool
    path: str = Field(..., min_length=1)
    message: Optional[str] = None
    size: Optional[int] = Field(None, ge=0)


class TerminalCommandResult(BaseModel):
    """Schema for terminal command results."""
    stdout: str
    stderr: str
    exit_code: int
    command: str = Field(..., min_length=1)


# ============================================================================
# TOOL OUTPUT VALIDATOR
# ============================================================================

class ToolOutputValidator:
    """Validates tool execution outputs against schemas."""

    def __init__(self):
        """Initialize validator."""
        self.logger = logger.bind(component="tool_validator")
        self._init_schemas()

    def _init_schemas(self):
        """Initialize schema mappings for each tool type and operation."""
        self.schemas: Dict[ToolType, Dict[str, BaseModel]] = {
            ToolType.GITHUB: {
                "create_issue": GitHubIssueOutput,
                "create_pr": GitHubPROutput,
                "get_repo_info": GitHubRepoInfo,
                "list_repos": List[GitHubRepoListItem],  # type: ignore
            },
            ToolType.DOCKER: {
                "list_containers": List[DockerContainerInfo],  # type: ignore
                "get_container": DockerContainerInfo,
                "list_images": List[DockerImageInfo],  # type: ignore
            },
            ToolType.KUBERNETES: {
                "list_pods": List[KubernetesPodInfo],  # type: ignore
                "get_pod": KubernetesPodInfo,
                "list_deployments": List[KubernetesDeploymentInfo],  # type: ignore
            },
            ToolType.FILE_SYSTEM: {
                "read_file": str,  # Simple string output
                "write_file": FileOperationResult,
                "delete_file": FileOperationResult,
                "list_directory": List[str],  # type: ignore
            },
            ToolType.TERMINAL: {
                "execute": TerminalCommandResult,
            },
        }

    def validate(
        self,
        tool_result: ToolResult,
        strict: bool = False
    ) -> ValidationResult:
        """Validate tool execution result.

        Args:
            tool_result: Result from tool execution
            strict: If True, raise exception on validation failure
                    If False, log warning and return invalid result

        Returns:
            ValidationResult with validation status and details
        """
        # If tool execution failed, skip validation
        if not tool_result.success:
            return ValidationResult(
                status=ValidationStatus.SKIPPED,
                is_valid=True,  # Don't penalize execution failures
                warnings=["Tool execution failed, skipping output validation"],
                validated_output=None,
                metadata={"reason": "execution_failure", "error": tool_result.error}
            )

        # Get schema for this tool type and operation
        schema = self._get_schema(tool_result.tool_type, tool_result.operation)

        if schema is None:
            # No schema defined for this operation
            self.logger.warning(
                "no_schema_defined",
                tool_type=tool_result.tool_type,
                operation=tool_result.operation
            )
            return ValidationResult(
                status=ValidationStatus.SKIPPED,
                is_valid=True,  # Don't fail if no schema
                warnings=[f"No validation schema for {tool_result.tool_type}.{tool_result.operation}"],
                validated_output=tool_result.result,
                metadata={"reason": "no_schema"}
            )

        # Validate output against schema
        return self._validate_against_schema(
            output=tool_result.result,
            schema=schema,
            tool_type=tool_result.tool_type,
            operation=tool_result.operation,
            strict=strict
        )

    def _get_schema(
        self,
        tool_type: ToolType,
        operation: str
    ) -> Optional[Union[BaseModel, type]]:
        """Get validation schema for tool type and operation."""
        if tool_type not in self.schemas:
            return None

        return self.schemas[tool_type].get(operation)

    def _validate_against_schema(
        self,
        output: Any,
        schema: Union[BaseModel, type],
        tool_type: ToolType,
        operation: str,
        strict: bool
    ) -> ValidationResult:
        """Validate output against Pydantic schema."""
        errors = []
        warnings = []
        validated_output = None

        try:
            # Handle list outputs
            if hasattr(schema, "__origin__") and schema.__origin__ is list:  # type: ignore
                item_schema = schema.__args__[0]  # type: ignore
                if not isinstance(output, list):
                    errors.append(f"Expected list output, got {type(output).__name__}")
                    return ValidationResult(
                        status=ValidationStatus.INVALID,
                        is_valid=False,
                        errors=errors,
                        validated_output=output,
                        metadata={"schema": str(schema)}
                    )

                validated_items = []
                for i, item in enumerate(output):
                    try:
                        validated_item = item_schema(**item) if isinstance(item, dict) else item_schema(item)
                        validated_items.append(validated_item.model_dump() if hasattr(validated_item, 'model_dump') else validated_item)
                    except ValidationError as e:
                        errors.append(f"Item {i} validation failed: {str(e)}")
                        if strict:
                            raise

                validated_output = validated_items

            # Handle string outputs
            elif schema is str:
                if not isinstance(output, str):
                    errors.append(f"Expected string output, got {type(output).__name__}")
                    if strict:
                        raise ValueError(f"Expected string, got {type(output).__name__}")
                else:
                    validated_output = output

            # Handle Pydantic model outputs
            elif isinstance(schema, type) and issubclass(schema, BaseModel):
                if not isinstance(output, dict):
                    errors.append(f"Expected dict output for {schema.__name__}, got {type(output).__name__}")
                    if strict:
                        raise ValueError(f"Expected dict, got {type(output).__name__}")
                else:
                    validated_model = schema(**output)
                    validated_output = validated_model.model_dump()

            # Unknown schema type
            else:
                warnings.append(f"Unknown schema type: {schema}")
                validated_output = output

            # Determine status
            if errors:
                status = ValidationStatus.INVALID
                is_valid = False
                self.logger.error(
                    "validation_failed",
                    tool_type=tool_type,
                    operation=operation,
                    errors=errors
                )
            else:
                status = ValidationStatus.VALID
                is_valid = True
                self.logger.info(
                    "validation_passed",
                    tool_type=tool_type,
                    operation=operation
                )

            return ValidationResult(
                status=status,
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                validated_output=validated_output,
                metadata={"schema": str(schema), "tool_type": tool_type.value, "operation": operation}
            )

        except ValidationError as e:
            error_details = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
            self.logger.error(
                "pydantic_validation_error",
                tool_type=tool_type,
                operation=operation,
                errors=error_details
            )

            return ValidationResult(
                status=ValidationStatus.INVALID,
                is_valid=False,
                errors=error_details,
                validated_output=output,  # Return original output
                metadata={"schema": str(schema), "validation_error": str(e)}
            )

        except Exception as e:
            self.logger.error(
                "validation_exception",
                tool_type=tool_type,
                operation=operation,
                error=str(e)
            )

            return ValidationResult(
                status=ValidationStatus.INVALID,
                is_valid=False,
                errors=[f"Validation exception: {str(e)}"],
                validated_output=output,
                metadata={"exception": str(e)}
            )


# Global validator instance
_validator: Optional[ToolOutputValidator] = None


def get_validator() -> ToolOutputValidator:
    """Get global validator instance (singleton)."""
    global _validator
    if _validator is None:
        _validator = ToolOutputValidator()
    return _validator
