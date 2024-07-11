from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='templates')

# Define the API key and endpoint
proxycurl_api_key = 'YOUR_API_KEY'
headers = {'Authorization': 'Bearer ' + proxycurl_api_key}
api_endpoint = 'https://nubela.co/proxycurl/api/v2/search/person'

# Function to update API parameters with user input
def update_params_with_business_need(params, business_need):
    params.update({
        'industries': f'NOT {business_need}',
        'current_job_description': f'NOT {business_need}',
        'summary': f'NOT {business_need}',
        'past_job_description': f'NOT {business_need}',
    })
    return params

# Function to make API request and get the first round of profiles
def get_first_round_profiles(api_endpoint, headers, params):
    profiles = []
    next_page = api_endpoint
    while next_page:
        response = requests.get(next_page, headers=headers, params=params)
        data = response.json()
        profiles.extend(data.get('results', []))
        next_page = data.get('next_page')
    return profiles

# Function to filter profiles based on specific role titles
def filter_profiles_by_role_titles(profiles, desired_titles):
    filtered_profiles = [profile for profile in profiles if profile['current_role_title'] in desired_titles]
    return filtered_profiles

# Function to check if a company has moved up in size group in the last 3 months
def has_company_moved_up_recently(company):
    current_date = datetime.now()
    three_months_ago = current_date - timedelta(days=90)
    
    company_size_history = {
        'CompanyA': [('2023-01-01', 'Group 1'), ('2023-04-01', 'Group 2')],
    }
    
    if company in company_size_history:
        history = company_size_history[company]
        for date, size_group in history:
            if datetime.strptime(date, '%Y-%m-%d') > three_months_ago and size_group in ['Group 2', 'Group 3', 'Group 4']:
                return True
    return False

# Function to score profiles based on the absence of business_need in different fields
def score_profiles(profiles, business_need):
    scored_profiles = []
    for profile in profiles:
        score = 0
        if business_need not in profile.get('industries', ''):
            score += 2
        if business_need not in profile.get('current_job_description', ''):
            score += 2
        if business_need not in profile.get('summary', ''):
            score += 1
        if business_need not in profile.get('past_job_description', ''):
            score += 1
        
        company = profile.get('current_company_name', '')
        if has_company_moved_up_recently(company):
            score += 3

        scored_profiles.append((profile, score))
    return scored_profiles

# Function to categorize profiles into tiers based on their scores and recent company size changes
def categorize_profiles_by_score(scored_profiles):
    scored_profiles.sort(key=lambda x: x[1], reverse=True)
    
    whales = [profile for profile, score in scored_profiles if has_company_moved_up_recently(profile.get('current_company_name', ''))]
    hot_leads = [profile for profile, score in scored_profiles if score == 6 and profile not in whales]
    warm_leads = [profile for profile, score in scored_profiles if score == 5 and profile not in whales]
    potential_leads = [profile for profile, score in scored_profiles if score == 4 and profile not in whales]
    
    return whales, hot_leads, warm_leads, potential_leads

@app.route('/leadgen', methods=['GET', 'POST'])
def leadgen():
    if request.method == 'POST':
        business_need = request.form['business_need']
        params = {
            'country': 'US',
        }
        params = update_params_with_business_need(params, business_need)
        first_round_profiles = get_first_round_profiles(api_endpoint, headers, params)
        desired_titles = ['founder', 'CEO', 'Sales', 'COO', 'CTO', 'BDO', 'SDR']
        second_round_profiles = filter_profiles_by_role_titles(first_round_profiles, desired_titles)
        scored_profiles = score_profiles(second_round_profiles, business_need)
        whales, hot_leads, warm_leads, potential_leads = categorize_profiles_by_score(scored_profiles)
        return render_template('leadgen_results.html', whales=whales, hot_leads=hot_leads, warm_leads=warm_leads, potential_leads=potential_leads)
    return render_template('leadgen.html')

if __name__ == '__main__':
    app.run(debug=True)