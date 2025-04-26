import pandas as pd
import numpy as np
from utils import *

def perform_funnel_analysis(home_df, search_df, payment_df, confirmation_df, user_df):
    funnel_df, overall_conversion, user_sets = calculate_user_journeys(
        home_df, search_df, payment_df, confirmation_df
    )
    device_segments = segment_by_attribute(
        home_df, search_df, payment_df, confirmation_df, user_df, 'device'
    )
    gender_segments = segment_by_attribute(
        home_df, search_df, payment_df, confirmation_df, user_df, 'sex'
    )
    new_users, existing_users = identify_new_users(user_df)
    
    new_user_home = home_df[home_df['user_id'].isin(new_users['user_id'])]
    new_user_search = search_df[search_df['user_id'].isin(new_users['user_id'])]
    new_user_payment = payment_df[payment_df['user_id'].isin(new_users['user_id'])]
    new_user_confirmation = confirmation_df[confirmation_df['user_id'].isin(new_users['user_id'])]
    
    existing_user_home = home_df[home_df['user_id'].isin(existing_users['user_id'])]
    existing_user_search = search_df[search_df['user_id'].isin(existing_users['user_id'])]
    existing_user_payment = payment_df[payment_df['user_id'].isin(existing_users['user_id'])]
    existing_user_confirmation = confirmation_df[confirmation_df['user_id'].isin(existing_users['user_id'])]
    
    new_user_funnel, new_user_overall, _ = calculate_user_journeys(
        new_user_home, new_user_search, new_user_payment, new_user_confirmation
    )
    
    existing_user_funnel, existing_user_overall, _ = calculate_user_journeys(
        existing_user_home, existing_user_search, existing_user_payment, existing_user_confirmation
    )
    
    drop_off_data = {
        'Stage': ['Home to Search', 'Search to Payment', 'Payment to Confirmation'],
        'Drop_Off_Count': [
            len(user_sets['home_users']) - len(user_sets['home_to_search']),
            len(user_sets['search_users']) - len(user_sets['search_to_payment']),
            len(user_sets['payment_users']) - len(user_sets['payment_to_confirmation'])
        ]
    }
    
    drop_off_df = pd.DataFrame(drop_off_data)
    drop_off_df['Drop_Off_Percentage'] = [
        round(drop_off_df.loc[0, 'Drop_Off_Count'] / len(user_sets['home_users']) * 100, 2) if len(user_sets['home_users']) > 0 else 0,
        round(drop_off_df.loc[1, 'Drop_Off_Count'] / len(user_sets['search_users']) * 100, 2) if len(user_sets['search_users']) > 0 else 0,
        round(drop_off_df.loc[2, 'Drop_Off_Count'] / len(user_sets['payment_users']) * 100, 2) if len(user_sets['payment_users']) > 0 else 0
    ]
    
    return {
        'overall': {
            'funnel': funnel_df,
            'conversion_rate': overall_conversion,
            'drop_off': drop_off_df
        },
        'segments': {
            'device': device_segments,
            'gender': gender_segments,
            'user_type': {
                'new': {
                    'funnel': new_user_funnel,
                    'overall_conversion': new_user_overall,
                    'count': len(new_users)
                },
                'existing': {
                    'funnel': existing_user_funnel,
                    'overall_conversion': existing_user_overall,
                    'count': len(existing_users)
                }
            }
        },
        'user_counts': {
            'total': len(user_df),
            'new': len(new_users),
            'existing': len(existing_users)
        }
    }

