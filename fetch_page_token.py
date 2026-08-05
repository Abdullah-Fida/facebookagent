import requests
import re
from core.config import load_config

config = load_config()
user_token = config.facebook_access_token

print("Fetching pages...")
r = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?access_token={user_token}")
data = r.json()

if 'data' in data:
    for page in data['data']:
        print(f"Found Page: {page['name']} (ID: {page['id']})")
        if page['name'] == 'Zindagi Ke Rang' or page['id'] == '61593052854572':
            page_token = page['access_token']
            print("\nSuccessfully found the Page Access Token for Zindagi Ke Rang!")
            
            # Update the .env file with this new token
            with open('.env', 'r') as f:
                env_content = f.read()
                
            env_content = re.sub(
                r'FACEBOOK_ACCESS_TOKEN=".*"', 
                f'FACEBOOK_ACCESS_TOKEN="{page_token}"', 
                env_content
            )
            
            with open('.env', 'w') as f:
                f.write(env_content)
                
            print("Successfully updated .env with the new Page Token.")
            break
else:
    print("No pages found or error:")
    print(data)
