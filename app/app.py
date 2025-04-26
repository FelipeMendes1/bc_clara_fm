import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import tempfile
import os
import base64
import sys

sys.path.append('/Users/Felipe/Documents/bc_clara_fm/EcommerceFunnel/src')
sys.path.append('/Users/Felipe/Documents/bc_clara_fm/EcommerceFunnel/reports')

from utils import load_data, clean_data
from analysis import perform_funnel_analysis, generate_insights, generate_recommendations
from visualization import (
    create_funnel_chart, create_conversion_rate_chart, create_drop_off_chart,
    create_segment_comparison_chart, create_stage_comparison_by_segment,
    create_new_vs_existing_comparison
)
from presentation import create_presentation


st.set_page_config(
    page_title="E-commerce Funnel Analysis",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

def download_link(object_to_download, download_filename, download_link_text):
    if isinstance(object_to_download, bytes):
        b64 = base64.b64encode(object_to_download).decode()
    else:
        b64 = base64.b64encode(object_to_download.getvalue()).decode()
        
    dl_link = f'<a href="data:application/octet-stream;base64,{b64}" download="{download_filename}">{download_link_text}</a>'
    return dl_link

# Main app
def main():
    st.title("🛒 E-commerce Funnel Analysis")
    st.markdown("### Identifying Conversion Issues and Providing Strategic Recommendations")
    
    # Load data
    with st.spinner("Loading data..."):
        home_df, search_df, payment_df, confirmation_df, user_df = load_data()
        
        if home_df is None:
            st.error("Failed to load data. Please check file paths and formats.")
            return
        
        # Clean data
        home_df, search_df, payment_df, confirmation_df, user_df = clean_data(
            home_df, search_df, payment_df, confirmation_df, user_df
        )
        
        # Perform analysis
        analysis_results = perform_funnel_analysis(
            home_df, search_df, payment_df, confirmation_df, user_df
        )
        
        # Generate insights and recommendations
        insights = generate_insights(analysis_results)
        recommendations = generate_recommendations(analysis_results)
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Funnel Overview", 
        "👥 User Segments", 
        "🔍 New vs Existing Users", 
        "💡 Insights", 
        "📝 Recommendations"
    ])
    
    # Tab 1: Funnel Overview
    with tab1:
        st.header("Conversion Funnel Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Funnel chart
            funnel_fig = create_funnel_chart(analysis_results['overall']['funnel'])
            st.plotly_chart(funnel_fig, use_container_width=True)
            
            # Display conversion rates in a table
            st.subheader("Conversion Rates")
            funnel_df = analysis_results['overall']['funnel']
            st.dataframe(
                funnel_df[['Stage', 'Users', 'Conversion_Rate']],
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            # Conversion rate chart
            conversion_fig = create_conversion_rate_chart(analysis_results['overall']['funnel'])
            st.plotly_chart(conversion_fig, use_container_width=True)
            
            # Drop-off chart
            drop_off_fig = create_drop_off_chart(analysis_results['overall']['drop_off'])
            st.plotly_chart(drop_off_fig, use_container_width=True)
        
        # Overall stats
        st.subheader("Summary Statistics")
        
        overall_metrics_col1, overall_metrics_col2, overall_metrics_col3, overall_metrics_col4 = st.columns(4)
        
        with overall_metrics_col1:
            st.metric(
                "Total Users", 
                f"{analysis_results['user_counts']['total']:,}",
                delta=None
            )
        
        with overall_metrics_col2:
            st.metric(
                "Overall Conversion Rate", 
                f"{analysis_results['overall']['conversion_rate']}%",
                delta=None
            )
        
        with overall_metrics_col3:

            drop_off = analysis_results['overall']['drop_off']
            max_drop_idx = drop_off['Drop_Off_Percentage'].idxmax()
            max_drop_stage = drop_off.loc[max_drop_idx, 'Stage']
            st.metric(
                "Biggest Drop-off Point", 
                f"{max_drop_stage}",
                delta=f"-{drop_off.loc[max_drop_idx, 'Drop_Off_Percentage']}%",
                delta_color="inverse"
            )
        
        with overall_metrics_col4:
            
            funnel_df = analysis_results['overall']['funnel']
            current_users = funnel_df.loc[3, 'Users']  
            
            
            conversion_rates = funnel_df['Conversion_Rate'].values[1:]  
            worst_step_idx = np.argmin(conversion_rates) + 1  
            
            
            improved_rate = min(funnel_df.loc[worst_step_idx, 'Conversion_Rate'] + 10, 100)
            improvement_factor = improved_rate / funnel_df.loc[worst_step_idx, 'Conversion_Rate']
            
            if worst_step_idx == 1:  
                potential_users = funnel_df.loc[0, 'Users'] * (improved_rate/100) * (funnel_df.loc[2, 'Conversion_Rate']/100) * (funnel_df.loc[3, 'Conversion_Rate']/100)
            elif worst_step_idx == 2:  
                potential_users = funnel_df.loc[1, 'Users'] * (improved_rate/100) * (funnel_df.loc[3, 'Conversion_Rate']/100)
            else:  
                potential_users = funnel_df.loc[2, 'Users'] * (improved_rate/100)
            
            potential_increase = potential_users - current_users
            
            st.metric(
                "Potential Increase in Sales", 
                f"+{int(potential_increase):,}",
                delta=f"+{round((potential_increase/current_users)*100, 1)}%",
                delta_color="normal"
            )
    with tab2:
        st.header("User Segment Analysis")
        
        segment_tab1, segment_tab2 = st.tabs(["Device", "Gender"])
        
        with segment_tab1:
            st.subheader("Analysis by Device")
            
            device_segments = analysis_results['segments']['device']
            
            device_cr_fig = create_segment_comparison_chart(
                device_segments, "Device", "overall_conversion"
            )
            st.plotly_chart(device_cr_fig, use_container_width=True)
            
            device_stage_fig = create_stage_comparison_by_segment(
                device_segments, "Device"
            )
            st.plotly_chart(device_stage_fig, use_container_width=True)
            
            st.subheader("Conversion Rates by Device")
            
            device_data = []
            for device, data in device_segments.items():
                funnel = data['funnel_df']
                device_data.append({
                    "Device": device,
                    "Home to Search": f"{funnel.loc[1, 'Conversion_Rate']}%",
                    "Search to Payment": f"{funnel.loc[2, 'Conversion_Rate']}%",
                    "Payment to Confirmation": f"{funnel.loc[3, 'Conversion_Rate']}%",
                    "Overall": f"{data['overall_conversion']}%"
                })
            
            device_df = pd.DataFrame(device_data)
            st.dataframe(device_df, hide_index=True, use_container_width=True)
        
        with segment_tab2:
            st.subheader("Analysis by Gender")
            
            gender_segments = analysis_results['segments']['gender']
            
            gender_cr_fig = create_segment_comparison_chart(
                gender_segments, "Gender", "overall_conversion"
            )
            st.plotly_chart(gender_cr_fig, use_container_width=True)
            
            gender_stage_fig = create_stage_comparison_by_segment(
                gender_segments, "Gender"
            )
            st.plotly_chart(gender_stage_fig, use_container_width=True)
            
            st.subheader("Conversion Rates by Gender")
            
            gender_data = []
            for gender, data in gender_segments.items():
                funnel = data['funnel_df']
                gender_data.append({
                    "Gender": gender,
                    "Home to Search": f"{funnel.loc[1, 'Conversion_Rate']}%",
                    "Search to Payment": f"{funnel.loc[2, 'Conversion_Rate']}%",
                    "Payment to Confirmation": f"{funnel.loc[3, 'Conversion_Rate']}%",
                    "Overall": f"{data['overall_conversion']}%"
                })
            
            gender_df = pd.DataFrame(gender_data)
            st.dataframe(gender_df, hide_index=True, use_container_width=True)
    
    with tab3:
        st.header("New vs Existing Users Analysis")
        
        new_vs_existing_fig1, new_vs_existing_fig2 = create_new_vs_existing_comparison(analysis_results)
        
        st.plotly_chart(new_vs_existing_fig1, use_container_width=True)
        st.plotly_chart(new_vs_existing_fig2, use_container_width=True)
        
        st.subheader("Conversion Rates Comparison")
        
        new_data = analysis_results['segments']['user_type']['new']
        existing_data = analysis_results['segments']['user_type']['existing']
        
        user_type_data = []
        
        new_funnel = new_data['funnel']
        user_type_data.append({
            "User Type": "New Users",
            "Home to Search": f"{new_funnel.loc[1, 'Conversion_Rate']}%",
            "Search to Payment": f"{new_funnel.loc[2, 'Conversion_Rate']}%",
            "Payment to Confirmation": f"{new_funnel.loc[3, 'Conversion_Rate']}%",
            "Overall": f"{new_data['overall_conversion']}%",
            "Count": f"{new_data['count']:,}"
        })
        existing_funnel = existing_data['funnel']
        user_type_data.append({
            "User Type": "Existing Users",
            "Home to Search": f"{existing_funnel.loc[1, 'Conversion_Rate']}%",
            "Search to Payment": f"{existing_funnel.loc[2, 'Conversion_Rate']}%",
            "Payment to Confirmation": f"{existing_funnel.loc[3, 'Conversion_Rate']}%",
            "Overall": f"{existing_data['overall_conversion']}%",
            "Count": f"{existing_data['count']:,}"
        })
        
        user_type_df = pd.DataFrame(user_type_data)
        st.dataframe(user_type_df, hide_index=True, use_container_width=True)
        
        st.subheader("Key Differences")
        
        difference_col1, difference_col2, difference_col3 = st.columns(3)
        
        with difference_col1:
            diff = new_data['overall_conversion'] - existing_data['overall_conversion']
            st.metric(
                "Overall Conversion Rate Difference", 
                f"{abs(diff):.2f}%",
                delta=f"{'Higher' if diff > 0 else 'Lower'} for new users",
                delta_color="normal" if diff > 0 else "inverse"
            )
        
        with difference_col2:
            stage_diffs = [
                new_funnel.loc[i, 'Conversion_Rate'] - existing_funnel.loc[i, 'Conversion_Rate']
                for i in range(1, 4)
            ]
            max_diff_idx = np.argmax([abs(diff) for diff in stage_diffs]) + 1
            stages = ['Home to Search', 'Search to Payment', 'Payment to Confirmation']
            
            st.metric(
                "Biggest Stage Difference", 
                f"{stages[max_diff_idx-1]}",
                delta=f"{abs(stage_diffs[max_diff_idx-1]):.2f}% {'higher' if stage_diffs[max_diff_idx-1] > 0 else 'lower'} for new users",
                delta_color="normal" if stage_diffs[max_diff_idx-1] > 0 else "inverse"
            )
        
        with difference_col3:
            new_drop_offs = [
                100 - new_funnel.loc[i, 'Conversion_Rate']
                for i in range(1, 4)
            ]
            max_drop_idx = np.argmax(new_drop_offs) + 1
            
            st.metric(
                "Focus Area for New Users", 
                f"{stages[max_drop_idx-1]}",
                delta=f"{new_drop_offs[max_drop_idx-1]:.2f}% drop-off",
                delta_color="inverse"
            )
    with tab4:
        st.header("Key Insights")
        
        for i, insight in enumerate(insights):
            st.markdown(f"### {i+1}. {insight}")
    
    with tab5:
        st.header("Strategic Recommendations")
        
        for i, recommendation in enumerate(recommendations):
            st.markdown(f"### {i+1}. {recommendation}")
    
    st.sidebar.header("Download Analysis")
    
    if st.sidebar.button("Generate PowerPoint Presentation"):
        with st.spinner("Generating PowerPoint presentation..."):
            ppt_bytes = create_presentation(analysis_results, insights, recommendations)
            st.sidebar.markdown(
                download_link(
                    ppt_bytes, 
                    "E-commerce_Funnel_Analysis.pptx", 
                    "⬇️ Download PowerPoint Presentation"
                ), 
                unsafe_allow_html=True
            )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About This Analysis")
    st.sidebar.markdown(
        """
        This analysis examines the e-commerce conversion funnel:
        
        Home → Search → Payment → Confirmation
        
        We analyze drop-off points, segment by user characteristics, 
        and provide strategic recommendations to improve conversion rates.
        """
    )

if __name__ == "__main__":
    main()
