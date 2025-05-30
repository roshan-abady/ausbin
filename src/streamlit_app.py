# streamlit_app.py
import streamlit as st

# Configure Streamlit page (must be the first Streamlit command)
st.set_page_config(
    page_title="Australian Business Names Explorer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import other libraries
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import tempfile
from pathlib import Path
import time
from collections import Counter
import re
from wordcloud import WordCloud
import sys
import os

# Fix the import to work both when running from project root and from src directory
# Add parent directory to path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.business_names_api import BusinessNamesAPI, BusinessNamesAPIError

"""
Streamlit web application for the Australian Business Names Explorer.

Author: Roshan Abady
Email: roshanabady@gmail.com
"""

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .search-results {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class StreamlitBusinessNamesApp:
    """Streamlit web application for Australian Business Names Register"""
    
    def __init__(self):
        self.api = BusinessNamesAPI()
        self.cache_file = Path("streamlit_data_cache.pkl")
        
        # Initialize session state
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'cached_data' not in st.session_state:
            st.session_state.cached_data = None
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def fetch_data(_self, limit: Optional[int] = None) -> pd.DataFrame:
        """Fetch and cache business names data using Streamlit caching"""
        try:
            with st.spinner("Fetching business names data from API..."):
                result = _self.api.search_business_names(limit=limit)
                records = result.get('result', {}).get('records', [])
                
                if not records:
                    st.error("No data retrieved from API")
                    return pd.DataFrame()
                
                df = pd.DataFrame(records)
                
                # Convert date columns
                date_columns = ['BN_REG_DT', 'BN_RENEWAL_DT', 'BN_CANCEL_DT']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)

                
                st.success(f"Successfully loaded {len(df):,} business records")
                return df
                
        except BusinessNamesAPIError as e:
            st.error(f"API Error: {e}")
            return pd.DataFrame()
    
    def apply_filters(self, df: pd.DataFrame, status_filter: str, date_from: str, state_filter: str) -> pd.DataFrame:
        """Apply filtering parameters to the dataset"""
        filtered_df = df.copy()
        
        if status_filter and status_filter != "All":
            filtered_df = filtered_df[
                filtered_df['BN_STATUS'].str.contains(status_filter, case=False, na=False)
            ]
        
        if date_from:
            try:
                from_date = pd.to_datetime(date_from)
                filtered_df = filtered_df[filtered_df['BN_REG_DT'] >= from_date]
            except ValueError:
                st.warning(f"Invalid date format '{date_from}'. Expected YYYY-MM-DD")
        
        if state_filter and state_filter != "All" and 'BN_STATE' in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df['BN_STATE'].str.contains(state_filter, case=False, na=False)
            ]
        
        return filtered_df
    
    def similarity_search(self, df: pd.DataFrame, search_term: str, threshold: int = 50) -> pd.DataFrame:
        """Perform similarity matching on business names"""
        if 'BN_NAME' not in df.columns or df.empty:
            return pd.DataFrame()
        
        from fuzzywuzzy import fuzz
        
        search_term_clean = search_term.upper().strip()
        business_names = df['BN_NAME'].fillna('').astype(str)
        
        # Find exact matches
        exact_matches = df[business_names.str.upper() == search_term_clean].copy()
        if len(exact_matches) > 0:
            exact_matches['similarity_score'] = 100.0
            exact_matches['match_type'] = 'Exact'
        
        # Find partial matches
        partial_matches = df[
            (business_names.str.upper() != search_term_clean) & 
            (business_names.str.upper().str.contains(search_term_clean, na=False))
        ].copy()
        
        if len(partial_matches) > 0:
            partial_matches['similarity_score'] = 95.0
            partial_matches['match_type'] = 'Contains'
        
        # Find fuzzy matches
        remaining_df = df[
            (~business_names.str.upper().str.contains(search_term_clean, na=False)) &
            (business_names.str.upper() != search_term_clean)
        ].copy()
        
        fuzzy_matches = pd.DataFrame()
        
        if len(remaining_df) > 0:
            # Limit for performance
            search_sample = remaining_df.head(5000)
            
            with st.spinner("Computing similarity scores..."):
                similarity_scores = []
                valid_indices = []
                
                progress_bar = st.progress(0)
                total = len(search_sample)
                
                for idx, name in enumerate(search_sample['BN_NAME']):
                    if pd.notna(name) and str(name).strip():
                        score = fuzz.ratio(search_term_clean, str(name).upper())
                        if score >= threshold:
                            similarity_scores.append(score)
                            valid_indices.append(idx)
                    
                    # Update progress
                    if idx % 100 == 0:
                        progress_bar.progress((idx + 1) / total)
                
                progress_bar.empty()
                
                if similarity_scores:
                    fuzzy_matches = search_sample.iloc[valid_indices].copy()
                    fuzzy_matches['similarity_score'] = similarity_scores
                    fuzzy_matches['match_type'] = 'Fuzzy'
        
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
            )
            return all_matches
        
        return pd.DataFrame()
    
    def create_search_barchart(self, df: pd.DataFrame, search_term: str):
        """Create bar chart for search results"""
        if df.empty:
            return None
        
        top_matches = df.head(20)
        business_names = [name[:40] + "..." if len(name) > 40 else name 
                         for name in top_matches['BN_NAME']]
        
        fig = go.Figure()
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
                    textposition='inside'
                ))
        
        fig.update_layout(
            title=f"Top Business Name Matches for '{search_term}'",
            xaxis_title="Similarity Score (%)",
            yaxis_title="Business Names",
            height=max(600, len(top_matches) * 30),
            showlegend=True
        )
        
        return fig
    
    def create_piechart(self, df: pd.DataFrame, search_term: str):
        """Create pie chart for match type distribution"""
        if df.empty:
            st.info("No data available for pie chart")
            return None
            
        if 'match_type' not in df.columns:
            st.info("Match type information is not available for this search")
            return None
        
        match_counts = df['match_type'].value_counts()
        
        # Debug information
        st.write(f"Match type distribution: {dict(match_counts)}")
        
        # Only 1 match type, not very informative as a pie chart
        if len(match_counts) <= 1:
            st.info(f"All results are of type '{match_counts.index[0]}' - pie chart would not be informative")
            
            # Create a single-segment pie chart with a note
            fig = go.Figure(data=[go.Pie(
                labels=match_counts.index,
                values=match_counts.values,
                hole=0.3,
                textinfo='label+percent+value'
            )])
            
            fig.update_layout(
                title=f"All {len(df)} matches are '{match_counts.index[0]}' type"
            )
            
            return fig
        
        # Normal case - multiple match types
        fig = go.Figure(data=[go.Pie(
            labels=match_counts.index,
            values=match_counts.values,
            hole=0.3,
            textinfo='label+percent+value'
        )])
        
        fig.update_layout(
            title=f"Match Type Distribution for '{search_term}' ({len(df)} total matches)"
        )
        
        return fig
    
    def create_histogram(self, df: pd.DataFrame, search_term: str = None):
        """Create histogram based on context"""
        if df.empty:
            return None
        
        if search_term and 'similarity_score' in df.columns:
            # Similarity score histogram
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=df['similarity_score'],
                nbinsx=20,
                name='Similarity Scores',
                marker_color='lightblue'
            ))
            fig.add_vline(x=50, line_dash="dash", line_color="red", 
                         annotation_text="Minimum Threshold")
            fig.update_layout(
                title=f"Similarity Score Distribution for '{search_term}'",
                xaxis_title="Similarity Score (%)",
                yaxis_title="Number of Matches"
            )
        else:
            # Registration date histogram
            if 'BN_REG_DT' not in df.columns:
                return None
            
            date_data = df['BN_REG_DT'].dropna()
            if len(date_data) == 0:
                return None
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=date_data,
                nbinsx=50,
                name='Registrations',
                marker_color='skyblue'
            ))
            fig.update_layout(
                title='Business Name Registrations Over Time',
                xaxis_title='Registration Date',
                yaxis_title='Number of Registrations'
            )
        
        return fig
    
    def create_wordcloud(self, df: pd.DataFrame, search_term: str):
        """Create word cloud from business names"""
        if df.empty:
            st.info("No data available for word cloud generation")
            return None
        
        try:
            # Debug information
            st.write(f"Generating word cloud from {len(df)} business names")
            
            text = ' '.join(df['BN_NAME'].fillna('').astype(str))
            original_text_length = len(text)
            
            if original_text_length < 10:
                st.warning("Insufficient text data for word cloud generation")
                return None
                
            # Clean text
            common_words = ['PTY', 'LTD', 'LIMITED', 'COMPANY', 'CORP', 'INC', 'LLC', 
                           'SERVICES', 'GROUP', 'HOLDINGS']
                           
            # Only remove search term if it's not too short (to avoid removing common short words)
            if search_term and len(search_term) > 2:
                common_words.append(search_term.upper())
            
            for word in common_words:
                text = re.sub(r'\b' + re.escape(word) + r'\b', '', text, flags=re.IGNORECASE)
            
            cleaned_text_length = len(text.strip())
            
            # Check if we have enough text left after cleaning
            if cleaned_text_length < 10:
                st.warning("After removing common business terms, insufficient text remains for word cloud generation")
                return None
                
            st.write(f"Original text: {original_text_length} chars, Cleaned: {cleaned_text_length} chars")
            
            wordcloud = WordCloud(
                width=800, 
                height=400, 
                background_color='white',
                colormap='viridis',
                max_words=100,
                min_word_length=3,  # Ignore very short words
                collocations=False   # Avoid repeated word pairs
            ).generate(text)
            
            # Convert to plotly figure
            fig = go.Figure()
            fig.add_layout_image(
                dict(
                    source=wordcloud.to_image(),
                    xref="paper", yref="paper",
                    x=0, y=1, sizex=1, sizey=1,
                    xanchor="left", yanchor="top"
                )
            )
            
            fig.update_layout(
                title=f"Word Cloud for Business Names matching '{search_term}'",
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
            )
            
            return fig
            
        except ImportError:
            st.warning("WordCloud package not installed. Install with: pip install wordcloud")
            return None
        except Exception as e:
            st.error(f"Error generating word cloud: {e}")
            import traceback
            st.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def run(self):
        """Main Streamlit app"""
        # Header
        st.markdown('<h1 class="main-header">🏢 Australian Business Names Explorer</h1>', 
                   unsafe_allow_html=True)
        
        st.markdown("""
        **Explore and analyze business names from the Australian Business Names Register**
        
        This tool provides intelligent similarity matching, filtering, and visualization capabilities 
        for business intelligence and data exploration workflows.
        """)
        
        # Sidebar for controls
        st.sidebar.header("🔧 Search & Filter Controls")
        
        # Data loading section
        st.sidebar.subheader("📊 Data Loading")
        data_limit = st.sidebar.selectbox(
            "Data Limit",
            options=[1000, 5000, 10000, None],
            format_func=lambda x: "All Available" if x is None else f"{x:,} records",
            index=2
        )
        
        if st.sidebar.button("🔄 Load/Refresh Data"):
            st.session_state.cached_data = None
            st.rerun()
        
        # Load data
        df = self.fetch_data(data_limit)
        
        if df.empty:
            st.error("No data available. Please check your API connection.")
            return
        
        # Display data statistics
        st.sidebar.subheader("📈 Dataset Statistics")
        st.sidebar.metric("Total Records", f"{len(df):,}")
        st.sidebar.metric("Unique Business Names", f"{df['BN_NAME'].nunique():,}")
        
        if 'BN_STATUS' in df.columns:
            most_common_status = df['BN_STATUS'].mode().iloc[0]
            st.sidebar.metric("Most Common Status", most_common_status)
        
        # Search section
        st.sidebar.subheader("🔍 Search")
        search_term = st.sidebar.text_input(
            "Business Name Search",
            placeholder="Enter business name (e.g., 'Jones', 'ACME')",
            help="Leave empty to browse all records"
        )
        
        # Filter controls
        st.sidebar.subheader("🎛️ Filters")
        
        # Status filter
        status_options = ["All"] + sorted(df['BN_STATUS'].dropna().unique().tolist())
        status_filter = st.sidebar.selectbox("Business Status", status_options)
        
        # Date filter
        date_from = st.sidebar.date_input(
            "Registration Date From",
            value=None,
            help="Filter businesses registered from this date onwards"
        )
        
        # State filter (if available)
        state_filter = "All"
        if 'BN_STATE' in df.columns:
            state_options = ["All"] + sorted(df['BN_STATE'].dropna().unique().tolist())
            state_filter = st.sidebar.selectbox("State/Territory", state_options)
        
        # Search parameters
        if search_term:
            st.sidebar.subheader("⚙️ Search Parameters")
            threshold = st.sidebar.slider(
                "Similarity Threshold (%)",
                min_value=0,
                max_value=100,
                value=50,
                help="Minimum similarity score for fuzzy matches"
            )
            
            max_results = st.sidebar.slider(
                "Maximum Results",
                min_value=10,
                max_value=200,
                value=50
            )
            
            exact_only = st.sidebar.checkbox(
                "Exact Matches Only",
                help="Show only exact matches, no similarity search"
            )
        
        # Apply filters
        date_from_str = date_from.strftime('%Y-%m-%d') if date_from else ""
        filtered_df = self.apply_filters(df, status_filter, date_from_str, state_filter)
        
        # Main content area
        if search_term:
            # Search mode
            st.header(f"🔍 Search Results for: '{search_term}'")
            
            if exact_only:
                # Exact matches only
                result_df = filtered_df[
                    filtered_df['BN_NAME'].str.upper() == search_term.upper()
                ].copy()
                if len(result_df) > 0:
                    result_df['similarity_score'] = 100.0
                    result_df['match_type'] = 'Exact'
                st.info("Showing exact matches only")
            else:
                # Similarity search
                result_df = self.similarity_search(filtered_df, search_term, threshold)
                result_df = result_df.head(max_results)
            
            if result_df.empty:
                st.warning(f"No matches found for '{search_term}' with the current filters.")
                return
            
            # Display results summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Matches", len(result_df))
            with col2:
                if 'match_type' in result_df.columns:
                    exact_count = len(result_df[result_df['match_type'] == 'Exact'])
                    st.metric("Exact Matches", exact_count)
            with col3:
                if 'match_type' in result_df.columns:
                    partial_count = len(result_df[result_df['match_type'] == 'Contains'])
                    st.metric("Partial Matches", partial_count)
            with col4:
                if 'match_type' in result_df.columns:
                    fuzzy_count = len(result_df[result_df['match_type'] == 'Fuzzy'])
                    st.metric("Fuzzy Matches", fuzzy_count)
            
            # Visualization tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Table", "📈 Bar Chart", "🥧 Pie Chart", "📊 Histogram", "☁️ Word Cloud"])
            
            with tab1:
                st.subheader("Search Results Table")
                display_columns = ['BN_NAME', 'BN_STATUS', 'BN_REG_DT']
                if 'similarity_score' in result_df.columns:
                    display_columns.extend(['similarity_score', 'match_type'])
                
                # Format the dataframe for display
                display_df = result_df[display_columns].copy()
                if 'BN_REG_DT' in display_df.columns:
                    display_df['BN_REG_DT'] = display_df['BN_REG_DT'].dt.strftime('%Y-%m-%d')
                if 'similarity_score' in display_df.columns:
                    display_df['similarity_score'] = display_df['similarity_score'].round(1)
                
                st.dataframe(display_df, use_container_width=True)
            
            with tab2:
                st.subheader("Top Matches Bar Chart")
                fig = self.create_search_barchart(result_df, search_term)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for bar chart")
            
            with tab3:
                st.subheader("Match Type Distribution")
                fig = self.create_piechart(result_df, search_term)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No match type data available for pie chart")
            
            with tab4:
                st.subheader("Similarity Score Distribution")
                fig = self.create_histogram(result_df, search_term)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No similarity data available for histogram")
            
            with tab5:
                st.subheader("Business Names Word Cloud")
                fig = self.create_wordcloud(result_df, search_term)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Word cloud not available")
        
        else:
            # Browse mode
            st.header("📋 Browse Business Names")
            
            # Display filtered results summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Filtered Records", f"{len(filtered_df):,}")
            with col2:
                if 'BN_STATUS' in filtered_df.columns:
                    status_counts = filtered_df['BN_STATUS'].value_counts()
                    if len(status_counts) > 0:
                        st.metric("Most Common Status", status_counts.index[0])
            with col3:
                if 'BN_REG_DT' in filtered_df.columns:
                    valid_dates = filtered_df['BN_REG_DT'].dropna()
                    if len(valid_dates) > 0:
                        latest_date = valid_dates.max().strftime('%Y-%m-%d')
                        st.metric("Latest Registration", latest_date)
            
            # Browse visualization tabs
            tab1, tab2, tab3 = st.tabs(["📊 Table", "📈 Status Chart", "📊 Registration Histogram"])
            
            with tab1:
                st.subheader("Business Names Table")
                display_limit = st.selectbox("Records to Display", [50, 100, 200, 500], index=0)
                
                display_df = filtered_df.head(display_limit)[['BN_NAME', 'BN_STATUS', 'BN_REG_DT']].copy()
                if 'BN_REG_DT' in display_df.columns:
                    display_df['BN_REG_DT'] = display_df['BN_REG_DT'].dt.strftime('%Y-%m-%d')
                
                st.dataframe(display_df, use_container_width=True)
                
                if len(filtered_df) > display_limit:
                    st.info(f"Showing first {display_limit:,} of {len(filtered_df):,} records")
            
            with tab2:
                st.subheader("Business Status Distribution")
                if 'BN_STATUS' in filtered_df.columns:
                    status_counts = filtered_df['BN_STATUS'].value_counts()
                    fig = px.bar(
                        x=status_counts.values,
                        y=status_counts.index,
                        orientation='h',
                        title="Business Names by Status"
                    )
                    fig.update_layout(
                        xaxis_title="Count",
                        yaxis_title="Status"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No status data available")
            
            with tab3:
                st.subheader("Registration Date Distribution")
                fig = self.create_histogram(filtered_df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No registration date data available")
        
        # Footer
        st.markdown("---")
        st.markdown("""
        **About this app:** This tool uses the Australian Business Names Register API to provide 
        intelligent business name search and analysis capabilities. Built with Streamlit and Plotly 
        for interactive data exploration.
        """)

# Run the app
if __name__ == "__main__":
    app = StreamlitBusinessNamesApp()
    app.run()
