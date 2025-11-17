"""Command-line interface for AIBooks."""

import sys
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

from .db.database import init_database, get_db
from .core.processor import DocumentProcessor
from .core.config import get_config


app = typer.Typer(
    name="aibooks",
    help="LLM-ready document and ebook ingestion system with deep agentic self-learning",
)
console = Console()


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    logger.remove()  # Remove default handler

    log_level = "DEBUG" if verbose else "INFO"

    # Console logging
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # File logging
    config = get_config()
    if config.logging.enable_file_log:
        config.paths.log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            config.logging.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="10 MB",
            retention="30 days",
        )


@app.command()
def init(
    database_path: Optional[str] = typer.Option(None, help="Database path"),
    reset: bool = typer.Option(False, help="Reset existing database"),
):
    """Initialize the AIBooks database."""
    setup_logging()

    console.print("[bold blue]Initializing AIBooks database...[/bold blue]")

    try:
        db = init_database(database_path, reset=reset)

        if reset:
            console.print("[yellow]Database reset complete[/yellow]")
        else:
            console.print("[green]Database initialized successfully[/green]")

        console.print(f"Database location: {db.database_path}")

    except Exception as e:
        console.print(f"[red]Error initializing database: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ingest(
    files: List[Path] = typer.Argument(..., help="Files or directories to ingest"),
    skip_duplicates: bool = typer.Option(True, help="Skip duplicate documents"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Ingest documents into AIBooks."""
    setup_logging(verbose)

    console.print("[bold blue]Starting document ingestion...[/bold blue]")

    # Collect all files
    all_files = []
    for file_path in files:
        file_path = Path(file_path)
        if file_path.is_dir():
            # Recursively find supported files
            patterns = ["*.pdf", "*.epub", "*.mobi", "*.azw3", "*.docx", "*.txt"]
            for pattern in patterns:
                all_files.extend(file_path.rglob(pattern))
        elif file_path.is_file():
            all_files.append(file_path)

    if not all_files:
        console.print("[yellow]No files found to process[/yellow]")
        return

    console.print(f"Found {len(all_files)} files to process")

    # Initialize processor
    processor = DocumentProcessor()

    # Process files with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing documents...", total=len(all_files))

        results = []
        for file_path in all_files:
            progress.update(task, description=f"Processing: {file_path.name}")

            doc = processor.process_document(file_path, skip_if_duplicate=skip_duplicates)
            results.append(doc)

            progress.advance(task)

    # Summary
    successful = sum(1 for r in results if r is not None)
    failed = len(results) - successful

    console.print(f"\n[bold green]Ingestion complete![/bold green]")
    console.print(f"  Successful: {successful}")
    console.print(f"  Failed/Skipped: {failed}")

    # Cost summary
    cost_summary = processor.get_daily_cost_summary()
    console.print(f"\n[bold]Daily Cost:[/bold] ${cost_summary['daily_spend']:.2f}")


@app.command()
def stats(
    days: int = typer.Option(7, help="Number of days to analyze"),
):
    """Show pipeline statistics and performance."""
    setup_logging()

    console.print("[bold blue]Pipeline Statistics[/bold blue]\n")

    db = get_db()
    with db.session_scope() as session:
        from .db.models import Document, GenAIUsageLog
        from sqlalchemy import func
        from datetime import datetime, timedelta

        # Document stats
        total_docs = session.query(Document).count()
        recent_docs = (
            session.query(Document)
            .filter(Document.created_at >= datetime.utcnow() - timedelta(days=days))
            .count()
        )

        # Cost stats
        total_cost = (
            session.query(func.sum(GenAIUsageLog.cost))
            .filter(GenAIUsageLog.timestamp >= datetime.utcnow() - timedelta(days=days))
            .scalar()
            or 0.0
        )

        # Format distribution
        format_dist = (
            session.query(Document.format, func.count(Document.id))
            .group_by(Document.format)
            .all()
        )

    # Display stats
    console.print(f"[bold]Total Documents:[/bold] {total_docs}")
    console.print(f"[bold]Recent Documents (last {days} days):[/bold] {recent_docs}")
    console.print(f"[bold]Total Cost (last {days} days):[/bold] ${total_cost:.2f}\n")

    # Format distribution table
    if format_dist:
        table = Table(title="Format Distribution")
        table.add_column("Format", style="cyan")
        table.add_column("Count", style="magenta", justify="right")

        for fmt, count in format_dist:
            table.add_row(fmt, str(count))

        console.print(table)


@app.command()
def evolve(
    days: int = typer.Option(7, help="Number of days to analyze"),
    auto_apply: bool = typer.Option(False, help="Auto-apply safe improvements"),
):
    """Analyze pipeline and suggest improvements."""
    setup_logging()

    console.print("[bold blue]Analyzing pipeline performance...[/bold blue]\n")

    processor = DocumentProcessor()
    analysis = processor.analyze_pipeline_performance(days=days)

    # Display analysis
    console.print(f"[bold]Analysis Period:[/bold] {days} days")
    console.print(
        f"[bold]Documents Processed:[/bold] {analysis['analysis']['total_documents']}"
    )
    console.print(
        f"[bold]Success Rate:[/bold] {analysis['analysis']['success_rate']:.1%}"
    )
    console.print(f"[bold]Total Cost:[/bold] ${analysis['analysis']['total_cost']:.2f}\n")

    # Suggestions
    suggestions = analysis["suggestions"]

    if not suggestions:
        console.print("[green]No improvements needed - pipeline performing well![/green]")
        return

    console.print(f"[bold yellow]Found {len(suggestions)} improvement suggestions:[/bold yellow]\n")

    for idx, suggestion in enumerate(suggestions, 1):
        priority = suggestion.get("priority", "medium")
        priority_color = {
            "high": "red",
            "medium": "yellow",
            "low": "green",
        }.get(priority, "white")

        console.print(f"{idx}. [{priority_color}]{suggestion['suggestion']}[/{priority_color}]")

    if auto_apply and analysis["auto_apply_safe"]:
        console.print("\n[green]Auto-applying safe improvements...[/green]")
        # TODO: Implement auto-apply logic


@app.command()
def providers():
    """Show available LLM providers and configuration."""
    setup_logging()

    console.print("[bold blue]LLM Provider Information[/bold blue]\n")

    from .core.llm_manager import LLMManager
    from .core.llm_provider import LLMFactory
    from .db.database import get_db

    # Get available providers
    available = LLMFactory.get_available_providers()

    console.print("[bold]Available Providers:[/bold]")
    for provider in available:
        console.print(f"  ✅ {provider}")

    if not available:
        console.print("  ⚠️  No providers available")
        console.print("\n[yellow]Install providers:[/yellow]")
        console.print("  • OpenAI: pip install openai")
        console.print("  • Anthropic: pip install anthropic")
        console.print("  • Groq: pip install groq")
        console.print("  • Ollama: curl -fsSL https://ollama.ai/install.sh | sh")
        return

    # Get configuration
    db = get_db()
    with db.session_scope() as session:
        from .core.cost_tracker import CostTracker
        manager = LLMManager(CostTracker(session))

        info = manager.get_provider_info()

        console.print("\n[bold]Configured:[/bold]")
        console.print(f"  Default: {info['configured']['default']}")
        console.print(f"  Advanced: {info['configured']['advanced']}")
        console.print(f"  Free: {info['configured']['free']}")

        console.print("\n[bold]Strategy:[/bold]")
        console.print(f"  Use free for simple: {info['strategy']['use_free_for_simple']}")
        console.print(f"  Cost threshold: ${info['strategy']['cost_threshold']}")


@app.command()
def test_llm(
    provider: str = typer.Option("ollama", help="Provider to test (openai, anthropic, ollama, groq)"),
    model: str = typer.Option("llama3.1:8b", help="Model to test"),
):
    """Test LLM provider connection."""
    setup_logging()

    console.print(f"[bold blue]Testing {provider}:{model}...[/bold blue]\n")

    from .core.llm_provider import LLMFactory

    try:
        # Get config
        from .core.config import get_config
        config = get_config()

        # Get API key
        api_key = None
        if provider == "openai":
            api_key = config.llm.openai_api_key
        elif provider == "anthropic":
            api_key = config.llm.anthropic_api_key
        elif provider == "groq":
            api_key = config.llm.groq_api_key

        # Create provider
        llm = LLMFactory.create_provider(provider, model, api_key=api_key)

        if not llm.is_available():
            console.print(f"[red]❌ Provider {provider} not available[/red]")
            return

        console.print("✅ Provider available")
        console.print("Sending test prompt...")

        # Test completion
        response = llm.complete(
            prompt="Say 'Hello from AIBooks' and nothing else.",
            temperature=0.1,
            max_tokens=50,
        )

        console.print(f"\n[green]✅ Success![/green]")
        console.print(f"Response: {response.content}")
        console.print(f"Tokens: {response.tokens_in} in, {response.tokens_out} out")
        console.print(f"Cost: ${response.cost:.4f}")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


@app.command()
def version():
    """Show AIBooks version."""
    from . import __version__

    console.print(f"AIBooks version {__version__}")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
