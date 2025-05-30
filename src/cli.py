# Author: Roshan Abady
# cli.py - Enhanced with proper visualizations
# AUSBIN - Australian Business Names Register CLI

import click
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime, timedelta
import sys
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz, process
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot
from plotly.subplots import make_subplots
import tempfile
import webbrowser
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint
from pathlib import Path
import time
from collections import Counter
import re
from wordcloud import WordCloud
from src.business_names_api import BusinessNamesAPI, BusinessNamesAPIError

"""
Enterprise-grade command line utility for the Australian Business Names Register.

Author: Roshan Abady
Email: roshanabady@gmail.com
"""

# Initialize rich console for beautiful output
console = Console()

class BusinessNamesCLI:
    """
    Enterprise-grade command line utility for AUSBIN - Australian Business Names Register
    
    Provides filtering, visualization, and similarity matching capabilities
    for business intelligence and data exploration workflows.
    """
    
    def __init__(self):
        self.api = BusinessNamesAPI()
        self.data_cache = None
        self.cache_file = Path("data_cache.pkl")
        
    def fetch_data(self, limit: Optional[int] = None, use_cache: bool = True) -> pd.DataFrame:
        """Fetch and cache business names data - gets ALL records by default"""
        # Try to load from cache first
        if use_cache and self.cache_file.exists() and self.data_cache is None:
            try:
                console.print("[blue]Loading data from cache...[/blue]")
                self.data_cache = pd.read_pickle(self.cache_file)
                console.print(f"[green]Loaded {len(self.data_cache)} records from cache[/green]")
                return self.data_cache
            except Exception as e:
                console.print(f"[yellow]Cache load failed: {e}. Fetching fresh data...[/yellow]")
        
        if self.data_cache is not None:
            return self.data_cache
            
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching business names data...", total=None)
            
            try:
                # Fetch ALL records if no limit specified
                fetch_limit = limit if limit is not None else None  # None means get all available
                
                if fetch_limit is None:
                    console.print("[blue]Fetching ALL available records from API...[/blue]")
                else:
                    console.print(f"[blue]Fetching up to {fetch_limit} records from API...[/blue]")
                
                result = self.api.search_business_names(limit=fetch_limit)
                records = result.get('result', {}).get('records', [])
                
                if not records:
                    console.print("[red]No data retrieved from API[/red]")
                    sys.exit(1)
                
                self.data_cache = pd.DataFrame(records)
                
                # Convert date columns
                date_columns = ['BN_REG_DT', 'BN_RENEWAL_DT', 'BN_CANCEL_DT']
                for col in date_columns:
                    if col in self.data_cache.columns:
                        self.data_cache[col] = pd.to_datetime(
                            self.data_cache[col], 
                            errors='coerce'
                        )
                
                # Save to cache
                try:
                    self.data_cache.to_pickle(self.cache_file)
                    console.print(f"[blue]Data cached to {self.cache_file}[/blue]")
                except Exception as e:
                    console.print(f"[yellow]Cache save failed: {e}[/yellow]")
                
                progress.update(task, completed=True)
                console.print(f"[green]Successfully loaded {len(self.data_cache)} business records[/green]")
                
                return self.data_cache
                
            except BusinessNamesAPIError as e:
                console.print(f"[red]API Error: {e}[/red]")
                sys.exit(1)
    
    def apply_filters(
        self, 
        df: pd.DataFrame,
        status_filter: Optional[str] = None,
        date_from: Optional[str] = None,
        state_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """Apply filtering parameters to the dataset"""
        filtered_df = df.copy()
        
        # Filter by business status
        if status_filter:
            filtered_df = filtered_df[
                filtered_df['BN_STATUS'].str.contains(status_filter, case=False, na=False)
            ]
            console.print(f"[blue]Applied status filter: {status_filter}[/blue]")
        
        # Filter by registration date
        if date_from:
            try:
                from_date = pd.to_datetime(date_from)
                filtered_df = filtered_df[
                    filtered_df['BN_REG_DT'] >= from_date
                ]
                console.print(f"[blue]Applied date filter: from {date_from}[/blue]")
            except ValueError:
                console.print(f"[yellow]Warning: Invalid date format '{date_from}'. Expected YYYY-MM-DD[/yellow]")
        
        # Filter by state (if available in data)
        if state_filter and 'BN_STATE' in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df['BN_STATE'].str.contains(state_filter, case=False, na=False)
            ]
            console.print(f"[blue]Applied state filter: {state_filter}[/blue]")
        
        console.print(f"[green]Filtered dataset: {len(filtered_df)} records[/green]")
        return filtered_df
    
    def similarity_search(
        self, 
        df: pd.DataFrame, 
        search_term: str, 
        limit: int = 50,
        min_threshold: int = 50
    ) -> pd.DataFrame:
        """
        Perform similarity matching on business names
        Returns exact matches first, then by decreasing similarity
        """
        if 'BN_NAME' not in df.columns:
            console.print("[red]BN_NAME column not found in dataset[/red]")
            return pd.DataFrame()
        
        search_term_clean = search_term.upper().strip()
        business_names = df['BN_NAME'].fillna('').astype(str)
        
        # Debug: Show search info
        console.print(f"[blue]Searching in {len(df)} records for '{search_term}'...[/blue]")
        
        # Find exact matches first
        exact_matches = df[business_names.str.upper() == search_term_clean].copy()
        if len(exact_matches) > 0:
            exact_matches['similarity_score'] = 100.0
            exact_matches['match_type'] = 'Exact'
            console.print(f"[green]Found {len(exact_matches)} exact matches[/green]")
        
        # Find partial string matches (contains)
        partial_matches = df[
            (business_names.str.upper() != search_term_clean) & 
            (business_names.str.upper().str.contains(search_term_clean, na=False))
        ].copy()
        
        if len(partial_matches) > 0:
            partial_matches['similarity_score'] = 95.0
            partial_matches['match_type'] = 'Contains'
            console.print(f"[green]Found {len(partial_matches)} partial matches[/green]")
        
        # Find fuzzy matches for remaining records
        remaining_df = df[
            (~business_names.str.upper().str.contains(search_term_clean, na=False)) &
            (business_names.str.upper() != search_term_clean)
        ].copy()
        
        fuzzy_matches = pd.DataFrame()
        
        if len(remaining_df) > 0:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Computing similarity scores...", total=None)
                
                # Use fuzzywuzzy for similarity scoring
                similarity_scores = []
                valid_indices = []
                
                # Limit fuzzy search to reasonable number for performance
                search_sample = remaining_df.head(10000) if len(remaining_df) > 10000 else remaining_df
                
                for idx, name in enumerate(search_sample['BN_NAME']):
                    if pd.notna(name) and str(name).strip():
                        score = fuzz.ratio(search_term_clean, str(name).upper())
                        if score >= min_threshold:
                            similarity_scores.append(score)
                            valid_indices.append(idx)
                
                if similarity_scores:
                    fuzzy_matches = search_sample.iloc[valid_indices].copy()
                    fuzzy_matches['similarity_score'] = similarity_scores
                    fuzzy_matches['match_type'] = 'Fuzzy'
                    console.print(f"[green]Found {len(fuzzy_matches)} fuzzy matches[/green]")
                
                progress.update(task, completed=True)
        
        # Combine all results
        all_matches_list = []
        if len(exact_matches) > 0:
            all_matches_list.append(exact_matches)
        if len(partial_matches) > 0:
            all_matches_list.append(partial_matches)
        if len(fuzzy_matches) > 0:
            all_matches_list.append(fuzzy_matches)
        
        if all_matches_list:
            all_matches = pd.concat(all_matches_list, ignore_index=True)
            all_matches = all_matches.sort_values(
                ['similarity_score', 'BN_NAME'], 
                ascending=[False, True]
            ).head(limit)
            
            console.print(f"[green]Total matches found: {len(all_matches)}[/green]")
            return all_matches
        else:
            console.print(f"[yellow]No matches found for '{search_term}' (tried exact, partial, and fuzzy matching)[/yellow]")
            return pd.DataFrame()
    
    def display_table(self, df: pd.DataFrame, similarity_search: bool = False):
        """Display data in a formatted table using Rich"""
        if df.empty:
            console.print("[yellow]No data to display[/yellow]")
            return
        
        # Create Rich table
        table = Table(show_header=True, header_style="bold magenta")
        
        # Define columns to display
        if similarity_search:
            display_columns = ['BN_NAME', 'BN_STATUS', 'BN_REG_DT', 'similarity_score', 'match_type']
            table.add_column("Business Name", style="cyan", width=40)
            table.add_column("Status", style="green")
            table.add_column("Registration Date", style="blue")
            table.add_column("Similarity %", style="yellow", justify="right")
            table.add_column("Match Type", style="magenta")
        else:
            display_columns = ['BN_NAME', 'BN_STATUS', 'BN_REG_DT']
            table.add_column("Business Name", style="cyan", width=50)
            table.add_column("Status", style="green")
            table.add_column("Registration Date", style="blue")
        
        # Add rows
        display_limit = min(50, len(df))
        for _, row in df.head(display_limit).iterrows():
            row_data = []
            for col in display_columns:
                if col in row:
                    if col == 'BN_REG_DT' and pd.notna(row[col]):
                        row_data.append(row[col].strftime('%Y-%m-%d'))
                    elif col == 'similarity_score':
                        row_data.append(f"{row[col]:.1f}")
                    else:
                        row_data.append(str(row[col]) if pd.notna(row[col]) else 'N/A')
                else:
                    row_data.append('N/A')
            table.add_row(*row_data)
        
        console.print(table)
        
        if len(df) > display_limit:
            console.print(f"[yellow]Showing first {display_limit} of {len(df)} records[/yellow]")
    
    def display_search_barchart(self, df: pd.DataFrame, search_term: str):
        """Display search results as a bar chart showing business names with similarity scores"""
        if df.empty:
            console.print("[yellow]No data to display[/yellow]")
            return
        
        # Prepare data for bar chart
        top_matches = df.head(20)  # Show top 20 matches
        
        # Truncate long business names for display
        business_names = [name[:40] + "..." if len(name) > 40 else name 
                         for name in top_matches['BN_NAME']]
        
        # Create bar chart
        fig = go.Figure()
        
        # Add bars with different colors based on match type
        colors = {'Exact': '#1f77b4', 'Contains': '#ff7f0e', 'Fuzzy': '#2ca02c'}
        
        for match_type in ['Exact', 'Contains', 'Fuzzy']:
            mask = top_matches['match_type'] == match_type
            if mask.any():
                fig.add_trace(go.Bar(
                    x=top_matches.loc[mask, 'similarity_score'],
                    y=[business_names[i] for i in range(len(business_names)) if mask.iloc[i]],
                    name=f'{match_type} Match',
                    orientation='h',
                    marker_color=colors[match_type],
                    text=top_matches.loc[mask, 'similarity_score'].round(1),
                    textposition='inside',
                    textfont=dict(color='white', size=12)
                ))
        
        fig.update_layout(
            title=f"Top Business Name Matches for '{search_term}'",
            xaxis_title="Similarity Score (%)",
            yaxis_title="Business Names",
            height=max(600, len(top_matches) * 30),
            showlegend=True,
            template="plotly_white",
            font=dict(size=12)
        )
        
        # Save and display
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            plot(fig, filename=f.name, auto_open=False)
            console.print(f"[green]Bar chart saved to: {f.name}[/green]")
            webbrowser.open(f.name)
    
    def display_search_piechart(self, df: pd.DataFrame, search_term: str):
        """Display search results as a pie chart showing match type distribution"""
        if df.empty:
            console.print("[yellow]No data to display[/yellow]")
            return
        
        # Count match types
        match_counts = df['match_type'].value_counts()
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=match_counts.index,
            values=match_counts.values,
            hole=0.3,
            textinfo='label+percent+value',
            textfont_size=14,
            marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c'])
        )])
        
        fig.update_layout(
            title=f"Match Type Distribution for '{search_term}' ({len(df)} total matches)",
            font=dict(size=14),
            template="plotly_white"
        )
        
        # Save and display
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            plot(fig, filename=f.name, auto_open=False)
            console.print(f"[green]Pie chart saved to: {f.name}[/green]")
            webbrowser.open(f.name)
    
    def display_search_histogram(self, df: pd.DataFrame, search_term: str):
        """Display search results as a histogram showing similarity score distribution"""
        if df.empty or 'similarity_score' not in df.columns:
            console.print("[yellow]No similarity data to display[/yellow]")
            return
        
        # Create histogram of similarity scores
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=df['similarity_score'],
            nbinsx=20,
            name='Similarity Scores',
            marker_color='lightblue',
            opacity=0.7,
            text=df['BN_NAME'],  # Show business names on hover
            hovertemplate='<b>%{text}</b><br>Similarity: %{x}%<extra></extra>'
        ))
        
        # Add vertical line for threshold
        fig.add_vline(x=50, line_dash="dash", line_color="red", 
                     annotation_text="Minimum Threshold (50%)")
        
        fig.update_layout(
            title=f"Similarity Score Distribution for '{search_term}'",
            xaxis_title="Similarity Score (%)",
            yaxis_title="Number of Matches",
            template="plotly_white",
            font=dict(size=12),
            showlegend=False
        )
        
        # Save and display
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            plot(fig, filename=f.name, auto_open=False)
            console.print(f"[green]Histogram saved to: {f.name}[/green]")
            webbrowser.open(f.name)
    
    def display_wordcloud(self, df: pd.DataFrame, search_term: str):
        """Generate and display a word cloud from business names"""
        if df.empty:
            console.print("[yellow]No data to display[/yellow]")
            return
        
        try:
            # Combine all business names
            text = ' '.join(df['BN_NAME'].fillna('').astype(str))
            
            # Clean text - remove common business suffixes and the search term
            common_words = ['PTY', 'LTD', 'LIMITED', 'COMPANY', 'CORP', 'INC', 'LLC', 
                           'SERVICES', 'GROUP', 'HOLDINGS', search_term.upper()]
            
            for word in common_words:
                text = re.sub(r'\b' + re.escape(word) + r'\b', '', text, flags=re.IGNORECASE)
            
            # Generate word cloud
            wordcloud = WordCloud(
                width=800, 
                height=400, 
                background_color='white',
                colormap='viridis',
                max_words=100,
                relative_scaling=0.5,
                random_state=42
            ).generate(text)
            
            # Create plotly figure
            fig = go.Figure()
            
            # Convert word cloud to image and display
            import io
            import base64
            from PIL import Image
            
            # Save word cloud to bytes
            img_buffer = io.BytesIO()
            wordcloud.to_image().save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Convert to base64 for plotly
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            fig.add_layout_image(
                dict(
                    source=f"data:image/png;base64,{img_base64}",
                    xref="paper", yref="paper",
                    x=0, y=1, sizex=1, sizey=1,
                    xanchor="left", yanchor="top"
                )
            )
            
            fig.update_layout(
                title=f"Word Cloud for Business Names matching '{search_term}'",
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                template="plotly_white"
            )
            
            # Save and display
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                plot(fig, filename=f.name, auto_open=False)
                console.print(f"[green]Word cloud saved to: {f.name}[/green]")
                webbrowser.open(f.name)
                
        except ImportError:
            console.print("[yellow]WordCloud package not installed. Install with: pip install wordcloud[/yellow]")
        except Exception as e:
            console.print(f"[red]Error generating word cloud: {e}[/red]")
    
    def display_chart(self, df: pd.DataFrame):
        """Display data as interactive charts using Plotly"""
        if df.empty:
            console.print("[yellow]No data to display[/yellow]")
            return
        
        # Create status distribution chart
        if 'BN_STATUS' in df.columns:
            status_counts = df['BN_STATUS'].value_counts()
            
            fig = go.Figure(data=[
                go.Bar(
                    x=status_counts.index,
                    y=status_counts.values,
                    marker_color='lightblue',
                    text=status_counts.values,
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                title="Business Names by Status",
                xaxis_title="Status",
                yaxis_title="Count",
                template="plotly_white"
            )
            
            # Save to temporary file and open in browser
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                plot(fig, filename=f.name, auto_open=False)
                console.print(f"[green]Chart saved to: {f.name}[/green]")
                webbrowser.open(f.name)
    
    def display_histogram(self, df: pd.DataFrame):
        """Display registration date histogram using Plotly"""
        if df.empty or 'BN_REG_DT' not in df.columns:
            console.print("[yellow]No date data available for histogram[/yellow]")
            return
        
        # Filter out null dates
        date_data = df['BN_REG_DT'].dropna()
        
        if len(date_data) == 0:
            console.print("[yellow]No valid registration dates found[/yellow]")
            return
        
        # Create histogram using Plotly
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=date_data,
            nbinsx=50,
            name='Registrations',
            marker_color='skyblue',
            opacity=0.7
        ))
        
        fig.update_layout(
            title='Business Name Registrations Over Time',
            xaxis_title='Registration Date',
            yaxis_title='Number of Registrations',
            template="plotly_white",
            font=dict(size=12)
        )
        
        # Save and display
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            plot(fig, filename=f.name, auto_open=False)
            console.print(f"[green]Histogram saved to: {f.name}[/green]")
            webbrowser.open(f.name)

