"""
Main entry point for the AI Research Agent.

This module provides the CLI interface for running the research pipeline.
Uses Rich for beautiful progress bars and console output.

Usage:
    python -m agent.main research --provider mock
    python -m agent.main resume
    python -m agent.main status
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import argparse
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.panel import Panel

from .config import settings
from .logger import get_logger, setup_logger
from .research_agent import ResearchAgent, create_research_agent
from .models import AppResearch

# Initialize console and logger
console = Console()
logger = get_logger(__name__)


def run_research(
    provider: str = "mock",
    apps_file: Optional[Path] = None,
    force: bool = False,
    max_retries: int = 3,
    limit: Optional[int] = None,
) -> None:
    """
    Run the research pipeline.
    
    Args:
        provider: LLM provider type
        apps_file: Path to apps.json
        force: Force reprocessing
        max_retries: Maximum retries per app
        limit: Limit number of apps to process
    """
    apps_file = apps_file or Path(__file__).parent / "apps.json"
    
    console.print(Panel.fit(
        "[bold cyan]Composio AI Research Agent[/bold cyan]\n"
        "[dim]Researching SaaS applications for AI agent buildability[/dim]",
        border_style="cyan"
    ))
    
    # Create research agent
    agent = create_research_agent(
        provider_type=provider,
        output_dir=settings.OUTPUT_DIR,
        max_retries=max_retries,
    )
    
    try:
        # Load apps
        apps = agent.load_apps(apps_file)
        console.print(f"[green][+][/green] Loaded [bold]{len(apps)}[/bold] apps")
        
        # Apply limit if specified
        if limit:
            apps = apps[:limit]
            console.print(f"[yellow][!][/yellow] Limited to [bold]{limit}[/bold] apps")
        
        # Process with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Researching apps...[/cyan]",
                total=len(apps)
            )
            
            # Process each app
            summary = {
                "total": len(apps),
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "results": [],
                "errors": [],
            }
            
            for i, app in enumerate(apps, 1):
                app_name = app.get("name", f"App {i}")
                
                # Update progress
                progress.update(
                    task,
                    description=f"[cyan]Processing {app_name}[/cyan]"
                )
                
                # Check if already processed
                if not force and agent.storage.is_processed(app_name):
                    progress.console.print(
                        f"[dim]  ↳ {app_name} already done, skipping[/dim]"
                    )
                    summary["skipped"] += 1
                    progress.advance(task)
                    continue
                
                # Process app
                success, result, error = agent.process_app(app, force=force)
                
                if success:
                    summary["processed"] += 1
                    if result:
                        summary["results"].append(result)
                        progress.console.print(
                            f"[green]  ↳ {app_name}[/green] "
                            f"Confidence: [bold]{result.confidence_score:.0%}[/bold]"
                        )
                else:
                    summary["failed"] += 1
                    summary["errors"].append({"app": app_name, "error": error})
                    progress.console.print(
                        f"[red]  ↳ {app_name} failed: {error}[/red]"
                    )
                
                progress.advance(task)
        
        # Show summary
        _show_summary(summary)
        
    except KeyboardInterrupt:
        console.print("\n[yellow][!][/yellow] Interrupted by user. Progress saved.")
        console.print("[dim]Run 'python -m agent.main resume' to continue.[/dim]")
    except Exception as e:
        logger.error(f"Research failed: {e}")
        console.print(f"[red][x][/red] Research failed: {e}")
        sys.exit(1)
    finally:
        agent.close()


def run_resume() -> None:
    """Resume interrupted research run."""
    console.print(Panel.fit(
        "[bold cyan]Resuming Research[/bold cyan]",
        border_style="cyan"
    ))
    
    agent = create_research_agent(output_dir=settings.OUTPUT_DIR)
    
    try:
        # Load apps
        apps_file = Path(__file__).parent / "apps.json"
        agent.load_apps(apps_file)
        
        # Get pending apps
        pending = agent.get_pending_apps()
        
        if not pending:
            console.print("[green]✓[/green] No pending apps to process")
            return
        
        console.print(
            f"[yellow]⚠[/yellow] {len(pending)} apps pending"
        )
        
        # Process with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Resuming...[/cyan]",
                total=len(pending)
            )
            
            summary = agent.resume()
            
            # Update progress based on summary
            processed = summary.get("processed", 0)
            for _ in range(processed):
                progress.advance(task)
        
        _show_summary(summary)
        
    except Exception as e:
        logger.error(f"Resume failed: {e}")
        console.print(f"[red]✗[/red] Resume failed: {e}")
        sys.exit(1)
    finally:
        agent.close()


def show_status() -> None:
    """Show current research status."""
    console.print(Panel.fit(
        "[bold cyan]Research Status[/bold cyan]",
        border_style="cyan"
    ))
    
    agent = create_research_agent(output_dir=settings.OUTPUT_DIR)
    
    try:
        # Load apps
        apps_file = Path(__file__).parent / "apps.json"
        apps = agent.load_apps(apps_file)
        
        # Get statistics
        stats = agent.get_statistics()
        progress = stats.get("progress", {})
        
        # Create status table
        table = Table(title="Research Progress")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Apps", str(len(apps)))
        table.add_row("Processed", str(progress.get("total_processed", 0)))
        table.add_row("Successful", str(progress.get("successful", 0)))
        table.add_row("Failed", str(progress.get("failed", 0)))
        table.add_row("Success Rate", f"{progress.get('success_rate', 0):.1f}%")
        table.add_row("Saved Results", str(stats.get("total_saved", 0)))
        table.add_row("Avg Confidence", f"{stats.get('average_confidence', 0):.0%}")
        
        console.print(table)
        
        # Show category breakdown if available
        categories = stats.get("categories", {})
        if categories:
            cat_table = Table(title="Categories")
            cat_table.add_column("Category", style="cyan")
            cat_table.add_column("Count", style="green")
            
            for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                cat_table.add_row(cat, str(count))
            
            console.print(cat_table)
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        console.print(f"[red]✗[/red] Status check failed: {e}")
        sys.exit(1)
    finally:
        agent.close()


def _show_summary(summary: Dict[str, Any]) -> None:
    """
    Show research summary.
    
    Args:
        summary: Summary dictionary
    """
    console.print("\n" + "=" * 60)
    console.print(Panel.fit(
        f"[bold green]Research Complete[/bold green]\n"
        f"Processed: [bold]{summary['processed']}[/bold] | "
        f"Failed: [bold red]{summary['failed']}[/bold red] | "
        f"Skipped: [bold yellow]{summary['skipped']}[/bold yellow]",
        border_style="green"
    ))
    
    if summary["errors"]:
        console.print("\n[red]Errors:[/red]")
        for error in summary["errors"][:10]:  # Show first 10 errors
            console.print(f"  [red]✗[/red] {error['app']}: {error['error']}")
        
        if len(summary["errors"]) > 10:
            console.print(f"  [dim]... and {len(summary['errors']) - 10} more[/dim]")
    
    console.print(
        "\n[dim]Run 'python -m agent.main status' for detailed statistics[/dim]"
    )


def main() -> None:
    """
    Main CLI entry point.
    """
    parser = argparse.ArgumentParser(
        description="Composio AI Research Agent - Research SaaS applications"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Research command
    research_parser = subparsers.add_parser(
        "research",
        help="Run research pipeline"
    )
    research_parser.add_argument(
        "--provider",
        "-p",
        default="mock",
        choices=["mock", "openai", "anthropic", "groq"],
        help="LLM provider to use"
    )
    research_parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="Path to apps.json"
    )
    research_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force reprocessing of all apps"
    )
    research_parser.add_argument(
        "--retries",
        "-r",
        type=int,
        default=3,
        help="Maximum retries per app"
    )
    research_parser.add_argument(
        "--limit",
        "-l",
        type=int,
        help="Limit number of apps to process"
    )
    
    # Resume command
    subparsers.add_parser(
        "resume",
        help="Resume interrupted research"
    )
    
    # Status command
    subparsers.add_parser(
        "status",
        help="Show research status"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "research":
        run_research(
            provider=args.provider,
            apps_file=args.input,
            force=args.force,
            max_retries=args.retries,
            limit=args.limit,
        )
    elif args.command == "resume":
        run_resume()
    elif args.command == "status":
        show_status()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()