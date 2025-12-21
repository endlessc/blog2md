import re
import json
import requests
from urllib.parse import unquote
from .base import BaseScraper

class ToutiaoScraper(BaseScraper):
    def can_handle(self, url):
        return "toutiao.com" in url

    def fetch(self, url):
        # Handle short links or redirects first
        if "toutiao.com/is/" in url:
            try:
                # Use HEAD first to be faster, but Toutiao might require GET
                # Let's just use GET with stream=True to avoid downloading body if possible, 
                # but we need the final URL.
                headers = {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
                }
                resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10, stream=True)
                url = resp.url
                resp.close()
            except Exception as e:
                print(f"Error resolving Toutiao short link: {e}")
        
        # Extract Article ID
        match = re.search(r'(article|group|i)/(\d+)', url)
        if not match:
            # Fallback to generic if ID not found, but realistically generic won't work well on toutiao PC
            return None
            
        article_id = match.group(2)
        mobile_url = f"https://m.toutiao.com/i{article_id}/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Referer': mobile_url,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
        }
        
        try:
            response = requests.get(mobile_url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            soup = self._get_soup(response.text)
            content = ""
            title = ""
            
            # Strategy 1: RENDER_DATA JSON
            render_data = soup.find('script', {'id': 'RENDER_DATA'})
            if render_data:
                try:
                    data_str = unquote(render_data.string)
                    data = json.loads(data_str)
                    if 'articleInfo' in data:
                        content = data['articleInfo'].get('content', '')
                        title = data['articleInfo'].get('title', '')
                except Exception:
                    pass
            
            # Strategy 2: HTML Fallback
            if not content:
                article = soup.find('article')
                if article:
                    content = str(article)
                else:
                    div = soup.find('div', class_='article-content')
                    if div:
                        content = str(div)
            
            if not title:
                title = soup.title.string if soup.title else "Toutiao Article"
                
            if content:
                clean_content = self._clean_html(content, mobile_url)
                return {
                    'title': self.clean_text(title),
                    'content': clean_content,
                    'url': mobile_url
                }
                
        except Exception as e:
            print(f"Toutiao fetch error: {e}")
            
        return None
