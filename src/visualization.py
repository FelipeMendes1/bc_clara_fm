import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def create_funnel_chart(funnel_df, title="Conversion Funnel"):
    """
    Create a funnel chart visualizing the conversion funnel
    """
    # Create a plotly funnel chart
    fig = go.Figure(go.Funnel(
        y=funnel_df['Stage'],
        x=funnel_df['Users'],
        textinfo="value+percent initial",
        marker={"color": ["#0068c9", "#83c9ff", "#29b09d", "#7defa1"]}
    ))
    
    fig.update_layout(
        title=title,
        font=dict(size=14),
        height=500
    )
    
    return fig

def create_conversion_rate_chart(funnel_df, title="Conversion Rates by Funnel Stage"):
    """
    Create a bar chart showing conversion rates between funnel stages
    """
    # For conversion rates between stages
    stages = ['Home to Search', 'Search to Payment', 'Payment to Confirmation']
    rates = funnel_df['Conversion_Rate'].values[1:]  # Skip the first one (Home)
    
    fig = go.Figure(go.Bar(
        x=stages,
        y=rates,
        text=[f"{rate}%" for rate in rates],
        textposition='auto',
        marker_color=['#83c9ff', '#29b09d', '#7defa1']
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Funnel Stage",
        yaxis_title="Conversion Rate (%)",
        yaxis=dict(range=[0, 100]),
        height=400
    )
    
    return fig

def create_drop_off_chart(drop_off_df, title="Drop-off Rates by Funnel Stage"):
    """
    Create a bar chart showing drop-off rates between funnel stages
    """
    fig = go.Figure(go.Bar(
        x=drop_off_df['Stage'],
        y=drop_off_df['Drop_Off_Percentage'],
        text=[f"{rate}%" for rate in drop_off_df['Drop_Off_Percentage']],
        textposition='auto',
        marker_color=['#ff6b6b', '#ff9e7d', '#ffcd56']
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Funnel Stage",
        yaxis_title="Drop-off Rate (%)",
        yaxis=dict(range=[0, 100]),
        height=400
    )
    
    return fig

def create_segment_comparison_chart(segments, segment_type, metric='overall_conversion'):
    """
    Create a bar chart comparing a metric across different segments
    """
    labels = list(segments.keys())
    
    if metric == 'overall_conversion':
        values = [segments[label]['overall_conversion'] for label in labels]
        title = f"Overall Conversion Rate by {segment_type}"
        y_title = "Conversion Rate (%)"
    else:
        # For other metrics if needed in the future
        values = [0] * len(labels)
        title = f"{metric} by {segment_type}"
        y_title = metric
    
    colors = px.colors.qualitative.Plotly[:len(labels)]
    
    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        text=[f"{value}%" for value in values],
        textposition='auto',
        marker_color=colors
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title=segment_type,
        yaxis_title=y_title,
        height=400
    )
    
    return fig

def create_stage_comparison_by_segment(segments, segment_type):
    """
    Create a grouped bar chart comparing conversion at each stage across segments
    """
    labels = list(segments.keys())
    stages = ['Home', 'Search', 'Payment', 'Confirmation']
    
    fig = go.Figure()
    
    for i, label in enumerate(labels):
        funnel_df = segments[label]['funnel_df']
        fig.add_trace(go.Bar(
            x=stages,
            y=funnel_df['Users'],
            name=str(label),
            text=[f"{count}" for count in funnel_df['Users']],
            textposition='auto'
        ))
    
    fig.update_layout(
        title=f"Users at Each Funnel Stage by {segment_type}",
        xaxis_title="Funnel Stage",
        yaxis_title="Number of Users",
        barmode='group',
        height=500
    )
    
    return fig

def create_new_vs_existing_comparison(analysis_results):
    """
    Create visualizations comparing new vs existing users
    """
    # Get data
    new_data = analysis_results['segments']['user_type']['new']
    existing_data = analysis_results['segments']['user_type']['existing']
    
    # Conversion rate comparison
    labels = ['New Users', 'Existing Users']
    values = [new_data['overall_conversion'], existing_data['overall_conversion']]
    
    fig1 = go.Figure(go.Bar(
        x=labels,
        y=values,
        text=[f"{value}%" for value in values],
        textposition='auto',
        marker_color=['#ff9e7d', '#29b09d']
    ))
    
    fig1.update_layout(
        title="Overall Conversion Rate: New vs Existing Users",
        yaxis_title="Conversion Rate (%)",
        height=400
    )
    
    # Funnel stage comparison
    stages = ['Home', 'Search', 'Payment', 'Confirmation']
    
    fig2 = go.Figure()
    
    fig2.add_trace(go.Bar(
        x=stages,
        y=new_data['funnel']['Users'],
        name='New Users',
        text=[f"{count}" for count in new_data['funnel']['Users']],
        textposition='auto'
    ))
    
    fig2.add_trace(go.Bar(
        x=stages,
        y=existing_data['funnel']['Users'],
        name='Existing Users',
        text=[f"{count}" for count in existing_data['funnel']['Users']],
        textposition='auto'
    ))
    
    fig2.update_layout(
        title="Users at Each Funnel Stage: New vs Existing Users",
        xaxis_title="Funnel Stage",
        yaxis_title="Number of Users",
        barmode='group',
        height=500
    )
    
    return fig1, fig2
