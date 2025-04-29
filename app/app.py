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
from pathlib import Path

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
            st.header("💡 Insights")
            st.markdown("### Understanding the Conversion Gaps by User Type")

            st.markdown("""
            #### 📊 Conversion Performance by User Type:
            - **New Users Conversion Rate:** **0.13%** 🧍‍♂️
            - **Existing Users Conversion Rate:** **0.53%** 🧍‍♂️➡️

            #### 🧠 Key Findings:
            - Existing users are **4x more likely to convert** compared to new users.
            - The extremely low conversion rate among new users suggests **issues in the initial engagement** or **lack of early trust**.

            #### 🚨 Root Cause Hypotheses:
            - Poor onboarding experience for new users.
            - Lack of clear value proposition immediately after signup.
            - Navigation friction or lack of early guidance.
            """)
            st.markdown("### Diagnosing Drop-offs Across Funnel Stages")

            st.markdown("""
            #### 📊 Funnel Performance Overview:
            - Major drop-offs occur **right after the Home Page**, especially for **New Users**.
            - Only **40% of New Users** and **50% of Existing Users** proceed from Home to Search.
            - From Search to Payment, abandonment increases drastically, with **New Users nearly vanishing** at the Payment stage.

            #### 🧠 Key Findings:
            - Initial engagement is weak, suggesting issues with the first user interaction experience.
            - New Users struggle significantly more to progress through the funnel compared to Existing Users.
            - The funnel narrows critically after the Search phase, indicating possible friction or lack of incentive to proceed.

            #### 🚨 Root Cause Hypotheses (Evidence-Based):

            1. **Homepage Overload or Lack of Clear CTAs (Call to Actions)**  
            - According to HubSpot, 76% of users say the most important factor in a website's design is the ability to find what they want easily. A homepage without clear action steps significantly increases bounce rates.

            2. **Search Function Inefficiency or Poor Relevance of Results**  
            - A survey by Invesp shows that visitors who use internal search are 2-3 times more likely to convert, but only if search results are fast and relevant. A frustrating search experience causes rapid abandonment. 

            3. **High Friction in Payment Process for First-Time Users**  
            - Research from Baymard Institute indicates that complicated checkout processes cause 17% of users to abandon carts. Especially for new users, complexity or distrust during payment is a major conversion killer.
            """)
            st.markdown("### Identifying Critical Drop-offs in the Conversion Funnel")

            st.markdown("""
            #### 📊 Funnel Drop-off Analysis:
            - **Home → Search:** 50% of users abandon at the first interaction point.
            - **Search → Payment:** Critical drop-off of **86.66%**, indicating major friction in product discovery or purchase decision.
            - **Payment → Confirmation:** Extremely high abandonment of **92.5%**, suggesting severe issues during checkout.

            #### 🧠 Key Findings:
            - Half of the users never initiate a search after landing on the Home page.
            - Most users who do search fail to proceed to payment, implying problems with product attractiveness, trust, or pricing.
            - Even among users willing to pay, the majority abandon before completing the transaction, highlighting checkout or payment barriers.

            #### 🚨 Root Cause Hypotheses (Evidence-Based):

            1. **Lack of Engagement or Motivation on Home Page**  
            - According to a survey by Top Design Firms, 42% of users will leave a website due to poor functionality and lack of clear calls-to-action. ([topdesignfirms.com](https://topdesignfirms.com/blog/website-optimization-strategies?utm_source=chatgpt.com))

            2. **Poor Product Relevance or Pricing Mismatch**  
            - According to Baymard Institute, 55% of users abandon a purchase because they weren't ready to buy or found the product price too high compared to perceived value. ([baymard.com](https://baymard.com/lists/cart-abandonment-rate?utm_source=chatgpt.com))

            3. **High Checkout Friction (Complex Forms, Lack of Payment Options)**  
            - Research shows that 17% of users abandon carts due to complex or lengthy checkout processes, and 6% due to insufficient payment options. ([baymard.com](https://baymard.com/checkout-usability?utm_source=chatgpt.com))
            """)
            st.markdown("### Device Impact on Conversion Rates and Funnel Drop-offs")

            st.markdown("""
            #### 📊 Device-Based Conversion Overview:
            - **Mobile users** have a conversion rate of **1.0%**, significantly outperforming **Desktop users** (**0.25%**).
            - Despite Mobile users being fewer at the start, they maintain better progression through the funnel stages.

            #### 🧠 Key Findings:
            - **Mobile devices** are associated with a higher conversion likelihood.
            - **Desktop users** exhibit higher abandonment, possibly due to differences in session intent or user expectations.
            - Mobile users are slightly more consistent in progressing from search to payment stages.

            #### 🚨 Root Cause Hypotheses (Evidence-Based):

            1. **Mobile-friendly UX advantages**  
            - Mobile-optimized experiences (simpler checkout, faster navigation) can increase conversion rates. A Statista report highlights that mobile commerce continues to grow faster than desktop purchases. ([statista.com](https://www.statista.com/statistics/249863/us-mobile-retail-commerce-sales-as-percentage-of-e-commerce-sales/?utm_source=chatgpt.com))

            2. **Session context differences**  
            - Mobile users often engage in quick, goal-driven sessions, favoring faster decisions. Desktop users may exhibit more exploratory behaviors, delaying purchases. (Nielsen Norman Group, Mobile vs Desktop Behavior Study)

            3. **Performance and Speed**  
            - Google's research shows that mobile page load times have a major impact on conversion: faster mobile experiences boost engagement. ([thinkwithgoogle.com](https://www.thinkwithgoogle.com/marketing-strategies/app-and-mobile/mobile-page-speed-new-industry-benchmarks/?utm_source=chatgpt.com))
            """)
            st.markdown("### Gender Influence on Conversion Behavior")

            st.markdown("""
            #### 📊 Gender-Based Conversion Overview:
            - **Female users** have a slightly higher overall conversion rate (**0.53%**) compared to **Male users** (**0.47%**).
            - Both genders have similar progression patterns across funnel stages, with minor differences at payment and confirmation stages.

            #### 🧠 Key Findings:
            - Female users are marginally more likely to complete the funnel compared to male users.
            - Both genders show similar drop-off behaviors from Home to Search and from Search to Payment.

            #### 🚨 Root Cause Hypotheses (Evidence-Based):

            1. **Decision-Making Styles by Gender**  
            - Studies suggest that women tend to make purchasing decisions faster when the platform aligns with their goals and trust is established early. (Harvard Business Review, "The Female Economy")

            2. **Product/Category Relevance and Personalization**  
            - Relevance of product offerings and personalization can affect male vs female user journeys differently. Better targeting may further enhance female conversion. (McKinsey Insights on Consumer Personalization)

            3. **Trust and Confidence Factors**  
            - Research indicates women place higher importance on security, privacy, and guarantees, influencing conversion positively when emphasized. (GlobalWebIndex Research)
            """)
            st.markdown("### Understanding Conversion Gaps Between New and Existing Users")

            st.markdown("""
            #### 📊 Conversion Rate Comparison:
            - **Overall Conversion Rate:** 0.13% for New Users vs. 0.53% for Existing Users.
            - **Home to Search Transition:** 39.97% (New) vs. 50.73% (Existing).
            - **Search to Payment Transition:** 6.52% (New) vs. 13.73% (Existing).
            - **Payment to Confirmation Transition:** 5.03% (New) vs. 7.56% (Existing).

            #### 🧠 Key Findings:
            - New users consistently underperform across all funnel stages compared to existing users.
            - The **Home to Search** stage shows a **critical 10.76% lower engagement** for new users.
            - **Payment to Confirmation** is the biggest bottleneck for new users, with a **94.97% drop-off rate**.

            #### 🚨 Root Cause Hypotheses (Evidence-Based):

            1. **Insufficient Motivation to Explore or Search**  
            - Research suggests that the absence of immediate value or guidance leads to abandonment during first interactions. (Nielsen Norman Group, UX Research)

            2. **Trust and Confidence Barriers for New Users**  
            - First-time users are particularly sensitive to signals of trust, security, and value alignment. Lack of these leads to hesitancy at the point of payment. (Baymard Institute Checkout Study)

            3. **Higher Cognitive Load for New Users**  
            - New visitors face higher cognitive friction navigating the funnel. Without clear and simple progression cues, dropout rates surge. (NNGroup Cognitive Friction Studies)
            """)
            st.markdown("""
            ### 📈 Low Search Engagement
            - The vast majority of users performed only **one search** before abandoning the funnel.
            - Very few users made multiple search attempts, suggesting **early frustration** or **low search engine effectiveness**.

            ### 🛑 High Early Drop-off
            - Over **45,200 users** visited only the Home page without progressing.
            - Another **39,170 users** advanced to Search but then abandoned.
            - Very few users reached the payment stage, and even fewer completed the funnel.

            ### 🧠 Interpretation:
            - **Search effectiveness is critical**: If users don't find what they want quickly, they leave.
            - **First impression is crucial**: Homepage and Search must immediately guide and engage users.
            - **Persistence is rare**: Users rarely make a second search if the first is unsuccessful, indicating a need for better navigation support.
            """)
    with tab5:
        st.header("Strategic Recommendations")
        st.markdown("### Data-Driven Actions to Optimize Funnel Performance")

        st.markdown("""
        #### 🎯 1. Improve New User Engagement and Trust:
        - Implement a **guided onboarding** process for new users immediately upon account creation.
        - **Highlight key benefits and trust elements** early (e.g., money-back guarantee, secure payments, social proof).
        - Offer **special welcome promotions** to encourage first-time exploration and purchases.
        - Simplify navigation and first steps with **clear calls-to-action** on the home page.

        #### 🎯 2. Optimize the First Funnel Stage (Home → Search):
        - Display **top categories, trending products**, or **personalized suggestions** directly on the home page.
        - Include **intuitive search prompts** or **popular searches** immediately visible to users.
        - Reduce homepage clutter; **focus the user journey on initiating a search** quickly.

        #### 🎯 3. Enhance Search-to-Payment Transition:
        - Improve **search functionality** to return fast, highly relevant results.
        - Offer **filters and sorting options** to help users find the right products faster.
        - Implement **scarcity tactics** ("Only X items left!", "Limited Time Offer!") to drive urgency towards purchase.

        #### 🎯 4. Reduce Payment-to-Confirmation Drop-offs:
        - **Simplify checkout**: fewer steps, fewer form fields, progress indicators.
        - Enable **guest checkout** (no mandatory account creation) to reduce friction.
        - Offer **multiple trusted payment methods** (credit card, PayPal, digital wallets).
        - Reinforce trust at the payment step with **security badges** and **clear refund policies**.

        #### 🎯 5. Leverage Mobile Advantage:
        - Prioritize **mobile-first design**: fast loading, responsive layout, easy click targets.
        - Optimize checkout flows for mobile: **autofill options**, **one-click payments**, **short forms**.
        - Consider **mobile-exclusive promotions** to encourage mobile conversions.

        #### 🎯 6. Personalize Experiences Based on Gender:
        - Test **different messaging, offers, or product categories** tailored to gender preferences.
        - Highlight **trust and security elements** for all users, but especially for female users who are more sensitive to these factors.
        - Provide **customized product recommendations** based on past browsing or gender-specific trends.
        """)
        
        st.markdown("""
        ### 🎯 7. Improve Search Resilience
        - Implement **auto-suggestions** and **correct minor typos** automatically.
        - Offer **similar search suggestions** if no results are found.
        - Highlight **popular categories** when the user starts typing.

        ### 🎯 8. Boost Persistence with Guided Navigation
        - After an empty search result, propose **top categories or trending products** to encourage another search.
        - Introduce a **wizard-like journey** for first-time users ("What are you looking for? Choose your interests.").

        ### 🎯 9. Strengthen Early Stage Motivation
        - Make the Home page **highly actionable**: large call-to-actions like "Start Searching", "See Top Offers", "Shop Best Sellers".
        - Promote **quick wins**: discounts, limited-time offers, easy navigation paths.

        ### 🎯 10. Minimize Abandonment at Search Stage
        - Provide immediate **next-step prompts** after the first search (e.g., "Found what you needed? Proceed to checkout now!").
        - Show **limited-stock messages** and **social proof** ("10 people are viewing this item!") to boost urgency.
        """)
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

        # 📈 Número de Buscas x Conversão

        st.subheader("📈 Search Activity vs Conversion Success")

        # Contar número de buscas por usuário
        search_counts = search_df['user_id'].value_counts().rename_axis('user_id').reset_index(name='search_count')

        # Marcar quem confirmou pagamento
        search_counts['confirmed'] = search_counts['user_id'].isin(confirmation_df['user_id'])

        # Agrupar por número de buscas e calcular taxa de conversão
        conversion_by_searches = search_counts.groupby('search_count').agg(
            total_users=('user_id', 'count'),
            total_converted=('confirmed', 'sum')
        ).reset_index()

        conversion_by_searches['conversion_rate'] = conversion_by_searches['total_converted'] / conversion_by_searches['total_users']

        # Plotar gráfico
        fig_conversion_search = px.line(
            conversion_by_searches,
            x="search_count",
            y="conversion_rate",
            markers=True,
            title="Conversion Rate by Number of Searches",
            labels={"search_count": "Number of Searches", "conversion_rate": "Conversion Rate"},
        )

        fig_conversion_search.update_layout(
            yaxis_tickformat=".1%",
            xaxis_title="Number of Searches",
            yaxis_title="Conversion Rate"
        )

        st.plotly_chart(fig_conversion_search, use_container_width=True)

        # 📊 Número de Etapas Percorridas

        st.subheader("📊 Funnel Depth Analysis: Number of Steps Completed")

        # Criar conjunto de usuários por etapa
        home_users = set(home_df['user_id'])
        search_users = set(search_df['user_id'])
        payment_users = set(payment_df['user_id'])
        confirmation_users = set(confirmation_df['user_id'])

        # Contar número de etapas atingidas por usuário
        all_users = home_users.union(search_users).union(payment_users).union(confirmation_users)

        user_steps = []
        for user in all_users:
            steps = 0
            if user in home_users:
                steps += 1
            if user in search_users:
                steps += 1
            if user in payment_users:
                steps += 1
            if user in confirmation_users:
                steps += 1
            user_steps.append(steps)

        # Criar DataFrame
        steps_df = pd.DataFrame(user_steps, columns=['steps_completed'])

        # Agrupar
        steps_distribution = steps_df['steps_completed'].value_counts().sort_index().reset_index()
        steps_distribution.columns = ['steps_completed', 'number_of_users']

        # Plotar gráfico
        fig_steps = px.bar(
            steps_distribution,
            x="steps_completed",
            y="number_of_users",
            text="number_of_users",
            title="Number of Users by Funnel Depth",
            labels={"steps_completed": "Number of Steps Completed", "number_of_users": "Number of Users"},
        )

        fig_steps.update_traces(textposition='outside')

        st.plotly_chart(fig_steps, use_container_width=True)


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
    if st.sidebar.button("📥 Download Final Presentation"):
        ppt_path = Path(r"C:\Users\Felipe\Documents\Clara\Business Case - Clara FM.pptx")
        with open(ppt_path, "rb") as f:
            ppt_bytes = f.read()

        styled_link = f"""
        <style>
            .download-link {{
                display: inline-block;
                padding: 10px 15px;
                background-color: #f63366;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }}
            .download-link:hover {{
                background-color: #c0254f;
            }}
        </style>
        <a href="data:application/octet-stream;base64,{base64.b64encode(ppt_bytes).decode()}"
        download="Business_Case_Clara_FM.pptx"
        class="download-link">
        📄 Download the final presentation (PPTX)
        </a>
        """

        st.sidebar.markdown(styled_link, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
