"""Multi-agent orchestration and collaboration patterns.

This module implements advanced collaboration patterns for coordinating
multiple LLM agents to solve complex tasks:

- Sequential: Agent A → Agent B → Agent C (each builds on previous)
- Parallel: Multiple agents work simultaneously, results merged
- Hierarchical: Master agent delegates to specialized sub-agents

Example:
    Sequential pattern for full-stack development:
    1. Gemini optimizes requirements
    2. ChatGPT designs UI/UX
    3. Claude Code implements backend + frontend

    Parallel pattern for incident analysis:
    1. Local LLM analyzes logs (privacy-safe)
    2. Gemini summarizes metrics
    3. Results merged into comprehensive report
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from src.models.schemas import (
    LLMProvider,
    TaskCategory,
    Message,
    LLMResponse,
    RoutingDecision,
)
from src.core.context_manager import get_context_manager
import structlog

logger = structlog.get_logger()


class CollaborationPattern(str, Enum):
    """Type of multi-agent collaboration pattern."""

    SEQUENTIAL = "sequential"  # Agent A → Agent B → Agent C (chain)
    PARALLEL = "parallel"  # Multiple agents simultaneously
    HIERARCHICAL = "hierarchical"  # Master delegates to sub-agents
    DEBATE = "debate"  # Agents discuss and reach consensus
    SPECIALIZED = "specialized"  # Each agent handles specific aspect
    PIPELINE = "pipeline"  # Processing stages with transformation


@dataclass
class AgentTask:
    """Task for a single agent in collaboration."""

    agent: LLMProvider
    instruction: str
    context: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)  # Task IDs this depends on
    task_id: str = ""
    result: Optional[LLMResponse] = None
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class CollaborationPlan:
    """Plan for multi-agent collaboration."""

    pattern: CollaborationPattern
    tasks: List[AgentTask]
    original_request: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Auto-generate task IDs."""
        for i, task in enumerate(self.tasks):
            if not task.task_id:
                task.task_id = f"task_{i+1}"


@dataclass
class AgentHandoff:
    """Context shared during agent handoff."""

    from_agent: LLMProvider
    to_agent: LLMProvider
    shared_context: Dict[str, Any]
    handoff_message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_message(self) -> str:
        """Convert handoff to message for next agent."""
        return (
            f"[Handoff from {self.from_agent.value}]\n"
            f"{self.handoff_message}\n\n"
            f"Context: {self._format_context()}"
        )

    def _format_context(self) -> str:
        """Format shared context as readable text."""
        lines = []
        for key, value in self.shared_context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)


