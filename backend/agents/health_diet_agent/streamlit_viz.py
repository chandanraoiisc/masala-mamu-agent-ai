"""
Streamlit Interactive Visualization for Nutrition Data

This module provides interactive Streamlit visualizations for nutrition data
that can be integrated with the main chatbot application.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
import agents.health_diet_agent.db as db
from agents.health_diet_agent.utils.logger import setup_logger

logger = setup_logger(__name__)

def load_nutrition_data(days=30, user_id='anonymous'):
    """
    Load nutrition data from the database for visualization.

    Args:
        days: Number of days to look back
        user_id: User identifier

    Returns:
        Pandas DataFrame with nutrition data
    """
    try:
        conn = sqlite3.connect(db.DB_FILE)

        # Query to get daily nutrition data
        query = """
        SELECT
            date(nq.timestamp) as date,
            SUM(nr.calories) as calories,
            SUM(nr.protein) as protein,
            SUM(nr.carbohydrates) as carbs,
            SUM(nr.fat) as fat,
            COUNT(*) as entries
        FROM nutrition_inquiries nq
        JOIN nutrition_records nr ON nq.id = nr.inquiry_id
        WHERE nq.user_id = ?
        AND nq.timestamp >= date('now', ?)
        GROUP BY date(nq.timestamp)
        ORDER BY date(nq.timestamp)
        """

        # Load data into DataFrame
        df = pd.read_sql_query(query, conn, params=(user_id, f'-{days} days'))

        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])

        # Fill in missing dates
        if not df.empty:
            date_range = pd.date_range(
                start=max(df['date'].min(), datetime.now() - timedelta(days=days)),
                end=datetime.now(),
                freq='D'
            )

            # Create a complete DataFrame with all dates
            complete_df = pd.DataFrame({'date': date_range})
            df = pd.merge(complete_df, df, on='date', how='left')
            df.fillna(0, inplace=True)

        conn.close()
        return df

    except Exception as e:
        logger.error(f"Error loading nutrition data: {str(e)}")
        return pd.DataFrame()

def create_macro_trends_plotly(df, show_daily_target=True, cal_target=2000, protein_target=50, carb_target=275, fat_target=55):
    """
    Create plotly figure for macro trends.

    Args:
        df: DataFrame with nutrition data
        show_daily_target: Whether to show daily target lines
        cal_target: Daily calorie target
        protein_target: Daily protein target
        carb_target: Daily carb target
        fat_target: Daily fat target

    Returns:
        Plotly figure object
    """
    if df.empty:
        return None

    # Create subplot figure
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=['Calories (kcal)', 'Protein (g)', 'Carbohydrates (g)', 'Fat (g)'],
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )

    # Colors for the traces
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']

    # Add traces for each macro
    macros = [
        ('calories', cal_target, 1, 1),
        ('protein', protein_target, 1, 2),
        ('carbs', carb_target, 2, 1),
        ('fat', fat_target, 2, 2)
    ]

    for i, (macro, target, row, col) in enumerate(macros):
        if macro in df.columns:
            # Add actual data line
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df[macro],
                    mode='lines+markers',
                    name=macro.capitalize(),
                    line=dict(color=colors[i], width=2),
                    marker=dict(size=4),
                    showlegend=False
                ),
                row=row, col=col
            )

            # Add target line if enabled
            if show_daily_target:
                fig.add_trace(
                    go.Scatter(
                        x=df['date'],
                        y=[target] * len(df),
                        mode='lines',
                        name=f'{macro.capitalize()} Target',
                        line=dict(color=colors[i], width=1, dash='dash'),
                        opacity=0.7,
                        showlegend=False
                    ),
                    row=row, col=col
                )

    # Update layout
    fig.update_layout(
        height=600,
        title_text="Macronutrient Trends Over Time",
        title_x=0.5,
        title_font_size=20,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    # Update x-axes
    for i in range(1, 5):
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            row=(i-1)//2 + 1,
            col=(i-1)%2 + 1
        )

    # Update y-axes
    for i in range(1, 5):
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            row=(i-1)//2 + 1,
            col=(i-1)%2 + 1
        )

    return fig

def create_macro_distribution_plotly(df):
    """
    Create plotly pie chart for macro distribution.

    Args:
        df: DataFrame with nutrition data

    Returns:
        Plotly figure object
    """
    if df.empty:
        return None

    # Calculate average daily macros
    avg_protein = df['protein'].mean()
    avg_carbs = df['carbs'].mean()
    avg_fat = df['fat'].mean()

    # Convert to calories (protein: 4 cal/g, carbs: 4 cal/g, fat: 9 cal/g)
    protein_cal = avg_protein * 4
    carbs_cal = avg_carbs * 4
    fat_cal = avg_fat * 9

    total_cal = protein_cal + carbs_cal + fat_cal

    if total_cal == 0:
        return None

    # Calculate percentages
    protein_pct = (protein_cal / total_cal) * 100
    carbs_pct = (carbs_cal / total_cal) * 100
    fat_pct = (fat_cal / total_cal) * 100

    fig = go.Figure(data=[go.Pie(
        labels=['Protein', 'Carbohydrates', 'Fat'],
        values=[protein_pct, carbs_pct, fat_pct],
        hole=.3,
        marker_colors=['#4ECDC4', '#45B7D1', '#96CEB4']
    )])

    fig.update_layout(
        title="Average Daily Macro Distribution",
        title_x=0.5,
        title_font_size=18,
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig

def create_weekly_summary_plotly(df):
    """
    Create weekly summary bar chart.

    Args:
        df: DataFrame with nutrition data

    Returns:
        Plotly figure object
    """
    if df.empty:
        return None

    # Calculate weekly averages
    avg_calories = df['calories'].mean()
    avg_protein = df['protein'].mean()
    avg_carbs = df['carbs'].mean()
    avg_fat = df['fat'].mean()

    # Create bar chart
    metrics = ['Calories', 'Protein', 'Carbs', 'Fat']
    values = [avg_calories, avg_protein, avg_carbs, avg_fat]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=metrics,
            y=values,
            marker_color=colors,
            text=[f"{v:.1f}" for v in values],
            textposition='auto'
        )
    )

    # Update layout
    fig.update_layout(
        title="Weekly Average Macro Intake",
        title_x=0.5,
        title_font_size=18,
        height=300,
        yaxis_title=None,
        xaxis_title=None,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig

def show_nutrition_dashboard(user_id='anonymous', days=30):
    """
    Render the nutrition dashboard with interactive Streamlit components.

    Args:
        user_id: User identifier
        days: Number of days to look back
    """
    # Load data
    df = load_nutrition_data(days=days, user_id=user_id)

    if df.empty:
        st.warning("No nutrition data available for this period. Start logging your meals to see trends!")
        return

    # Add filter for date range
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_days = st.slider(
            "Select timeframe:",
            min_value=7,
            max_value=90,
            value=days,
            step=7,
            help="Adjust to see nutrition data for different time periods"
        )

        if selected_days != days:
            df = load_nutrition_data(days=selected_days, user_id=user_id)

    with col2:
        # Show nutritional targets toggle
        show_targets = st.checkbox("Show targets", value=True)

    # Custom nutrition targets - collapsible section
    with st.expander("Customize Nutrition Targets"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            cal_target = st.number_input("Daily Calories (kcal)", value=2000, min_value=500, max_value=5000)
        with col2:
            protein_target = st.number_input("Daily Protein (g)", value=50, min_value=10, max_value=300)
        with col3:
            carb_target = st.number_input("Daily Carbs (g)", value=275, min_value=50, max_value=500)
        with col4:
            fat_target = st.number_input("Daily Fat (g)", value=55, min_value=10, max_value=200)

    # Show weekly summary metrics
    weekly_fig = create_weekly_summary_plotly(df)
    if weekly_fig:
        st.plotly_chart(weekly_fig, use_container_width=True)

    # Create tabs for different visualizations
    tab1, tab2 = st.tabs(["Macro Trends", "Macro Distribution"])

    with tab1:
        # Display macro trends chart
        trend_fig = create_macro_trends_plotly(
            df,
            show_daily_target=show_targets,
            cal_target=cal_target,
            protein_target=protein_target,
            carb_target=carb_target,
            fat_target=fat_target
        )
        if trend_fig:
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.info("Not enough data to display trends.")

    with tab2:
        # Display macro distribution chart
        dist_fig = create_macro_distribution_plotly(df)
        if dist_fig:
            st.plotly_chart(dist_fig, use_container_width=True)
        else:
            st.info("Not enough data to display distribution.")

    # Add download button for data
    st.download_button(
        label="Download nutrition data as CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name=f'nutrition_data_{datetime.now().strftime("%Y-%m-%d")}.csv',
        mime='text/csv',
    )

def create_nutrition_dashboard_component():
    """
    Create a Streamlit component for the nutrition dashboard that can be
    embedded in the chatbot app.

    Returns:
        A function that renders the nutrition dashboard
    """
    def render_nutrition_dashboard(user_id='anonymous', days=30):
        show_nutrition_dashboard(user_id=user_id, days=days)

    return render_nutrition_dashboard
