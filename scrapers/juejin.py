import requests
import re
import json
from .base import BaseScraper

class JuejinScraper(BaseScraper):
    def can_handle(self, url):
        return "juejin.cn" in url

    def fetch(self, url):
        # Extract ID
        match = re.search(r'post/(\d+)', url)
        if not match:
            return None
        
        # Juejin is tricky with simple requests because of heavy anti-bot.
        # However, sometimes we can extract data from window.__NUXT__ if we are lucky with the initial HTML.
        # Or we can try the API if we can sign it (hard).
        # Let's try simple HTML parsing first, as Juejin often returns SSR HTML for SEO.
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = self._get_soup(response.text)
            
            title = soup.title.string if soup.title else ""
            if not title:
                h1 = soup.find('h1', class_='article-title')
                if h1:
                    title = h1.get_text()
            
            # Content
            article = soup.find('article')
            if not article:
                article = soup.find('div', class_='markdown-body')
                
            if article:
                clean_content = self._clean_html(str(article), url)
                return {
                    'title': self.clean_text(title),
                    'content': clean_content,
                    'url': url
                }
            
            # If HTML parsing fails, check for __NUXT__
            # (Note: This might be compressed/obfuscated in newer versions)
            
        except Exception as e:
            print(f"Juejin fetch error: {e}")
            
        return None
