import requests
from bs4 import BeautifulSoup
import json
import re

# 提取文章 ID
article_id = "7581339815015956992"
# 尝试使用 API 端点
# 注意：头条 API 经常变动，这是一个常见的移动端接口
api_url = f"https://m.toutiao.com/i{article_id}/info/"
# 或者尝试直接访问移动端页面，有时候它会直接渲染 (取决于 IP 和 Header)
mobile_page_url = f"https://m.toutiao.com/i{article_id}/"

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    # Referer 非常重要
    'Referer': f'https://m.toutiao.com/i{article_id}/' 
}

try:
    print(f"Fetching Mobile Page {mobile_page_url}...")
    response = requests.get(mobile_page_url, headers=headers, timeout=15, allow_redirects=True)
    print(f"Status Code: {response.status_code}")
    
    html = response.text
    print(f"HTML Length: {len(html)}")
    
    with open("toutiao_mobile_page.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    # 检查是否依然是验证页面
    if "byted_acrawler" in html:
        print("⚠️ Still getting validation page (acrawler).")
    
    # 尝试查找正文 (如果运气好直接渲染了)
    soup = BeautifulSoup(html, 'html.parser')
    # 移动端正文通常在 article 或者 div.article-content
    article = soup.find('article')
    if article:
        print("✅ Found <article> tag in mobile page")
    
    # 尝试查找 script 中的 JSON
    # 头条移动端常把数据放在 <script id="RENDER_DATA" type="application/json">
    render_data = soup.find('script', {'id': 'RENDER_DATA'})
    if render_data:
        print("✅ Found RENDER_DATA script!")
        try:
            import urllib.parse
            # 数据通常是 URL 编码的 JSON
            data_str = urllib.parse.unquote(render_data.string)
            data = json.loads(data_str)
            print("✅ Successfully parsed RENDER_DATA JSON")
            # 尝试提取 content
            # 结构通常是: data -> articleInfo -> content
            if 'articleInfo' in data:
                content = data['articleInfo'].get('content', '')
                print(f"Extracted content length: {len(content)}")
        except Exception as e:
            print(f"Failed to parse RENDER_DATA: {e}")
            
except Exception as e:
    print(f"Error: {e}")