def generate_insights(analysis_results):
    insights = []
    
    overall_cr = analysis_results['overall']['conversion_rate']
    insights.append(f"Overall funnel conversion rate: {overall_cr}% from Home to Confirmation")
    
    drop_off = analysis_results['overall']['drop_off']
    max_drop_idx = drop_off['Drop_Off_Percentage'].idxmax()
    max_drop_stage = drop_off.loc[max_drop_idx, 'Stage']
    max_drop_pct = drop_off.loc[max_drop_idx, 'Drop_Off_Percentage']
    insights.append(f"Biggest drop-off point: {max_drop_stage} with {max_drop_pct}% users lost")
    
    devices = analysis_results['segments']['device']
    device_cr = {device: data['overall_conversion'] for device, data in devices.items()}
    best_device = max(device_cr, key=device_cr.get)
    worst_device = min(device_cr, key=device_cr.get)
    insights.append(f"Device comparison: {best_device} performs best with {device_cr[best_device]}% conversion rate, while {worst_device} has {device_cr[worst_device]}%")
    
    genders = analysis_results['segments']['gender']
    gender_cr = {gender: data['overall_conversion'] for gender, data in genders.items()}
    for gender, cr in gender_cr.items():
        insights.append(f"{gender} users have a {cr}% overall conversion rate")
    
    new_cr = analysis_results['segments']['user_type']['new']['overall_conversion']
    existing_cr = analysis_results['segments']['user_type']['existing']['overall_conversion']
    insights.append(f"New users convert at {new_cr}% compared to {existing_cr}% for existing users")
    
    new_funnel = analysis_results['segments']['user_type']['new']['funnel']
    new_worst_stage_idx = new_funnel['Drop_Off_Rate'].idxmax()
    new_worst_stage = new_funnel.loc[new_worst_stage_idx, 'Stage']
    new_worst_drop = new_funnel.loc[new_worst_stage_idx, 'Drop_Off_Rate']
    insights.append(f"New users struggle most at the {new_worst_stage} stage with a {new_worst_drop}% drop-off rate")
    
    return insights

def generate_recommendations(analysis_results):
    recommendations = []
    
    drop_off = analysis_results['overall']['drop_off']
    max_drop_idx = drop_off['Drop_Off_Percentage'].idxmax()
    max_drop_stage = drop_off.loc[max_drop_idx, 'Stage']
    
    new_cr = analysis_results['segments']['user_type']['new']['overall_conversion']
    existing_cr = analysis_results['segments']['user_type']['existing']['overall_conversion']
    
    devices = analysis_results['segments']['device']
    device_cr = {device: data['overall_conversion'] for device, data in devices.items()}
    worst_device = min(device_cr, key=device_cr.get)
    
    if max_drop_stage == 'Home to Search':
        recommendations.append("Improve search visibility: Make the search bar more prominent on the home page")
        recommendations.append("Add featured products on the home page to encourage exploration")
        recommendations.append("Implement personalized product recommendations on the home page based on user behavior")
    
    elif max_drop_stage == 'Search to Payment':
        recommendations.append("Enhance product listings with better images, descriptions, and social proof")
        recommendations.append("Implement filters to help users find relevant products faster")
        recommendations.append("Show limited-time offers to create urgency")
    
    elif max_drop_stage == 'Payment to Confirmation':
        recommendations.append("Simplify the checkout process with fewer form fields")
        recommendations.append("Add multiple payment options to accommodate user preferences")
        recommendations.append("Implement guest checkout to reduce friction for new users")
    
    if new_cr < existing_cr * 0.8: 
        recommendations.append("Create a first-time user discount to incentivize completion of first purchase")
        recommendations.append("Add a guided tutorial for new users explaining the shopping process")
        recommendations.append("Implement live chat support to assist new users with questions")
    
    if 'Mobile' in device_cr and device_cr['Mobile'] < device_cr.get('Desktop', 100):
        recommendations.append("Optimize the mobile experience with a responsive design")
        recommendations.append("Simplify the mobile checkout process")
        recommendations.append("Implement mobile-specific features like saved payment details")
    
    recommendations.append("Implement A/B testing to continuously optimize the conversion funnel")
    recommendations.append("Set up email retargeting campaigns for users who abandon the funnel")
    recommendations.append("Collect user feedback at drop-off points to understand specific issues")
    
    return recommendations