# CLI Command Definitions
@click.group()
@click.pass_context
def cli(ctx):
    """
    Australian Business Names Register CLI Tool
    
    A comprehensive command-line utility for exploring and analyzing
    business names data with intelligent similarity matching and filtering.
    
    Examples:
    \b
    # Browse all businesses
    python cli.py search
    
    # Find businesses similar to "Jones" with bar chart
    python cli.py search "Jones" --display barchart
    
    # Show match distribution as pie chart
    python cli.py search "Smith" --display piechart
    """
    ctx.ensure_object(dict)
    ctx.obj['cli'] = BusinessNamesCLI()

@cli.command()
@click.argument('search_term', required=False)
@click.option('--status', '-s', help='Filter by business status (e.g., "Registered", "Cancelled")')
@click.option('--date-from', '-d', help='Filter registrations from date (YYYY-MM-DD)')
@click.option('--state', '-st', help='Filter by state/territory')
@click.option('--display', '-v', 
              type=click.Choice(['table', 'barchart', 'piechart', 'histogram', 'wordcloud', 'chart']), 
              default='table',
              help='Display format: table, barchart, piechart, histogram, wordcloud, chart')
@click.option('--limit', '-l', default=50, help='Maximum number of results to display')
@click.option('--threshold', '-t', default=50, help='Minimum similarity threshold (0-100)')
@click.option('--exact-only', is_flag=True, help='Show only exact matches, no similarity search')
@click.option('--no-cache', is_flag=True, help='Skip cache and fetch fresh data')
@click.pass_context
def search(ctx, search_term, status, date_from, state, display, limit, threshold, exact_only, no_cache):
    """
    Search business names with intelligent similarity matching by default
    
    If no search term is provided, shows all records with applied filters.
    If a search term is provided, performs similarity matching by default.
    
    FILTERING PARAMETERS:
    \b
    --status: Filter by business registration status
    --date-from: Filter by registration date (from specified date onwards)
    --state: Filter by state/territory (if available in data)
    
    VISUALIZATION OPTIONS:
    \b
    --display table: Rich formatted table (default)
    --display barchart: Horizontal bar chart showing top matches with similarity scores
    --display piechart: Pie chart showing match type distribution
    --display histogram: Histogram of similarity score distribution
    --display wordcloud: Word cloud of business names
    --display chart: Status distribution chart
    
    Examples:
    \b
    # Find businesses similar to "Jones" with bar chart
    python cli.py search "Jones" --display barchart
    
    # Show match distribution as pie chart
    python cli.py search "Smith" --display piechart
    
    # Generate word cloud of matching names
    python cli.py search "Consulting" --display wordcloud
    
    # Show similarity score distribution
    python cli.py search "Services" --display histogram
    """
    cli_instance = ctx.obj['cli']
    
    # Fetch ALL available data (no limit)
    df = cli_instance.fetch_data(limit=None, use_cache=not no_cache)
    
    # Apply filters first
    filtered_df = cli_instance.apply_filters(df, status, date_from, state)
    
    # If search term provided, perform similarity search
    if search_term:
        if exact_only:
            # Exact matches only
            result_df = filtered_df[
                filtered_df['BN_NAME'].str.upper() == search_term.upper()
            ].copy()
            if len(result_df) > 0:
                result_df['similarity_score'] = 100.0
                result_df['match_type'] = 'Exact'
            console.print(f"[blue]Exact matches for '{search_term}'[/blue]")
        else:
            # Default similarity search
            result_df = cli_instance.similarity_search(filtered_df, search_term, limit, threshold)
            console.print(Panel(
                f"[bold]Search Results for: '{search_term}'[/bold]",
                style="blue"
            ))
        
        # Display similarity results
        if result_df.empty:
            console.print(f"[yellow]No matches found for '{search_term}'[/yellow]")
            return
        
        if display == 'table':
            cli_instance.display_table(result_df, similarity_search=True)
        elif display == 'barchart':
            cli_instance.display_search_barchart(result_df, search_term)
        elif display == 'piechart':
            cli_instance.display_search_piechart(result_df, search_term)
        elif display == 'histogram':
            cli_instance.display_search_histogram(result_df, search_term)
        elif display == 'wordcloud':
            cli_instance.display_wordcloud(result_df, search_term)
        elif display == 'chart':
            cli_instance.display_chart(result_df)
    else:
        # No search term - show filtered browse results
        console.print(Panel("[bold]Browse Business Names[/bold]", style="green"))
        
        # Limit display results for browsing
        display_df = filtered_df.head(limit)
        
        if display == 'table':
            cli_instance.display_table(display_df)
        elif display in ['barchart', 'piechart', 'wordcloud']:
            console.print("[yellow]Bar chart, pie chart, and word cloud are only available for search results[/yellow]")
            cli_instance.display_table(display_df)
        elif display == 'chart':
            cli_instance.display_chart(display_df)
        elif display == 'histogram':
            cli_instance.display_histogram(display_df)
        
        if len(filtered_df) > limit:
            console.print(f"[yellow]Showing first {limit} of {len(filtered_df)} records. Use --limit to see more.[/yellow]")

