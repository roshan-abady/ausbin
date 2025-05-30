# tests/integration_test.py
"""
Standalone integration tests for the Business Names API
This file provides a user-friendly test runner separate from pytest

Author: Roshan Abady
Email: roshanabady@gmail.com
"""
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.business_names_api import BusinessNamesAPI, BusinessNamesAPIError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

console = Console()

def run_connectivity_test():
    """Test API connectivity"""
    with console.status("[bold green]Testing API connectivity..."):
        try:
            api = BusinessNamesAPI()
            result = api.test_connection()
            
            if result:
                console.print("✅ API connectivity: [bold green]PASSED[/bold green]")
                return True
            else:
                console.print("❌ API connectivity: [bold red]FAILED[/bold red]")
                return False
                
        except Exception as e:
            console.print(f"❌ API connectivity: [bold red]ERROR[/bold red] - {e}")
            return False

def run_basic_search_test():
    """Test basic search functionality"""
    with console.status("[bold green]Testing basic search..."):
        try:
            api = BusinessNamesAPI()
            result = api.search_business_names(limit=5)
            
            if result.get('success'):
                records = result.get('result', {}).get('records', [])
                console.print(f"✅ Basic search: [bold green]PASSED[/bold green] ({len(records)} records)")
                return True
            else:
                console.print("❌ Basic search: [bold red]FAILED[/bold red] - No success flag")
                return False
                
        except Exception as e:
            console.print(f"❌ Basic search: [bold red]ERROR[/bold red] - {e}")
            return False

def run_query_search_test():
    """Test query search functionality"""
    with console.status("[bold green]Testing query search..."):
        try:
            api = BusinessNamesAPI()
            result = api.search_business_names(query="PTY", limit=3)
            
            if result.get('success'):
                records = result.get('result', {}).get('records', [])
                console.print(f"✅ Query search: [bold green]PASSED[/bold green] ({len(records)} records)")
                return True
            else:
                console.print("❌ Query search: [bold red]FAILED[/bold red] - No success flag")
                return False
                
        except Exception as e:
            console.print(f"❌ Query search: [bold red]ERROR[/bold red] - {e}")
            return False

def run_performance_test():
    """Test API performance"""
    with console.status("[bold green]Testing API performance..."):
        try:
            api = BusinessNamesAPI()
            
            start_time = time.time()
            result = api.search_business_names(limit=100)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if result.get('success') and response_time < 30:
                console.print(f"✅ Performance test: [bold green]PASSED[/bold green] ({response_time:.2f}s)")
                return True
            else:
                console.print(f"❌ Performance test: [bold red]FAILED[/bold red] ({response_time:.2f}s)")
                return False
                
        except Exception as e:
            console.print(f"❌ Performance test: [bold red]ERROR[/bold red] - {e}")
            return False

def main():
    """Run all integration tests"""
    console.print(Panel(
        "[bold blue]🚀 Business Names API Integration Tests[/bold blue]",
        style="blue"
    ))
    
    tests = [
        ("API Connectivity", run_connectivity_test),
        ("Basic Search", run_basic_search_test),
        ("Query Search", run_query_search_test),
        ("Performance", run_performance_test),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        console.print(f"\n[bold]Running {test_name}...[/bold]")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    console.print(f"\n{'='*50}")
    console.print(Panel("[bold]Integration Test Summary[/bold]"))
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Test", style="cyan")
    summary_table.add_column("Result", style="green")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        summary_table.add_row(test_name, status)
    
    console.print(summary_table)
    console.print(f"\n[bold]Overall: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print("[bold green]🎉 All integration tests passed![/bold green]")
        return True
    else:
        console.print(f"[bold red]❌ {total - passed} test(s) failed[/bold red]")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