class CollaborationManager:
    """Manages multi-agent collaboration workflows."""

    # Pre-defined collaboration templates
    TEMPLATES = {
        "full_stack_development": {
            "pattern": CollaborationPattern.SEQUENTIAL,
            "description": "Build complete application with UI and backend",
            "tasks": [
                {
                    "agent": LLMProvider.GEMINI,
                    "instruction": "Analyze requirements and create optimized technical specifications",
                    "task_id": "requirements"
                },
                {
                    "agent": LLMProvider.CHATGPT,
                    "instruction": "Design UI/UX based on specifications",
                    "task_id": "ui_design",
                    "depends_on": ["requirements"]
                },
                {
                    "agent": LLMProvider.CLAUDE_CODE,
                    "instruction": "Implement backend and frontend code",
                    "task_id": "implementation",
                    "depends_on": ["requirements", "ui_design"]
                }
            ]
        },
        "incident_analysis_report": {
            "pattern": CollaborationPattern.PARALLEL,
            "description": "Comprehensive incident analysis with report",
            "tasks": [
                {
                    "agent": LLMProvider.LOCAL,
                    "instruction": "Analyze logs for root cause (privacy-safe)",
                    "task_id": "log_analysis"
                },
                {
                    "agent": LLMProvider.GEMINI,
                    "instruction": "Summarize metrics and trends",
                    "task_id": "metrics_summary"
                },
                {
                    "agent": LLMProvider.CHATGPT,
                    "instruction": "Create formatted incident report",
                    "task_id": "report_generation",
                    "depends_on": ["log_analysis", "metrics_summary"]
                }
            ]
        },
        "code_review_pipeline": {
            "pattern": CollaborationPattern.PIPELINE,
            "description": "Multi-stage code review with improvements",
            "tasks": [
                {
                    "agent": LLMProvider.CLAUDE_CODE,
                    "instruction": "Analyze code for bugs and issues",
                    "task_id": "bug_detection"
                },
                {
                    "agent": LLMProvider.LOCAL,
                    "instruction": "Check security vulnerabilities",
                    "task_id": "security_check",
                    "depends_on": ["bug_detection"]
                },
                {
                    "agent": LLMProvider.GEMINI,
                    "instruction": "Suggest optimizations and improvements",
                    "task_id": "optimization",
                    "depends_on": ["bug_detection", "security_check"]
                }
            ]
        },
        "documentation_generation": {
            "pattern": CollaborationPattern.SPECIALIZED,
            "description": "Generate comprehensive documentation",
            "tasks": [
                {
                    "agent": LLMProvider.CLAUDE_CODE,
                    "instruction": "Generate API documentation and code comments",
                    "task_id": "api_docs"
                },
                {
                    "agent": LLMProvider.CHATGPT,
                    "instruction": "Create user guides and tutorials",
                    "task_id": "user_guides"
                },
                {
                    "agent": LLMProvider.GEMINI,
                    "instruction": "Write architecture documentation",
                    "task_id": "architecture_docs"
                }
            ]
        },
        "debate_consensus": {
            "pattern": CollaborationPattern.DEBATE,
            "description": "Multiple agents debate approach and reach consensus",
            "tasks": [
                {
                    "agent": LLMProvider.CLAUDE_CODE,
                    "instruction": "Propose technical approach A",
                    "task_id": "proposal_a"
                },
                {
                    "agent": LLMProvider.CHATGPT,
                    "instruction": "Propose alternative approach B",
                    "task_id": "proposal_b"
                },
                {
                    "agent": LLMProvider.GEMINI,
                    "instruction": "Evaluate both approaches and recommend best option",
                    "task_id": "consensus",
                    "depends_on": ["proposal_a", "proposal_b"]
                }
            ]
        }
    }

    def __init__(self):
        """Initialize collaboration manager."""
        self.logger = logger.bind(component="collaboration_manager")
        self.context_manager = get_context_manager()

    async def execute_plan(
        self,
        plan: CollaborationPlan,
        provider_map: Dict[LLMProvider, Any]
    ) -> Dict[str, Any]:
        """Execute a collaboration plan.

        Args:
            plan: Collaboration plan to execute
            provider_map: Map of LLMProvider -> provider instance

        Returns:
            Dict with results from all tasks
        """
        plan.started_at = datetime.utcnow()

        self.logger.info(
            "collaboration_started",
            pattern=plan.pattern.value,
            task_count=len(plan.tasks)
        )

        # Execute based on pattern
        if plan.pattern == CollaborationPattern.SEQUENTIAL:
            results = await self._execute_sequential(plan, provider_map)
        elif plan.pattern == CollaborationPattern.PARALLEL:
            results = await self._execute_parallel(plan, provider_map)
        elif plan.pattern == CollaborationPattern.HIERARCHICAL:
            results = await self._execute_hierarchical(plan, provider_map)
        elif plan.pattern == CollaborationPattern.PIPELINE:
            results = await self._execute_pipeline(plan, provider_map)
        elif plan.pattern == CollaborationPattern.SPECIALIZED:
            results = await self._execute_specialized(plan, provider_map)
        elif plan.pattern == CollaborationPattern.DEBATE:
            results = await self._execute_debate(plan, provider_map)
        else:
            raise ValueError(f"Unsupported pattern: {plan.pattern}")

        plan.completed_at = datetime.utcnow()
        duration = (plan.completed_at - plan.started_at).total_seconds()

        self.logger.info(
            "collaboration_completed",
            pattern=plan.pattern.value,
            duration_seconds=f"{duration:.2f}",
            success_count=sum(1 for t in plan.tasks if t.status == "completed"),
            failure_count=sum(1 for t in plan.tasks if t.status == "failed")
        )

        return results

    async def _execute_sequential(
        self,
        plan: CollaborationPlan,
        provider_map: Dict[LLMProvider, Any]
    ) -> Dict[str, Any]:
        """Execute tasks sequentially with context passing.

        Each agent receives the output from previous agents.

        Args:
            plan: Collaboration plan
            provider_map: Provider instances

        Returns:
            Dict mapping task_id -> result
        """
        results = {}
        shared_context = {"original_request": plan.original_request}

        for task in plan.tasks:
            self.logger.info(
                "sequential_task_started",
                task_id=task.task_id,
                agent=task.agent.value
            )

            task.status = "running"
            task.started_at = datetime.utcnow()

            # Build message with context from previous tasks
            message_content = self._build_sequential_message(
                task, results, shared_context
            )

            # Execute task
            try:
                provider = provider_map.get(task.agent)
                if not provider:
                    raise ValueError(f"Provider {task.agent.value} not available")

                messages = [Message(role="user", content=message_content)]
                response = await provider.complete(messages)

                task.result = response
                task.status = "completed"
                task.completed_at = datetime.utcnow()

                # Store result and update context
                results[task.task_id] = response.content
                shared_context[task.task_id] = response.content

                # Create handoff for next agent
                if plan.tasks.index(task) < len(plan.tasks) - 1:
                    next_task = plan.tasks[plan.tasks.index(task) + 1]
                    handoff = AgentHandoff(
                        from_agent=task.agent,
                        to_agent=next_task.agent,
                        shared_context={task.task_id: response.content},
                        handoff_message=f"Completed {task.task_id}: {response.content[:200]}..."
                    )
                    self.logger.info(
                        "agent_handoff",
                        from_agent=handoff.from_agent.value,
                        to_agent=handoff.to_agent.value
                    )

                latency = (task.completed_at - task.started_at).total_seconds()
                self.logger.info(
                    "sequential_task_completed",
                    task_id=task.task_id,
                    agent=task.agent.value,
                    latency_seconds=f"{latency:.2f}"
                )

            except Exception as e:
                task.status = "failed"
                task.completed_at = datetime.utcnow()
                self.logger.error(
                    "sequential_task_failed",
                    task_id=task.task_id,
                    agent=task.agent.value,
                    error=str(e)
                )
                results[task.task_id] = f"ERROR: {str(e)}"

        return results

    async def _execute_parallel(
        self,
        plan: CollaborationPlan,
        provider_map: Dict[LLMProvider, Any]
    ) -> Dict[str, Any]:
        """Execute independent tasks in parallel, then merge results.

        Args:
            plan: Collaboration plan
            provider_map: Provider instances

        Returns:
            Dict mapping task_id -> result
        """
        # Separate independent tasks from dependent tasks
        independent_tasks = [t for t in plan.tasks if not t.depends_on]
        dependent_tasks = [t for t in plan.tasks if t.depends_on]

        results = {}

        # Execute independent tasks in parallel
        if independent_tasks:
            self.logger.info(
                "parallel_execution_started",
                parallel_count=len(independent_tasks)
            )

            async def execute_task(task: AgentTask) -> Tuple[str, Any]:
                """Execute single task."""
                task.status = "running"
                task.started_at = datetime.utcnow()

                try:
                    provider = provider_map.get(task.agent)
                    if not provider:
                        raise ValueError(f"Provider {task.agent.value} not available")

                    message_content = f"{task.instruction}\n\nOriginal request: {plan.original_request}"
                    if task.context:
                        message_content += f"\n\nContext: {task.context}"

                    messages = [Message(role="user", content=message_content)]
                    response = await provider.complete(messages)

                    task.result = response
                    task.status = "completed"
                    task.completed_at = datetime.utcnow()

                    return task.task_id, response.content

                except Exception as e:
                    task.status = "failed"
                    task.completed_at = datetime.utcnow()
                    self.logger.error(
                        "parallel_task_failed",
                        task_id=task.task_id,
                        error=str(e)
                    )
                    return task.task_id, f"ERROR: {str(e)}"

            # Run all independent tasks concurrently
            parallel_results = await asyncio.gather(
                *[execute_task(task) for task in independent_tasks],
                return_exceptions=True
            )

            # Collect results
            for task_id, result in parallel_results:
                if not isinstance(result, Exception):
                    results[task_id] = result

        # Execute dependent tasks sequentially (they need results from parallel tasks)
        for task in dependent_tasks:
            task.status = "running"
            task.started_at = datetime.utcnow()

            # Build message with dependencies
            message_content = f"{task.instruction}\n\nOriginal request: {plan.original_request}\n\n"
            message_content += "Results from dependent tasks:\n"
            for dep_id in task.depends_on:
                if dep_id in results:
                    message_content += f"\n{dep_id}:\n{results[dep_id]}\n"

            try:
                provider = provider_map.get(task.agent)
                if not provider:
                    raise ValueError(f"Provider {task.agent.value} not available")

                messages = [Message(role="user", content=message_content)]
                response = await provider.complete(messages)

                task.result = response
                task.status = "completed"
                task.completed_at = datetime.utcnow()
                results[task.task_id] = response.content

            except Exception as e:
                task.status = "failed"
                task.completed_at = datetime.utcnow()
                results[task.task_id] = f"ERROR: {str(e)}"

        return results

    async def _execute_pipeline(
        self,
        plan: CollaborationPlan,
        provider_map: Dict[LLMProvider, Any]
    ) -> Dict[str, Any]:
        """Execute tasks as a pipeline (similar to sequential but with transformations).

        Args:
            plan: Collaboration plan
            provider_map: Provider instances

        Returns:
            Dict mapping task_id -> result
        """
        # Pipeline is similar to sequential but emphasizes data transformation
        return await self._execute_sequential(plan, provider_map)

    async def _execute_hierarchical(
        self,
        plan: CollaborationPlan,
        provider_map: Dict[LLMProvider, Any]
    ) -> Dict[str, Any]:
        """Execute hierarchical pattern: master delegates to sub-agents.

        Args:
            plan: Collaboration plan
            provider_map: Provider instances

        Returns:
            Dict mapping task_id -> result
        """
        # First task is master, rest are sub-agents
        if not plan.tasks:
            return {}

        master_task = plan.tasks[0]
        sub_tasks = plan.tasks[1:]

        results = {}

        # Master agent creates delegation plan
        master_task.status = "running"
        master_task.started_at = datetime.utcnow()

        try:
            provider = provider_map.get(master_task.agent)
            if not provider:
                raise ValueError(f"Provider {master_task.agent.value} not available")

            master_message = (
                f"{master_task.instruction}\n\n"
                f"Original request: {plan.original_request}\n\n"
                f"You are the master agent. Delegate tasks to sub-agents:\n"
            )
            for task in sub_tasks:
                master_message += f"- {task.agent.value}: {task.instruction}\n"

            messages = [Message(role="user", content=master_message)]
            master_response = await provider.complete(messages)

            master_task.result = master_response
            master_task.status = "completed"
            master_task.completed_at = datetime.utcnow()
            results[master_task.task_id] = master_response.content

        except Exception as e:
            master_task.status = "failed"
            results[master_task.task_id] = f"ERROR: {str(e)}"

        # Execute sub-tasks in parallel
        sub_plan = CollaborationPlan(
            pattern=CollaborationPattern.PARALLEL,
            tasks=sub_tasks,
            original_request=plan.original_request,
            metadata={"master_result": results.get(master_task.task_id, "")}
        )

        sub_results = await self._execute_parallel(sub_plan, provider_map)
        results.update(sub_results)

        return results

    async def _execute_specialized(
        self,
        plan: CollaborationPlan,
        provider_map: Dict[LLMProvider, Any]
    ) -> Dict[str, Any]:
        """Execute specialized pattern: each agent handles specific aspect.

        Args:
            plan: Collaboration plan
            provider_map: Provider instances

        Returns:
            Dict mapping task_id -> result
        """
        # All tasks are independent and specialized
        return await self._execute_parallel(plan, provider_map)

    async def _execute_debate(
        self,
        plan: CollaborationPlan,
        provider_map: Dict[LLMProvider, Any]
    ) -> Dict[str, Any]:
        """Execute debate pattern: agents discuss and reach consensus.

        Args:
            plan: Collaboration plan
            provider_map: Provider instances

        Returns:
            Dict mapping task_id -> result
        """
        results = {}

        # First, get proposals from all agents except the last (consensus agent)
        proposal_tasks = plan.tasks[:-1]
        consensus_task = plan.tasks[-1]

        # Execute proposals in parallel
        proposal_plan = CollaborationPlan(
            pattern=CollaborationPattern.PARALLEL,
            tasks=proposal_tasks,
            original_request=plan.original_request
        )

        proposal_results = await self._execute_parallel(proposal_plan, provider_map)
        results.update(proposal_results)

        # Consensus agent evaluates all proposals
        consensus_task.status = "running"
        consensus_task.started_at = datetime.utcnow()

        try:
            provider = provider_map.get(consensus_task.agent)
            if not provider:
                raise ValueError(f"Provider {consensus_task.agent.value} not available")

            consensus_message = (
                f"{consensus_task.instruction}\n\n"
                f"Original request: {plan.original_request}\n\n"
                f"Proposals to evaluate:\n\n"
            )

            for task in proposal_tasks:
                if task.task_id in results:
                    consensus_message += f"{task.agent.value} proposal:\n{results[task.task_id]}\n\n"

            messages = [Message(role="user", content=consensus_message)]
            consensus_response = await provider.complete(messages)

            consensus_task.result = consensus_response
            consensus_task.status = "completed"
            consensus_task.completed_at = datetime.utcnow()
            results[consensus_task.task_id] = consensus_response.content

        except Exception as e:
            consensus_task.status = "failed"
            results[consensus_task.task_id] = f"ERROR: {str(e)}"

        return results

    def _build_sequential_message(
        self,
        task: AgentTask,
        previous_results: Dict[str, Any],
        shared_context: Dict[str, Any]
    ) -> str:
        """Build message for sequential task with context.

        Args:
            task: Current task
            previous_results: Results from previous tasks
            shared_context: Shared context across all tasks

        Returns:
            Message content with context
        """
        message = f"{task.instruction}\n\n"

        if task.depends_on:
            message += "Results from previous agents:\n\n"
            for dep_id in task.depends_on:
                if dep_id in previous_results:
                    message += f"{dep_id}:\n{previous_results[dep_id]}\n\n"

        if shared_context:
            message += f"\nOriginal request: {shared_context.get('original_request', '')}\n"

        if task.context:
            message += f"\nAdditional context: {task.context}\n"

        return message

    def create_plan_from_template(
        self,
        template_name: str,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CollaborationPlan:
        """Create collaboration plan from predefined template.

        Args:
            template_name: Name of template (e.g., "full_stack_development")
            request: Original user request
            context: Additional context to pass to tasks

        Returns:
            CollaborationPlan

        Raises:
            ValueError: If template not found
        """
        if template_name not in self.TEMPLATES:
            raise ValueError(
                f"Unknown template: {template_name}. "
                f"Available: {list(self.TEMPLATES.keys())}"
            )

        template = self.TEMPLATES[template_name]

        # Create tasks from template
        tasks = []
        for task_spec in template["tasks"]:
            task = AgentTask(
                agent=task_spec["agent"],
                instruction=task_spec["instruction"],
                task_id=task_spec["task_id"],
                depends_on=task_spec.get("depends_on", []),
                context=context or {}
            )
            tasks.append(task)

        plan = CollaborationPlan(
            pattern=template["pattern"],
            tasks=tasks,
            original_request=request,
            metadata={
                "template": template_name,
                "description": template["description"]
            }
        )

        self.logger.info(
            "plan_created_from_template",
            template=template_name,
            pattern=template["pattern"].value,
            task_count=len(tasks)
        )

        return plan

    def estimate_handoff_latency(self, plan: CollaborationPlan) -> float:
        """Estimate total handoff latency for a plan.

        Handoff latency is the overhead of passing context between agents.
        Target: <2 seconds per handoff

        Args:
            plan: Collaboration plan

        Returns:
            Estimated latency in seconds
        """
        if plan.pattern == CollaborationPattern.SEQUENTIAL:
            # Sequential has (n-1) handoffs
            handoff_count = len(plan.tasks) - 1
            return handoff_count * 1.5  # 1.5s per handoff

        elif plan.pattern == CollaborationPattern.PARALLEL:
            # Parallel has fewer handoffs (only for merge)
            dependent_tasks = [t for t in plan.tasks if t.depends_on]
            return len(dependent_tasks) * 1.5

        elif plan.pattern == CollaborationPattern.HIERARCHICAL:
            # Master → sub-agents → back to master
            return (len(plan.tasks) - 1) * 1.5

        else:
            # Conservative estimate
            return len(plan.tasks) * 1.0


# Global instance
_collaboration_manager: Optional[CollaborationManager] = None


def get_collaboration_manager() -> CollaborationManager:
    """Get global collaboration manager instance (singleton)."""
    global _collaboration_manager
    if _collaboration_manager is None:
        _collaboration_manager = CollaborationManager()
    return _collaboration_manager