@cli.command()
@click.option('--pattern', '-p', help='Search pattern to look for in business names')
@click.option('--limit', '-l', default=20, help='Number of results to show')
@click.option('--no-cache', is_flag=True, help='Skip cache and fetch fresh data')
@click.pass_context
def explore(ctx, pattern, limit, no_cache):
    """
    Explore the dataset to see what business names are available
    
    Examples:
    \b
    # Show random sample of business names
    python cli.py explore
    
    # Look for names containing "PTY"
    python cli.py explore --pattern "PTY" --limit 10
    
    # Look for names containing "CONSULTING"
    python cli.py explore --pattern "CONSULTING" --limit 15
    """
    cli_instance = ctx.obj['cli']
    
    # Fetch all data
    df = cli_instance.fetch_data(limit=None, use_cache=not no_cache)
    
    if pattern:
        # Filter by pattern
        filtered_df = df[
            df['BN_NAME'].str.contains(pattern, case=False, na=False)
        ]
        console.print(f"[blue]Found {len(filtered_df)} names containing '{pattern}'[/blue]")
        display_df = filtered_df.head(limit)
    else:
        # Show random sample
        display_df = df.sample(min(limit, len(df)))
        console.print(f"[blue]Random sample of {len(display_df)} business names[/blue]")
    
    # Display results
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Business Name", style="cyan", width=60)
    table.add_column("Status", style="green")
    
    for _, row in display_df.iterrows():
        name = str(row.get('BN_NAME', 'N/A'))[:60]  # Truncate long names
        status = str(row.get('BN_STATUS', 'N/A'))
        table.add_row(name, status)
    
    console.print(table)

