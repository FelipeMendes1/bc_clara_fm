import pandas as pd
import numpy as np
import os
import pandas as pd

def load_data():
    base_path = os.path.abspath(os.path.dirname(__file__))  
    project_root = os.path.abspath(os.path.join(base_path, '..'))  

    home_path = os.path.join(project_root, 'data', 'processed', 'home_page_table.csv')
    search_path = os.path.join(project_root, 'data', 'processed', 'search_page_table.csv')
    payment_path = os.path.join(project_root, 'data', 'processed', 'payment_page_table.csv')
    confirmation_path = os.path.join(project_root, 'data', 'processed', 'payment_confirmation_table.csv')
    user_path = os.path.join(project_root, 'data', 'processed', 'user_table.csv')

    try:
        home_df = pd.read_csv(home_path)
        search_df = pd.read_csv(search_path)
        payment_df = pd.read_csv(payment_path)
        confirmation_df = pd.read_csv(confirmation_path)
        user_df = pd.read_csv(user_path)
        
        #convertendo a coluna 'date' para datetime depois de carregar
        if 'date' in user_df.columns:
            user_df['date'] = pd.to_datetime(user_df['date'], errors='coerce')

        print(f"Loaded data successfully. Dimensions:")
        print(f"Home page: {home_df.shape}")
        print(f"Search page: {search_df.shape}")
        print(f"Payment page: {payment_df.shape}")
        print(f"Confirmation page: {confirmation_df.shape}")
        print(f"User table: {user_df.shape}")
        
        return home_df, search_df, payment_df, confirmation_df, user_df
    
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return None, None, None, None, None

def merge_with_users(page_df, user_df):
    merged_df = pd.merge(page_df, user_df, on='user_id', how='left')
    return merged_df

def calculate_user_journeys(home_df, search_df, payment_df, confirmation_df):
    home_users = set(home_df['user_id'])
    search_users = set(search_df['user_id'])
    payment_users = set(payment_df['user_id'])
    confirmation_users = set(confirmation_df['user_id'])
    home_to_search = home_users.intersection(search_users)
    search_to_payment = search_users.intersection(payment_users)
    payment_to_confirmation = payment_users.intersection(confirmation_users)
    
    funnel_data = {
        'Stage': ['Home', 'Search', 'Payment', 'Confirmation'],
        'Users': [len(home_users), len(home_to_search), len(search_to_payment), len(payment_to_confirmation)]
    }
    
    funnel_df = pd.DataFrame(funnel_data)
    
    funnel_df['Conversion_Rate'] = [
        100.0,  
        round(len(home_to_search) / len(home_users) * 100, 2),  
        round(len(search_to_payment) / len(home_to_search) * 100, 2) if len(home_to_search) > 0 else 0,  
        round(len(payment_to_confirmation) / len(search_to_payment) * 100, 2) if len(search_to_payment) > 0 else 0 
    ]
    funnel_df['Drop_Off_Rate'] = [
        0,  
        round(100 - funnel_df.loc[1, 'Conversion_Rate'], 2),  
        round(100 - funnel_df.loc[2, 'Conversion_Rate'], 2),  
        round(100 - funnel_df.loc[3, 'Conversion_Rate'], 2)   
    ]
    
    overall_conversion = round(len(payment_to_confirmation) / len(home_users) * 100, 2) if len(home_users) > 0 else 0
    
    return funnel_df, overall_conversion, {
        'home_users': home_users,
        'search_users': search_users,
        'payment_users': payment_users,
        'confirmation_users': confirmation_users,
        'home_to_search': home_to_search,
        'search_to_payment': search_to_payment,
        'payment_to_confirmation': payment_to_confirmation
    }

def segment_by_attribute(home_df, search_df, payment_df, confirmation_df, user_df, attribute):
    if attribute not in user_df.columns:
        print(f"Error: {attribute} is not a valid column in user_df")
        return None

    unique_values = user_df[attribute].unique()
    
    results = {}
    
    for value in unique_values:
        filtered_users = user_df[user_df[attribute] == value]['user_id']
        
        
        filtered_home = home_df[home_df['user_id'].isin(filtered_users)]
        filtered_search = search_df[search_df['user_id'].isin(filtered_users)]
        filtered_payment = payment_df[payment_df['user_id'].isin(filtered_users)]
        filtered_confirmation = confirmation_df[confirmation_df['user_id'].isin(filtered_users)]
        
       
        funnel_df, overall_conversion, _ = calculate_user_journeys(
            filtered_home, filtered_search, filtered_payment, filtered_confirmation
        )
        
        results[value] = {
            'funnel_df': funnel_df,
            'overall_conversion': overall_conversion,
            'counts': {
                'home': len(filtered_home),
                'search': len(filtered_search),
                'payment': len(filtered_payment),
                'confirmation': len(filtered_confirmation)
            }
        }
    
    return results

def identify_new_users(user_df, days_threshold=7):
    if 'date' not in user_df.columns:
        raise ValueError("user_df precisa ter a coluna 'date'.")

    # 🔥 Forçar transformação para datetime SEMPRE aqui
    try:
        user_df['date'] = pd.to_datetime(user_df['date'], errors='coerce')
    except Exception as e:
        raise ValueError(f"Erro convertendo 'date' para datetime: {e}")

    # 🔥 Agora a data é garantidamente datetime
    max_date = user_df['date'].max()

    if pd.isnull(max_date):
        raise ValueError("Nenhuma data válida encontrada em user_df['date'].")

    new_users = user_df[user_df['date'] >= (max_date - pd.Timedelta(days=days_threshold))]
    existing_users = user_df[user_df['date'] < (max_date - pd.Timedelta(days=days_threshold))]

    return new_users, existing_users


