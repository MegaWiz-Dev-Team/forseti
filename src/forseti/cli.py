"""CLI entry point for Forseti."""

from __future__ import annotations

import asyncio
import logging
import sys

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from forseti import __version__

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with Rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, show_path=False, markup=True)],
    )


@click.group()
@click.version_option(version=__version__, prog_name="forseti")
def main():
    """⚖️ Forseti — LLM-Powered E2E Testing Service (เทพแห่งความยุติธรรม)"""
    pass


@main.command()
@click.argument("script_path", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True, help="Generate action plans without browser execution")
@click.option("--headed", is_flag=True, help="Run browser in headed mode (visible)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
@click.option("--model", default=None, help="LLM model override (e.g. gemini-2.0-flash)")
@click.option("--provider", default=None, help="LLM provider: gemini or openai_compatible")
@click.option("--base-url-override", default=None, help="Override base_url from script")
def run(script_path, dry_run, headed, verbose, model, provider, base_url_override):
    """Run a test script.

    Example: forseti run examples/test_scripts/login_test.yaml
    """
    setup_logging(verbose)

    from forseti.config import ForsetiConfig
    from forseti.parser import parse_script
    from forseti.runner import ForsetiRunner

    # Load config from environment
    config = ForsetiConfig.from_env()

    # Apply CLI overrides
    if headed:
        config.browser.headless = False
    if model:
        config.llm.model = model
    if provider:
        config.llm.provider = provider

    # Parse test script
    console.print(f"\n⚖️  [bold]Forseti v{__version__}[/bold] — E2E Testing Service\n")
    try:
        script = parse_script(script_path)
    except Exception as e:
        console.print(f"[red]❌ Failed to parse script: {e}[/red]")
        sys.exit(1)

    if base_url_override:
        script.base_url = base_url_override

    # Run
    runner = ForsetiRunner(config)
    result = asyncio.run(runner.run(script, dry_run=dry_run))

    # Exit with non-zero code if there are failures
    if result.failed > 0 or result.errors > 0:
        sys.exit(1)


@main.command()
@click.argument("script_path", type=click.Path(exists=True))
def validate(script_path):
    """Validate a test script's syntax.

    Example: forseti validate examples/test_scripts/login_test.yaml
    """
    setup_logging()

    from forseti.parser import validate_script

    issues = validate_script(script_path)

    if not issues:
        console.print(f"[green]✅ Script is valid: {script_path}[/green]")
    else:
        console.print(f"[red]❌ Script has {len(issues)} issue(s):[/red]")
        for issue in issues:
            console.print(f"  • {issue}")
        sys.exit(1)


@main.command()
@click.argument("results_path", type=click.Path(exists=True))
@click.option("--output", "-o", default="reports", help="Output directory for report")
def report(results_path, output):
    """Generate HTML report from a JSON results file.

    Example: forseti report results/forseti_SIT_20260316.json
    """
    setup_logging()

    import json

    from forseti.models import TestSuiteResult
    from forseti.reporter.html_report import HTMLReportGenerator

    with open(results_path, encoding="utf-8") as f:
        data = json.load(f)

    result = TestSuiteResult(**data)
    reporter = HTMLReportGenerator(output_dir=output)
    path = reporter.generate(result)
    console.print(f"[green]📊 Report generated: {path}[/green]")


@main.command()
def info():
    """Show Forseti configuration and environment info."""
    setup_logging()

    from forseti.config import ForsetiConfig

    config = ForsetiConfig.from_env()

    table = Table(title="⚖️ Forseti Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)
    table.add_row("LLM Provider", config.llm.provider)
    table.add_row("LLM Model", config.llm.model)
    table.add_row("LLM API Key", "✅ Set" if config.llm.api_key else "❌ Not set")
    table.add_row("LLM Base URL", config.llm.base_url or "(default)")
    table.add_row("Browser", config.browser.browser_type)
    table.add_row("Headless", str(config.browser.headless))
    table.add_row("GitHub Enabled", str(config.github.enabled))
    table.add_row("GitHub Repo", config.github.repo or "(not set)")

    console.print(table)


if __name__ == "__main__":
    main()