@cli.command()
@click.option('--no-cache', is_flag=True, help='Skip cache and fetch fresh data')
@click.pass_context
def stats(ctx, no_cache):
    """Display comprehensive dataset statistics and summary information"""
    cli_instance = ctx.obj['cli']
    
    # Fetch all data
    df = cli_instance.fetch_data(limit=None, use_cache=not no_cache)
    
    # Display statistics
    console.print(Panel("[bold]Dataset Statistics[/bold]", style="green"))
    
    stats_table = Table(show_header=True, header_style="bold blue")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Total Records", f"{len(df):,}")
    stats_table.add_row("Unique Business Names", f"{df['BN_NAME'].nunique():,}")
    
    if 'BN_STATUS' in df.columns:
        stats_table.add_row("Most Common Status", df['BN_STATUS'].mode().iloc[0])
        stats_table.add_row("Status Categories", str(df['BN_STATUS'].nunique()))
    
    if 'BN_REG_DT' in df.columns:
        valid_dates = df['BN_REG_DT'].dropna()
        if len(valid_dates) > 0:
            stats_table.add_row("Earliest Registration", valid_dates.min().strftime('%Y-%m-%d'))
            stats_table.add_row("Latest Registration", valid_dates.max().strftime('%Y-%m-%d'))
    
    console.print(stats_table)
    
    # Status distribution
    if 'BN_STATUS' in df.columns:
        console.print("\n[bold]Status Distribution:[/bold]")
        status_counts = df['BN_STATUS'].value_counts()
        for status, count in status_counts.head(10).items():
            percentage = (count / len(df)) * 100
            console.print(f"  {status}: {count:,} ({percentage:.1f}%)")

@cli.command()
@click.pass_context
def clear_cache(ctx):
    """Clear the data cache to force fresh API fetch"""
    cli_instance = ctx.obj['cli']
    
    if cli_instance.cache_file.exists():
        cli_instance.cache_file.unlink()
        console.print("[green]Cache cleared successfully[/green]")
    else:
        console.print("[yellow]No cache file found[/yellow]")

if __name__ == '__main__':
    cli()
