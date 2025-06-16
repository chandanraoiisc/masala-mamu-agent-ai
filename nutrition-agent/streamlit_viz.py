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
import db
from utils.logger import setup_logger

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
        subplot_titles=(
            'Daily Calorie Intake',
            'Daily Protein Intake',
            'Daily Carbohydrate Intake',
            'Daily Fat Intake'
        )
    )

    # Add traces for each macro
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['calories'],
            mode='lines+markers',
            name='Calories',
            line=dict(color='#FF9500', width=3),
            marker=dict(size=8)
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['protein'],
            mode='lines+markers',
            name='Protein',
            line=dict(color='#007AFF', width=3),
            marker=dict(size=8)
        ),
        row=1, col=2
    )

    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['carbs'],
            mode='lines+markers',
            name='Carbs',
            line=dict(color='#34C759', width=3),
            marker=dict(size=8)
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['fat'],
            mode='lines+markers',
            name='Fat',
            line=dict(color='#FF3B30', width=3),
            marker=dict(size=8)
        ),
        row=2, col=2
    )

    # Add daily target lines if enabled
    if show_daily_target:
        # Calorie target line
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=[cal_target] * len(df),
                mode='lines',
                name='Calorie Target',
                line=dict(color='#FF9500', width=1, dash='dash')
            ),
            row=1, col=1
        )

        # Protein target line
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=[protein_target] * len(df),
                mode='lines',
                name='Protein Target',
                line=dict(color='#007AFF', width=1, dash='dash')
            ),
            row=1, col=2
        )

        # Carb target line
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=[carb_target] * len(df),
                mode='lines',
                name='Carb Target',
                line=dict(color='#34C759', width=1, dash='dash')
            ),
            row=2, col=1
        )

        # Fat target line
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=[fat_target] * len(df),
                mode='lines',
                name='Fat Target',
                line=dict(color='#FF3B30', width=1, dash='dash')
            ),
            row=2, col=2
        )

    # Update layout
    fig.update_layout(
        height=600,
        showlegend=False,
        title_text="Nutrition Macro Trends",
        title_x=0.5,
        title_font_size=20,
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(211, 211, 211, 0.3)',
        tickformat='%b %d',
        tickangle=-45
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(211, 211, 211, 0.3)',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='rgba(211, 211, 211, 0.3)'
    )

    return fig

def create_macro_distribution_plotly(df):
    """
    Create plotly pie charts for macro distribution.

    Args:
        df: DataFrame with nutrition data

    Returns:
        Plotly figure object
    """
    if df.empty:
        return None

    # Calculate totals
    total_protein = df['protein'].sum()
    total_carbs = df['carbs'].sum()
    total_fat = df['fat'].sum()

    # Calculate calories from each macro
    protein_cals = total_protein * 4  # 4 calories per gram
    carb_cals = total_carbs * 4       # 4 calories per gram
    fat_cals = total_fat * 9          # 9 calories per gram

    # Create figure
    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{'type': 'domain'}, {'type': 'domain'}]],
        subplot_titles=('Macronutrient Distribution by Weight', 'Macronutrient Distribution by Calories')
    )

    # Colors for macro types
    colors = ['#007AFF', '#34C759', '#FF3B30']

    # Add weight distribution pie chart
    fig.add_trace(
        go.Pie(
            labels=['Protein', 'Carbs', 'Fat'],
            values=[total_protein, total_carbs, total_fat],
            name="By Weight",
            marker_colors=colors,
            textinfo='percent+label',
            hole=0.4,
            pull=[0.05, 0, 0],
            domain={'column': 0}
        ),
        row=1, col=1
    )

    # Add calorie distribution pie chart
    fig.add_trace(
        go.Pie(
            labels=['Protein', 'Carbs', 'Fat'],
            values=[protein_cals, carb_cals, fat_cals],
            name="By Calories",
            marker_colors=colors,
            textinfo='percent+label',
            hole=0.4,
            pull=[0.05, 0, 0],
            domain={'column': 1}
        ),
        row=1, col=2
    )

    # Update layout
    fig.update_layout(
        title_text="Nutrition Distribution Analysis",
        title_x=0.5,
        title_font_size=20,
        height=400,
        showlegend=False,
        margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        annotations=[
            dict(text='By Weight (g)', x=0.16, y=-0.1, font_size=12, showarrow=False),
            dict(text='By Calories (kcal)', x=0.84, y=-0.1, font_size=12, showarrow=False)
        ]
    )

    return fig

def create_weekly_summary_plotly(df):
    """
    Create a weekly summary bar chart for average macro intakes.

    Args:
        df: DataFrame with nutrition data

    Returns:
        Plotly figure object
    """
    if df.empty or len(df) < 7:
        return None

    # Get the last 7 days of data
    last_7_days = df.tail(7)

    # Calculate averages
    avg_calories = last_7_days['calories'].mean()
    avg_protein = last_7_days['protein'].mean()
    avg_carbs = last_7_days['carbs'].mean()
    avg_fat = last_7_days['fat'].mean()

    # Create metrics
    metrics = ['Calories (kcal)', 'Protein (g)', 'Carbs (g)', 'Fat (g)']
    values = [avg_calories, avg_protein, avg_carbs, avg_fat]
    colors = ['#FF9500', '#007AFF', '#34C759', '#FF3B30']

    # Create bar chart
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


if __name__ == "__main__":
    st.set_page_config(
        page_title="Nutrition Dashboard",
        page_icon="🥗",
        layout="wide"
    )

    st.title("Nutrition Analytics Dashboard")
    st.subheader("Track your nutrition trends over time")

    show_nutrition_dashboard()
