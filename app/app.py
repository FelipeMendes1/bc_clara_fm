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

from utils import load_data
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
        # Perform analysis
        analysis_results = perform_funnel_analysis(
            home_df, search_df, payment_df, confirmation_df, user_df
        )
        
        # Generate insights and recommendations
        insights = generate_insights(analysis_results)
        recommendations = generate_recommendations(analysis_results)
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Funnel Overview", 
    "👥 User Segments", 
    "🔍 New vs Existing Users", 
    "💡 Insights", 
    "📝 Recommendations",  
    "📈 Advanced Analytics"
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
    with tab6:
        st.header("📈 Advanced Funnel Analysis")
        st.markdown("### Deep dive into user behaviors and conversion analysis.")

        # 🔵 Drop-off Heatmap por Dispositivo (Mobile vs Desktop)
        st.subheader("🔵 Drop-off Heatmap (Device)")

        # Merge device information
        home_device = home_df.merge(user_df[['user_id', 'device']], on='user_id', how='left')
        search_device = search_df.merge(user_df[['user_id', 'device']], on='user_id', how='left')
        payment_device = payment_df.merge(user_df[['user_id', 'device']], on='user_id', how='left')
        confirmation_device = confirmation_df.merge(user_df[['user_id', 'device']], on='user_id', how='left')

        def calculate_dropoff_rates(step_dfs, segments, segment_name):
            rates = []
            for step_idx in range(len(step_dfs) - 1):
                start_step = step_dfs[step_idx]
                next_step = step_dfs[step_idx + 1]
                for segment in segments:
                    start_segment = start_step[start_step[segment_name] == segment]
                    next_segment = next_step[next_step[segment_name] == segment]
                    if len(start_segment) == 0:
                        dropoff_rate = None
                    else:
                        dropoff_rate = 1 - (len(next_segment) / len(start_segment))
                    rates.append({
                        'From Step': f"Step {step_idx+1} → {step_idx+2}",
                        'Segment': segment,
                        'Drop-off Rate': round(dropoff_rate * 100, 2) if dropoff_rate is not None else None
                    })
            return pd.DataFrame(rates)

        device_segments = user_df['device'].dropna().unique()

        dropoff_device = calculate_dropoff_rates(
            [home_device, search_device, payment_device, confirmation_device],
            device_segments,
            segment_name='device'
        )

        fig_device = px.density_heatmap(
            dropoff_device,
            x='From Step',
            y='Segment',
            z='Drop-off Rate',
            color_continuous_scale='Reds',
            labels={'Drop-off Rate': '% Drop-off'},
            title="Drop-off Rates by Device"
        )

        st.plotly_chart(fig_device, use_container_width=True)

        # 🔵 Drop-off Heatmap por Tipo de Usuário (Novo vs Existente)
        st.subheader("🔵 Drop-off Heatmap (User Type)")

        # Definir Novos vs Existentes
        user_df['date'] = pd.to_datetime(user_df['date'], errors='coerce')
        cutoff_date = user_df['date'].max() - pd.Timedelta(days=7)
        user_df['user_type'] = user_df['date'].apply(lambda x: 'New User' if x >= cutoff_date else 'Existing User')

        home_type = home_df.merge(user_df[['user_id', 'user_type']], on='user_id', how='left')
        search_type = search_df.merge(user_df[['user_id', 'user_type']], on='user_id', how='left')
        payment_type = payment_df.merge(user_df[['user_id', 'user_type']], on='user_id', how='left')
        confirmation_type = confirmation_df.merge(user_df[['user_id', 'user_type']], on='user_id', how='left')

        user_segments = ['New User', 'Existing User']

        dropoff_user_type = calculate_dropoff_rates(
            [home_type, search_type, payment_type, confirmation_type],
            user_segments,
            segment_name='user_type'
        )

        fig_user_type = px.density_heatmap(
            dropoff_user_type,
            x='From Step',
            y='Segment',
            z='Drop-off Rate',
            color_continuous_scale='Blues',
            labels={'Drop-off Rate': '% Drop-off'},
            title="Drop-off Rates by User Type"
        )

        st.plotly_chart(fig_user_type, use_container_width=True)
        st.subheader("🟢 Funnel Comparison by Device")

        # Função auxiliar para calcular taxas de conversão etapa a etapa
        def calculate_step_conversion(step_dfs, segments, segment_name):
            conversions = []
            for step_idx in range(len(step_dfs) - 1):
                start_step = step_dfs[step_idx]
                next_step = step_dfs[step_idx + 1]

                for segment in segments:
                    start_segment = start_step[start_step[segment_name] == segment]
                    next_segment = next_step[next_step[segment_name] == segment]

                    if len(start_segment) == 0:
                        conversion_rate = None
                    else:
                        conversion_rate = len(next_segment) / len(start_segment)

                    conversions.append({
                        'Step': f"Step {step_idx+1} → {step_idx+2}",
                        'Segment': segment,
                        'Conversion Rate': round(conversion_rate * 100, 2) if conversion_rate is not None else None
                    })
            return pd.DataFrame(conversions)

        # Dispositivo - Mobile vs Desktop
        conversion_device = calculate_step_conversion(
            [home_device, search_device, payment_device, confirmation_device],
            device_segments,
            segment_name='device'
        )

        fig_funnel_device = px.bar(
            conversion_device,
            x="Step",
            y="Conversion Rate",
            color="Segment",
            barmode="group",
            labels={'Conversion Rate': '% Conversion'},
            title="Funnel Conversion Comparison by Device"
        )

        st.plotly_chart(fig_funnel_device, use_container_width=True)

                

        st.subheader("🟣 Cumulative Conversion Curve")

        # Marcar quem converteu (baseado na confirmation_df)
        user_df['converted'] = user_df['user_id'].isin(confirmation_df['user_id'])

        # Agrupar conversões por data
        daily_conversions = user_df.groupby(user_df['date'].dt.date).agg(
            total_users=('user_id', 'count'),
            total_converted=('converted', 'sum')
        ).reset_index()

        # Calcular taxa diária
        daily_conversions['conversion_rate'] = daily_conversions['total_converted'] / daily_conversions['total_users']

        # Acumular ao longo do tempo
        daily_conversions['cumulative_users'] = daily_conversions['total_users'].cumsum()
        daily_conversions['cumulative_converted'] = daily_conversions['total_converted'].cumsum()
        daily_conversions['cumulative_conversion_rate'] = daily_conversions['cumulative_converted'] / daily_conversions['cumulative_users']

        # Plotar a curva
        fig_cumulative = px.line(
            daily_conversions,
            x="date",
            y="cumulative_conversion_rate",
            labels={'cumulative_conversion_rate': 'Cumulative Conversion Rate', 'date': 'Date'},
            title="Cumulative Conversion Rate Over Time"
        )

        fig_cumulative.update_traces(mode='lines+markers')
        fig_cumulative.update_layout(yaxis_tickformat='%')

        st.plotly_chart(fig_cumulative, use_container_width=True)
        
        # 🟠 Time to Conversion by Segment

        st.subheader("🟠 Time to Conversion by Segment")

        # Garantir que a data de cadastro está correta
        user_df['date'] = pd.to_datetime(user_df['date'], errors='coerce')

        # Marcar usuários que converteram
        confirmed_users = user_df[user_df['user_id'].isin(confirmation_df['user_id'])]

        # Para simular: vamos assumir que todos confirmaram no mesmo dia do cadastro
        confirmed_users['conversion_time_days'] = 0  # 🔥 Simplificação para agora

        # Se quiser simular atrasos reais: podemos randomizar pequenos atrasos

        # Plotar o Boxplot
        fig_boxplot = px.box(
            confirmed_users,
            x="user_type",
            y="conversion_time_days",
            color="user_type",
            title="Time to Conversion by User Type",
            labels={"conversion_time_days": "Days to Convert", "user_type": "User Type"}
        )

        st.plotly_chart(fig_boxplot, use_container_width=True)

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
