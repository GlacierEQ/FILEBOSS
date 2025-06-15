#!/usr/bin/env python3
"""
Legal Data Pipeline CLI - Command-line interface for the legal data pipeline
"""
import os
import sys
import json
import argparse
from pathlib import Path
import logging
from typing import List, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
import pandas as pd
from bs4 import BeautifulSoup

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from implementation.legal_data_pipeline import LegalDataPipeline
from implementation.legal_scraping import LegalAPIClient

# Set up console for rich output
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("legal_data_cli.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Legal-Data-CLI")

def print_header():
    """Print the CLI header"""
    console.print("\n[bold cyan]================================[/]")
    console.print("[bold cyan]  Legal Data Pipeline CLI  [/]")
    console.print("[bold cyan]================================[/]")

def scrape_command(args):
    """Handle scrape command"""
    console.print(f"\n[bold]Scraping URLs from {args.input}...[/]")
    
    # Load URLs from file or use provided URL
    urls = []
    if args.input.startswith(('http://', 'https://')):
        urls = [args.input]
    else:
        try:
            with open(args.input, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception as e:
            console.print(f"[red]Error loading URLs from file: {str(e)}[/]")
            return 1
    
    console.print(f"Loaded {len(urls)} URL(s) to scrape")
    
    # Initialize pipeline
    pipeline = LegalDataPipeline(output_dir=args.output_dir)
    
    # Set up credentials if provided
    credentials = None
    if args.username and args.password:
        credentials = {"username": args.username, "password": args.password}
    
    # Scrape URLs with progress bar
    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        "[bold green]{task.fields[status]}",
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Scraping URLs", total=len(urls), status="Starting...")
        
        results = []
        for i, url in enumerate(urls):
            progress.update(task, description=f"[cyan]Scraping URL {i+1}/{len(urls)}", status=f"Processing...")
            
            try:
                result = pipeline.scrape_urls([url], method=args.method, credentials=credentials)[0]
                results.append(result)
                
                if result.get("success", False):
                    status = f"[green]Success[/]"
                else:
                    status = f"[red]Failed[/]: {result.get('error', 'Unknown error')}"
                
                progress.update(task, advance=1, status=status)
            except Exception as e:
                console.print(f"[red]Error scraping {url}: {str(e)}[/]")
                progress.update(task, advance=1, status=f"[red]Error[/]")
    
    # Process results
    success_count = sum(1 for r in results if r.get("success", False))
    console.print(f"\n[bold]Scraping complete: {success_count}/{len(results)} successful[/]")
    
    # Process and save results
    if results:
        processed_docs = pipeline.process_legal_documents(results)
        
        # Save to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(args.output_dir, f"scraped_data_{timestamp}.json")
        with open(output_path, 'w') as f:
            json.dump(processed_docs, f, indent=2)
        console.print(f"Saved processed data to: {output_path}")
        
        # Export to CSV if requested
        if args.csv:
            csv_path = pipeline.export_to_csv(processed_docs)
            if csv_path:
                console.print(f"Exported data to CSV: {csv_path}")
    
    return 0

def search_command(args):
    """Handle search command"""
    console.print(f"\n[bold]Searching for '{args.query}'...[/]")
    
    # Initialize API client
    api_client = LegalAPIClient(api_key=args.api_key)
    
    # Search for the query
    results = api_client.search_courtlistener(args.query, page=args.page)
    
    if "results" in results and results["results"]:
        # Extract results
        cases = results["results"]
        
        # Display results in a table
        table = Table(title=f"Search Results for '{args.query}'")
        table.add_column("Case Name", style="cyan")
        table.add_column("Court", style="green")
        table.add_column("Date", style="yellow")
        table.add_column("URL")
        
        for case in cases[:args.limit]:
            table.add_row(
                case.get("caseName", "Unknown"),
                case.get("court", "Unknown"),
                case.get("dateFiled", "Unknown"),
                f"https://www.courtlistener.com{case.get('absolute_url', '')}"
            )
        
        console.print(table)
        
        # Save results if requested
        if args.save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"search_results_{timestamp}.json"
            with open(output_path, 'w') as f:
                json.dump(cases[:args.limit], f, indent=2)
            console.print(f"Saved search results to: {output_path}")
    else:
        console.print("[yellow]No results found.[/]")
    
    return 0

def analyze_command(args):
    """Handle analyze command"""
    console.print(f"\n[bold]Analyzing legal document: {args.file}...[/]")
    
    try:
        # Read the file
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        console.print(f"Loaded document: {len(text)} characters")
        
        # Initialize pipeline
        pipeline = LegalDataPipeline(output_dir=args.output_dir)
        
        # Create document with metadata
        document = {
            "id": os.path.basename(args.file),
            "text_content": text,
            "file_path": args.file,
            "timestamp": datetime.now().isoformat()
        }
        
        # Process document to extract structure
        processed_doc = pipeline._extract_case_information(
            BeautifulSoup(f"<html><body>{text}</body></html>", 'html.parser')
        )
        document["case_info"] = processed_doc
        
        # Extract citations
        processed_citations = pipeline._extract_citations(
            BeautifulSoup(f"<html><body>{text}</body></html>", 'html.parser')
        )
        document["citations"] = processed_citations
        
        # Display analysis results
        console.print("\n[bold cyan]Document Analysis:[/]")
        
        # Display case info
        if document["case_info"]:
            console.print("\n[bold]Case Information:[/]")
            for key, value in document["case_info"].items():
                console.print(f"  [green]{key}:[/] {value}")
        
        # Display citations
        if document["citations"]:
            console.print(f"\n[bold]Citations ({len(document['citations'])}):[/]")
            for citation in document["citations"]:
                console.print(f"  - {citation}")
        else:
            console.print("\n[yellow]No citations found.[/]")
        
        # Save analysis if requested
        if args.save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"document_analysis_{timestamp}.json"
            with open(output_path, 'w') as f:
                json.dump(document, f, indent=2)
            console.print(f"\nSaved analysis to: {output_path}")
        
        return 0
    
    except Exception as e:
        console.print(f"[red]Error analyzing document: {str(e)}[/]")
        return 1

def pipeline_command(args):
    """Handle pipeline command (full pipeline execution)"""
    console.print("\n[bold]Executing full legal data pipeline...[/]")
    
    # Load URLs from file
    urls = []
    try:
        with open(args.urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        console.print(f"Loaded {len(urls)} URL(s) from {args.urls_file}")
    except Exception as e:
        console.print(f"[red]Error loading URLs from file: {str(e)}[/]")
        return 1
    
    # Initialize pipeline
    es_host = args.elasticsearch if args.elasticsearch != "none" else None
    pipeline = LegalDataPipeline(
        elasticsearch_host=es_host,
        output_dir=args.output_dir,
        max_workers=args.workers,
        api_key=args.api_key
    )
    
    # Run the pipeline
    console.print("\n[bold]Running pipeline...[/]")
    results = pipeline.run_full_pipeline(
        urls=urls,
        scrape_method=args.method,
        index_name=args.index,
        analyze=args.analyze,
        export_csv=args.csv
    )
    
    # Display results
    console.print("\n[bold cyan]Pipeline Results:[/]")
    console.print(f"Status: [{'green' if results['status'] == 'success' else 'red'}]{results['status']}[/]")
    console.print(f"URLs processed: {results['urls_count']}")
    console.print(f"Successfully scraped: {results.get('successful_scrape_count', 0)}/{results.get('scraped_count', 0)}")
    console.print(f"Documents processed: {results.get('processed_count', 0)}")
    
    if 'indexed' in results:
        console.print(f"Documents indexed: [{'green' if results['indexed'] else 'yellow'}]{results['indexed']}[/]")
    
    if 'csv_export_path' in results:
        console.print(f"CSV export: {results['csv_export_path']}")
    
    return 0

def extract_command(args):
    """Handle extract command (extract citation information)"""
    console.print(f"\n[bold]Extracting citations from {args.input}...[/]")
    
    try:
        # Read input (file or text)
        text = ""
        if os.path.isfile(args.input):
            with open(args.input, 'r', encoding='utf-8') as f:
                text = f.read()
            console.print(f"Read {len(text)} characters from file")
        else:
            text = args.input
            console.print("Using provided text as input")
        
        # Initialize pipeline
        pipeline = LegalDataPipeline()
        
        # Create BeautifulSoup object
        soup = BeautifulSoup(f"<html><body>{text}</body></html>", 'html.parser')
        
        # Extract citations
        citations = pipeline._extract_citations(soup)
        
        # Display results
        if citations:
            console.print(f"\n[bold green]Found {len(citations)} citations:[/]")
            for i, citation in enumerate(citations):
                console.print(f"  {i+1}. {citation}")
                
            if args.lookup and len(citations) > 0:
                console.print("\n[bold]Looking up citation details...[/]")
                api_client = LegalAPIClient(api_key=args.api_key)
                
                # Look up first citation or specified one
                lookup_idx = min(args.lookup_index, len(citations)) - 1 if args.lookup_index else 0
                citation = citations[lookup_idx]
                
                console.print(f"Looking up: {citation}")
                results = api_client.search_courtlistener(citation, page=1)
                
                if "results" in results and results["results"]:
                    case = results["results"][0]
                    console.print(Panel(
                        f"[bold cyan]{case.get('caseName', 'Unknown case')}[/]\n"
                        f"Date: {case.get('dateFiled', 'Unknown')}\n"
                        f"Court: {case.get('court', 'Unknown')}\n"
                        f"URL: https://www.courtlistener.com{case.get('absolute_url', '')}\n\n"
                        f"[italic]{case.get('snippet', '')}[/]",
                        title=f"Citation Details: {citation}",
                        border_style="green"
                    ))
                else:
                    console.print(f"[yellow]No details found for citation: {citation}[/]")
        else:
            console.print("[yellow]No citations found in the input text.[/]")
        
        # Save results if requested
        if args.save and citations:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"citations_{timestamp}.json"
            with open(output_path, 'w') as f:
                json.dump({
                    "input": args.input,
                    "extraction_time": datetime.now().isoformat(),
                    "citations": citations
                }, f, indent=2)
            console.print(f"Saved citations to: {output_path}")
        
        return 0
    
    except Exception as e:
        console.print(f"[red]Error extracting citations: {str(e)}[/]")
        return 1

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Legal Data Pipeline Command-Line Interface")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape legal data from URLs")
    scrape_parser.add_argument("input", help="URL or file containing URLs to scrape")
    scrape_parser.add_argument("--method", choices=["playwright", "selenium", "api"], default="playwright", help="Scraping method")
    scrape_parser.add_argument("--output-dir", default="legal_data", help="Output directory for scraped data")
    scrape_parser.add_argument("--username", help="Username for login if needed")
    scrape_parser.add_argument("--password", help="Password for login if needed")
    scrape_parser.add_argument("--csv", action="store_true", help="Export results to CSV")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for legal data")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--api-key", help="API key for legal data services")
    search_parser.add_argument("--page", type=int, default=1, help="Page number for results")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum number of results")
    search_parser.add_argument("--save", action="store_true", help="Save search results to file")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a legal document")
    analyze_parser.add_argument("file", help="File to analyze")
    analyze_parser.add_argument("--output-dir", default="legal_data", help="Output directory")
    analyze_parser.add_argument("--save", action="store_true", help="Save analysis results to file")
    
    # Pipeline command
    pipeline_parser = subparsers.add_parser("pipeline", help="Run the full legal data pipeline")
    pipeline_parser.add_argument("urls_file", help="File containing URLs to process")
    pipeline_parser.add_argument("--method", choices=["playwright", "selenium", "api"], default="playwright", help="Scraping method")
    pipeline_parser.add_argument("--output-dir", default="legal_data", help="Output directory")
    pipeline_parser.add_argument("--elasticsearch", default="none", help="Elasticsearch host URL or 'none' to disable")
    pipeline_parser.add_argument("--workers", type=int, default=4, help="Maximum number of concurrent workers")
    pipeline_parser.add_argument("--api-key", help="API key for legal data services")
    pipeline_parser.add_argument("--index", default="legal_documents", help="Elasticsearch index name")
    pipeline_parser.add_argument("--analyze", action="store_true", help="Perform LLM analysis")
    pipeline_parser.add_argument("--csv", action="store_true", help="Export results to CSV")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract citations from text")
    extract_parser.add_argument("input", help="Text or file to extract citations from")
    extract_parser.add_argument("--save", action="store_true", help="Save citations to file")
    extract_parser.add_argument("--lookup", action="store_true", help="Look up citation details")
    extract_parser.add_argument("--lookup-index", type=int, help="Index of citation to look up")
    extract_parser.add_argument("--api-key", help="API key for citation lookup")
    
    args = parser.parse_args()
    
    # Print header
    print_header()
    
    # Handle command
    if args.command == "scrape":
        return scrape_command(args)
    elif args.command == "search":
        return search_command(args)
    elif args.command == "analyze":
        return analyze_command(args)
    elif args.command == "pipeline":
        return pipeline_command(args)
    elif args.command == "extract":
        return extract_command(args)
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
