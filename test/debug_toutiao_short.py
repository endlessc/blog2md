import requests
import re

url = "https://m.toutiao.com/is/Xcf8MG3bizI/"

print(f"Testing URL: {url}")

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
}

try:
    # First, let's see where it redirects
    response = requests.head(url, headers=headers, allow_redirects=True)
    print(f"Final URL (HEAD): {response.url}")
    
    # If HEAD doesn't work well (sometimes servers block it or don't redirect same way), try GET
    response_get = requests.get(url, headers=headers, allow_redirects=True)
    print(f"Final URL (GET): {response_get.url}")
    
    # Check if we can extract ID from the final URL
    match = re.search(r'(article|group|i)/(\d+)', response_get.url)
    if match:
        print(f"Found ID: {match.group(2)}")
    else:
        print("ID pattern not found in final URL")
        
except Exception as e:
    print(f"Error: {e}")
