#!/usr/bin/env python3
"""
Agent Sanitizer CLI - Interactive tool for sanitizing AI agent logs.

Usage:
    uvx agent-sanitizer
    uvx agent-sanitizer --input ~/.claude/projects --output ./clean-dataset
    uvx agent-sanitizer --upload zenlm/my-dataset
"""

import sys
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table
from rich.prompt import Confirm, Prompt

from .sanitizer import AgentSanitizer
from .detectors import SecurityDetector

console = Console()


@click.command()
@click.option(
    '--input', '-i',
    type=click.Path(exists=True, path_type=Path),
    help='Input directory containing agent logs (e.g., ~/.claude/projects)'
)
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    help='Output directory for sanitized dataset'
)
@click.option(
    '--format',
    type=click.Choice(['claude', 'openai', 'auto'], case_sensitive=False),
    default='auto',
    help='Agent log format (auto-detect by default)'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be changed without modifying files'
)
@click.option(
    '--upload',
    help='Upload to HuggingFace Hub (e.g., username/dataset-name)'
)
@click.option(
    '--private',
    is_flag=True,
    help='Make HuggingFace dataset private'
)
@click.option(
    '--interactive/--no-interactive',
    default=True,
    help='Interactive mode with confirmations'
)
def main(
    input: Optional[Path],
    output: Optional[Path],
    format: str,
    dry_run: bool,
    upload: Optional[str],
    private: bool,
    interactive: bool
):
    """🧹 Sanitize AI agent logs for safe dataset sharing.
    
    This tool helps you:
    - Remove PII (names, emails, phone numbers)
    - Clean credentials (API keys, passwords, tokens)
    - Anonymize file paths and project names
    - Upload sanitized data to HuggingFace
    
    Quick start:
        uvx agent-sanitizer
    """
    console.print(Panel.fit(
        "[bold cyan]Agent Sanitizer v0.1.0[/bold cyan]\n"
        "Clean AI agent logs for safe sharing",
        border_style="cyan"
    ))
    
    # Interactive setup if needed
    if interactive and not input:
        console.print("\n[yellow]Let's set up your sanitization![/yellow]\n")
        
        # Detect common agent directories
        common_paths = detect_agent_directories()
        if common_paths:
            console.print("[green]Found agent directories:[/green]")
            for i, path in enumerate(common_paths, 1):
                console.print(f"  {i}. {path}")
            
            choice = Prompt.ask(
                "\nSelect directory or enter custom path",
                default="1"
            )
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(common_paths):
                    input = common_paths[idx]
            except ValueError:
                input = Path(choice).expanduser()
        else:
            input = Path(Prompt.ask(
                "Enter path to agent logs",
                default="~/.claude/projects"
            )).expanduser()
    
    if not input:
        console.print("[red]Error: No input directory specified[/red]")
        console.print("Use --input or run interactively")
        sys.exit(1)
    
    input = Path(input).expanduser().resolve()
    
    if not output:
        output = Path.cwd() / "sanitized-dataset"
        if interactive:
            custom = Prompt.ask(
                f"Output directory",
                default=str(output)
            )
            output = Path(custom)
    
    output = Path(output).expanduser().resolve()
    
    # Run audit first
    console.print(f"\n[cyan]📊 Analyzing logs in {input}...[/cyan]\n")
    
    detector = SecurityDetector()
    sanitizer = AgentSanitizer(detector)
    
    # Scan for issues
    with Progress() as progress:
        task = progress.add_task("[cyan]Scanning...", total=None)
        issues = sanitizer.scan_directory(input, format=format)
        progress.update(task, completed=True)
    
    # Show audit results
    show_audit_results(issues)
    
    # Confirm if interactive
    if interactive and issues['total'] > 0:
        if not Confirm.ask("\n[yellow]Proceed with sanitization?[/yellow]"):
            console.print("[yellow]Cancelled[/yellow]")
            return
    
    # Sanitize
    if dry_run:
        console.print("\n[yellow]🔍 DRY RUN - No files will be modified[/yellow]")
    
    console.print(f"\n[cyan]🧹 Sanitizing dataset...[/cyan]")
    
    result = sanitizer.sanitize_directory(
        input_dir=input,
        output_dir=output,
        dry_run=dry_run,
        format=format
    )
    
    # Show results
    show_sanitization_results(result, dry_run)
    
    # Upload to HuggingFace if requested
    if upload and not dry_run:
        if interactive:
            if not Confirm.ask(f"\n[yellow]Upload to HuggingFace ({upload})?[/yellow]"):
                console.print("[green]✅ Sanitization complete![/green]")
                console.print(f"[dim]Dataset saved to: {output}[/dim]")
                return
        
        upload_to_huggingface(output, upload, private)
    
    console.print("\n[green]✅ Done![/green]")
    if not dry_run:
        console.print(f"[dim]Dataset saved to: {output}[/dim]")


