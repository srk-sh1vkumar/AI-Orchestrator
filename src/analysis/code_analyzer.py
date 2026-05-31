"""Code analyzer with AST parsing for signature extraction.

Enhancement 015: Extract function signatures, classes, and patterns from code.
"""

import ast
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class CodeSignature:
    """Extracted code signature from a function/class."""

    name: str
    signature_type: str  # function, class, method
    file_path: str
    line_number: int
    parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    body_hash: str  # Hash of normalized body
    complexity: int  # Cyclomatic complexity estimate
    imports: List[str]
    decorators: List[str]
    project: str
    extracted_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "signature_type": self.signature_type,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "docstring": self.docstring,
            "body_hash": self.body_hash,
            "complexity": self.complexity,
            "imports": self.imports,
            "decorators": self.decorators,
            "project": self.project,
            "extracted_at": self.extracted_at.isoformat(),
        }


class CodeAnalyzer:
    """Analyzes Python code to extract signatures and patterns."""

    def __init__(self) -> None:
        """Initialize code analyzer."""
        self.logger = logger.bind(component="code_analyzer")
        self._signatures: List[CodeSignature] = []

    def analyze_file(self, file_path: Path, project: str) -> List[CodeSignature]:
        """Analyze a single Python file.

        Args:
            file_path: Path to the Python file
            project: Project name/identifier

        Returns:
            List of extracted code signatures
        """
        signatures: List[CodeSignature] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            imports = self._extract_imports(tree)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    sig = self._extract_function_signature(node, file_path, project, imports)
                    signatures.append(sig)
                elif isinstance(node, ast.ClassDef):
                    sig = self._extract_class_signature(node, file_path, project, imports)
                    signatures.append(sig)
                    # Extract methods
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            method_sig = self._extract_function_signature(
                                item, file_path, project, imports, class_name=node.name
                            )
                            signatures.append(method_sig)

            self.logger.info(
                "file_analyzed",
                file=str(file_path),
                signatures=len(signatures),
            )

        except SyntaxError as e:
            self.logger.warning("syntax_error", file=str(file_path), error=str(e))
        except Exception as e:
            self.logger.error("analysis_error", file=str(file_path), error=str(e))

        return signatures

    def analyze_project(self, project_path: Path, project_name: str) -> List[CodeSignature]:
        """Analyze all Python files in a project.

        Args:
            project_path: Root path of the project
            project_name: Project identifier

        Returns:
            List of all extracted signatures
        """
        all_signatures: List[CodeSignature] = []

        # Find all Python files
        python_files = list(project_path.rglob("*.py"))

        # Exclude common directories
        exclude_dirs = {"venv", "env", ".venv", "__pycache__", "node_modules", ".git", "dist", "build"}
        python_files = [
            f for f in python_files
            if not any(excluded in f.parts for excluded in exclude_dirs)
        ]

        self.logger.info(
            "analyzing_project",
            project=project_name,
            files=len(python_files),
        )

        for file_path in python_files:
            signatures = self.analyze_file(file_path, project_name)
            all_signatures.extend(signatures)

        self._signatures.extend(all_signatures)

        self.logger.info(
            "project_analyzed",
            project=project_name,
            total_signatures=len(all_signatures),
        )

        return all_signatures

    def analyze_multiple_projects(self, projects: Dict[str, Path]) -> List[CodeSignature]:
        """Analyze multiple projects.

        Args:
            projects: Dict of project_name -> project_path

        Returns:
            List of all signatures across projects
        """
        all_signatures: List[CodeSignature] = []

        for project_name, project_path in projects.items():
            signatures = self.analyze_project(project_path, project_name)
            all_signatures.extend(signatures)

        return all_signatures

    def get_signatures(self) -> List[CodeSignature]:
        """Get all collected signatures."""
        return self._signatures

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all imports from AST."""
        imports: List[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        return imports

    def _extract_function_signature(
        self,
        node: ast.FunctionDef,
        file_path: Path,
        project: str,
        imports: List[str],
        class_name: Optional[str] = None,
    ) -> CodeSignature:
        """Extract signature from a function/method."""

        # Get parameters
        params = []
        for arg in node.args.args:
            param_name = arg.arg
            if arg.annotation:
                param_name += f": {ast.unparse(arg.annotation)}"
            params.append(param_name)

        # Get return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        # Get docstring
        docstring = ast.get_docstring(node)

        # Get decorators
        decorators = [ast.unparse(d) for d in node.decorator_list]

        # Calculate body hash (normalized)
        body_source = ast.unparse(node)
        body_hash = hashlib.md5(body_source.encode()).hexdigest()

        # Estimate complexity
        complexity = self._estimate_complexity(node)

        # Determine signature type
        sig_type = "method" if class_name else "function"
        name = f"{class_name}.{node.name}" if class_name else node.name

        return CodeSignature(
            name=name,
            signature_type=sig_type,
            file_path=str(file_path),
            line_number=node.lineno,
            parameters=params,
            return_type=return_type,
            docstring=docstring,
            body_hash=body_hash,
            complexity=complexity,
            imports=imports,
            decorators=decorators,
            project=project,
        )

    def _extract_class_signature(
        self,
        node: ast.ClassDef,
        file_path: Path,
        project: str,
        imports: List[str],
    ) -> CodeSignature:
        """Extract signature from a class."""

        # Get base classes
        bases = [ast.unparse(base) for base in node.bases]

        # Get docstring
        docstring = ast.get_docstring(node)

        # Get decorators
        decorators = [ast.unparse(d) for d in node.decorator_list]

        # Calculate body hash
        body_source = ast.unparse(node)
        body_hash = hashlib.md5(body_source.encode()).hexdigest()

        # Count methods for complexity
        method_count = sum(
            1 for item in node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        )

        return CodeSignature(
            name=node.name,
            signature_type="class",
            file_path=str(file_path),
            line_number=node.lineno,
            parameters=bases,  # Store base classes as parameters
            return_type=None,
            docstring=docstring,
            body_hash=body_hash,
            complexity=method_count,
            imports=imports,
            decorators=decorators,
            project=project,
        )

    def _estimate_complexity(self, node: ast.FunctionDef) -> int:
        """Estimate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1

        return complexity
