import requests
from .base import BaseScraper

class GenericScraper(BaseScraper):
    def can_handle(self, url):
        return True # Catch-all

    def fetch(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Handle encoding
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            soup = self._get_soup(response.text)
            
            title = soup.title.string if soup.title else "Untitled"
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text()
            
            # Heuristic to find main content
            main_content = soup.find('article')
            if not main_content:
                main_content = soup.find('main')
            if not main_content:
                # Try common class names
                for class_name in ['post-content', 'article-content', 'entry-content', 'content']:
                    main_content = soup.find(class_=class_name)
                    if main_content: break
            
            if not main_content:
                main_content = soup.body if soup.body else soup
                
            clean_content = self._clean_html(str(main_content), url)
            
            return {
                'title': self.clean_text(title),
                'content': clean_content,
                'url': url
            }
            
        except Exception as e:
            print(f"Generic fetch error: {e}")
            raise e