def detect_agent_directories() -> list[Path]:
    """Auto-detect common agent log directories."""
    common = [
        Path.home() / ".claude" / "projects",
        Path.home() / ".cursor" / "logs",
        Path.home() / ".continue" / "sessions",
        Path.home() / ".aider" / "history",
    ]
    return [p for p in common if p.exists()]


def show_audit_results(issues: dict):
    """Display audit results in a nice table."""
    table = Table(title="Security Audit Results")
    table.add_column("Category", style="cyan")
    table.add_column("Found", justify="right", style="yellow")
    table.add_column("Severity", style="magenta")
    
    severity_map = {
        'credentials': '🔴 Critical',
        'names': '🟡 Medium',
        'emails': '🟡 Medium',
        'phone_numbers': '🟡 Medium',
        'crypto_keys': '🔴 Critical',
        'api_keys': '🟠 High',
    }
    
    total = 0
    for category, count in issues.items():
        if category == 'total':
            continue
        if count > 0:
            severity = severity_map.get(category, '⚪ Low')
            table.add_row(category.replace('_', ' ').title(), str(count), severity)
            total += count
    
    if total > 0:
        table.add_section()
        table.add_row("[bold]Total Issues[/bold]", f"[bold]{total}[/bold]", "")
    
    console.print(table)
    
    if total == 0:
        console.print("[green]✅ No security issues found![/green]")


def show_sanitization_results(result: dict, dry_run: bool):
    """Display sanitization results."""
    console.print()
    
    table = Table(title="Sanitization Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")
    
    table.add_row("Files Processed", f"{result['files_processed']:,}")
    table.add_row("Lines Processed", f"{result['lines_processed']:,}")
    table.add_row("Lines Modified", f"{result['lines_modified']:,}")
    
    if result.get('replacements'):
        table.add_section()
        for category, count in result['replacements'].items():
            if count > 0:
                table.add_row(
                    f"  {category.replace('_', ' ').title()}",
                    str(count)
                )
    
    console.print(table)


def upload_to_huggingface(dataset_dir: Path, repo_id: str, private: bool):
    """Upload sanitized dataset to HuggingFace."""
    console.print(f"\n[cyan]📤 Uploading to HuggingFace: {repo_id}...[/cyan]")
    
    try:
        from datasets import Dataset, DatasetDict
        from huggingface_hub import HfApi
        
        # Load splits
        splits_dir = dataset_dir / "splits"
        if not splits_dir.exists():
            console.print("[red]Error: No splits directory found[/red]")
            return
        
        splits = {}
        for split_file in splits_dir.glob("*.jsonl"):
            split_name = split_file.stem
            data = []
            with open(split_file) as f:
                for line in f:
                    data.append(json.loads(line))
            splits[split_name] = Dataset.from_list(data)
            console.print(f"  Loaded {split_name}: {len(data):,} examples")
        
        if not splits:
            console.print("[red]Error: No data found[/red]")
            return
        
        dataset = DatasetDict(splits)
        
        console.print(f"\n[yellow]Uploading...[/yellow]")
        dataset.push_to_hub(repo_id, private=private)
        
        console.print(f"[green]✅ Uploaded to https://huggingface.co/datasets/{repo_id}[/green]")
        
    except ImportError:
        console.print("[red]Error: huggingface_hub not installed[/red]")
        console.print("Run: pip install huggingface_hub datasets")
    except Exception as e:
        console.print(f"[red]Error uploading: {e}[/red]")


if __name__ == "__main__":
    main()
