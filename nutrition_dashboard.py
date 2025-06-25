"""
Streamlit Nutrition Dashboard Integration

This module provides integration between the chatbot_app.py and the backend
nutrition agent's streamlit visualization components.
"""

import streamlit as st
import os
import sys

# Add backend directory to Python path
AGENTIC_FLOW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if AGENTIC_FLOW_DIR not in sys.path:
    sys.path.append(AGENTIC_FLOW_DIR)

# Import nutrition dashboard component from backend
try:
    from backend.agents.health_diet_agent.streamlit_viz import create_nutrition_dashboard_component
except ImportError as e:
    st.error(f"Failed to import nutrition dashboard component: {e}")
    st.error("Please ensure the backend is properly configured.")

    def create_nutrition_dashboard_component():
        def render_error(user_id='anonymous', days=30):
            st.error("Nutrition dashboard is not available. Please check the backend configuration.")
        return render_error


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
    st.markdown('<p class="nutrition-subheader">This dashboard displays your nutrition data based on your meal inputs and recipe queries from the backend.</p>', unsafe_allow_html=True)

    # Get the dashboard component and render it
    try:
        nutrition_dashboard = create_nutrition_dashboard_component()

        # Use the current user ID from session state, or default to 'anonymous'
        user_id = st.session_state.get('user_id', 'anonymous')

        # Render the dashboard with the user ID
        nutrition_dashboard(user_id=user_id)

    except Exception as e:
        st.error(f"Error loading nutrition dashboard: {str(e)}")
        st.info("Please ensure the backend is properly configured and the database is initialized.")

        # Show a fallback message
        st.markdown("""
        ### Dashboard Unavailable

        The nutrition dashboard requires:
        1. backend to be properly configured
        2. Database to be initialized
        3. Nutrition data to be available

        Please check the backend configuration and try again.
        """)
