"""Command-line interface for AI Orchestrator."""

import asyncio
import sys
from typing import Optional
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
import argparse

console = Console()


class OrchestratorCLI:
    """CLI for interacting with AI Orchestrator."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize CLI.

        Args:
            base_url: Base URL of orchestrator API
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)

    async def chat(
        self,
        message: str,
        provider: Optional[str] = None,
        enable_tools: bool = True,
        enable_collaboration: bool = True,
    ) -> None:
        """Send a chat request.

        Args:
            message: User message
            provider: Explicit provider (optional)
            enable_tools: Enable tool execution
            enable_collaboration: Enable multi-LLM collaboration
        """
        try:
            # Prepend provider prefix if specified
            if provider:
                message = f"@{provider}: {message}"

            console.print(f"\n[bold cyan]You:[/bold cyan] {message}\n")

            with console.status("[bold green]Thinking..."):
                response = await self.client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "message": message,
                        "enable_tools": enable_tools,
                        "enable_collaboration": enable_collaboration,
                    },
                )
                response.raise_for_status()
                data = response.json()

            # Display response
            console.print(f"[bold magenta]Provider:[/bold magenta] {data['provider']}")
            console.print(
                f"[bold yellow]Category:[/bold yellow] {data['routing_decision']['category']}"
            )
            console.print(
                f"[bold blue]Confidence:[/bold blue] {data['routing_decision']['confidence']:.0%}"
            )

            if data.get("fallback_events"):
                console.print(
                    f"[bold red]Fallbacks:[/bold red] {len(data['fallback_events'])}"
                )

            if data.get("collaboration_steps"):
                console.print(
                    f"[bold green]Collaboration Steps:[/bold green] {len(data['collaboration_steps'])}"
                )

            console.print(f"\n[bold cyan]Response:[/bold cyan]")
            console.print(Panel(Markdown(data["message"]), title="AI Response"))

            # Display tool executions
            if data.get("tool_results"):
                console.print("\n[bold yellow]Tools Executed:[/bold yellow]")
                for tool in data["tool_results"]:
                    status = "✓" if tool["success"] else "✗"
                    console.print(
                        f"  {status} {tool['tool_type']}: {tool['operation']} "
                        f"({tool['execution_time']:.2f}s)"
                    )

            console.print(f"\n[dim]Execution time: {data['execution_time']:.2f}s[/dim]\n")

        except httpx.HTTPError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    async def health(self) -> None:
        """Check orchestrator health."""
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            data = response.json()

            table = Table(title="Orchestrator Health")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="green")

            table.add_row("Overall", data["status"].upper())

            console.print("\n[bold]Providers:[/bold]")
            for provider, status in data["providers"].items():
                icon = "✓" if status else "✗"
                color = "green" if status else "red"
                console.print(f"  [{color}]{icon} {provider}[/{color}]")

            console.print("\n[bold]Tools:[/bold]")
            for tool, status in data["tools"].items():
                icon = "✓" if status else "✗"
                color = "green" if status else "red"
                console.print(f"  [{color}]{icon} {tool}[/{color}]")

            console.print()

        except httpx.HTTPError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    async def list_providers(self) -> None:
        """List available providers."""
        try:
            response = await self.client.get(f"{self.base_url}/api/providers")
            response.raise_for_status()
            data = response.json()

            table = Table(title="Available Providers")
            table.add_column("Provider", style="cyan")
            table.add_column("Configured", style="green")
            table.add_column("Role", style="yellow")

            for name, info in data["providers"].items():
                status = "✓" if info["configured"] else "✗"
                table.add_row(name, status, info["role"])

            console.print("\n")
            console.print(table)
            console.print()

        except httpx.HTTPError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    async def interactive(self) -> None:
        """Start interactive mode."""
        console.print(
            Panel(
                "[bold cyan]AI Orchestrator - Interactive Mode[/bold cyan]\n"
                "Commands:\n"
                "  /help - Show help\n"
                "  /health - Check health\n"
                "  /providers - List providers\n"
                "  /quit - Exit\n\n"
                "Use @provider: prefix to select specific provider:\n"
                "  @claude-code: build api\n"
                "  @chatgpt: create dashboard\n"
                "  @gemini: optimize prompt\n"
                "  @local: analyze incident\n",
                title="Welcome",
            )
        )

        while True:
            try:
                message = console.input("\n[bold green]You>[/bold green] ")

                if not message.strip():
                    continue

                if message == "/quit":
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                elif message == "/help":
                    console.print(
                        Panel(
                            "Available Commands:\n"
                            "  /help - Show this help\n"
                            "  /health - Check orchestrator health\n"
                            "  /providers - List available providers\n"
                            "  /quit - Exit interactive mode\n\n"
                            "Provider Selection:\n"
                            "  @claude-code: - Code generation & DevOps\n"
                            "  @chatgpt: - UI/UX & workflows\n"
                            "  @gemini: - Prompt optimization\n"
                            "  @claude: - Analysis & reasoning\n"
                            "  @local: - Privacy-focused analysis\n",
                            title="Help",
                        )
                    )
                elif message == "/health":
                    await self.health()
                elif message == "/providers":
                    await self.list_providers()
                else:
                    await self.chat(message)

            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    async def close(self) -> None:
        """Close the client."""
        await self.client.aclose()


async def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="AI Orchestrator CLI")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Orchestrator API URL"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Send a chat message")
    chat_parser.add_argument("message", nargs="+", help="Message to send")
    chat_parser.add_argument("--provider", help="Explicit provider selection")
    chat_parser.add_argument(
        "--no-tools", action="store_true", help="Disable tool execution"
    )
    chat_parser.add_argument(
        "--no-collaboration", action="store_true", help="Disable collaboration"
    )

    # Health command
    subparsers.add_parser("health", help="Check orchestrator health")

    # Providers command
    subparsers.add_parser("providers", help="List available providers")

    # Interactive command
    subparsers.add_parser("interactive", help="Start interactive mode")

    args = parser.parse_args()

    cli = OrchestratorCLI(base_url=args.url)

    try:
        if args.command == "chat":
            message = " ".join(args.message)
            await cli.chat(
                message,
                provider=args.provider,
                enable_tools=not args.no_tools,
                enable_collaboration=not args.no_collaboration,
            )
        elif args.command == "health":
            await cli.health()
        elif args.command == "providers":
            await cli.list_providers()
        elif args.command == "interactive" or args.command is None:
            await cli.interactive()
        else:
            parser.print_help()
    finally:
        await cli.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(0)
