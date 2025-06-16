"""
Streamlit Nutrition Dashboard Integration

This module provides integration between the chatbot_app.py and the nutrition agent's
streamlit visualization components.
"""

import streamlit as st
import os
import sys

# Add nutrition-agent directory to Python path
NUTRITION_AGENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nutrition-agent')
if NUTRITION_AGENT_DIR not in sys.path:
    sys.path.append(NUTRITION_AGENT_DIR)

# Import nutrition dashboard component
try:
    from nutrition_agent.streamlit_viz import create_nutrition_dashboard_component
except ImportError:
    from streamlit_viz import create_nutrition_dashboard_component


def render_nutrition_dashboard_page():
    """
    Render the nutrition dashboard page in the Streamlit app.
    This is called from the main chatbot_app.py file when the user
    navigates to the nutrition dashboard.
    """
    st.title("Nutrition Analytics Dashboard")
    st.markdown("""
    <style>
    .nutrition-header {
        font-size: 1.5rem;
        margin-bottom: 1rem;
        color: #333;
    }
    .nutrition-subheader {
        font-size: 1.1rem;
        margin-bottom: 1rem;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="nutrition-header">Track your nutrition trends over time</p>', unsafe_allow_html=True)
    st.markdown('<p class="nutrition-subheader">This dashboard displays your nutrition data based on your meal inputs and recipe queries.</p>', unsafe_allow_html=True)

    # Get the dashboard component and render it
    nutrition_dashboard = create_nutrition_dashboard_component()

    # Use the current user ID from session state, or default to 'anonymous'
    user_id = st.session_state.get('user_id', 'anonymous')

    # Render the dashboard with the user ID
    nutrition_dashboard(user_id=user_id)
