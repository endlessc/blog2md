import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

class BaseScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def can_handle(self, url):
        """
        Check if this scraper can handle the given URL.
        """
        return False

    def fetch(self, url):
        """
        Fetch content from the URL.
        Returns a dictionary with 'title', 'content', and 'url'.
        """
        raise NotImplementedError

    def clean_text(self, text):
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()

    def _get_soup(self, html_content):
        return BeautifulSoup(html_content, 'html.parser')

    def _clean_html(self, html_content, url, target_tag=None):
        """
        Common HTML cleaning logic.
        """
        soup = self._get_soup(html_content)
        
        # Remove unwanted tags
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'noscript', 'header', 'aside']):
            element.decompose()
        
        target = soup
        if target_tag:
            found = soup.find(target_tag)
            if found:
                target = found
            elif soup.body:
                target = soup.body

        # Clean attributes
        for tag in target.find_all(True):
            self._clean_tag_attributes(tag, url)
            
        return str(target)

    def _clean_tag_attributes(self, tag, base_url):
        if tag.name == 'img':
            allowed = ['src', 'alt', 'data-src', 'data-original', 'data-url']
            attrs = {k: v for k, v in tag.attrs.items() if k in allowed}
            tag.attrs = attrs
            
            # Handle lazy loading common patterns
            possible_srcs = ['data-src', 'data-original', 'data-url']
            for attr in possible_srcs:
                if attr in tag.attrs:
                    tag['src'] = tag[attr]
                    del tag[attr]
                    break
            
            if tag.get('src'):
                tag['src'] = urljoin(base_url, tag['src'])
                
        elif tag.name == 'a':
            allowed = ['href', 'title']
            attrs = {k: v for k, v in tag.attrs.items() if k in allowed}
            tag.attrs = attrs
            if tag.get('href'):
                tag['href'] = urljoin(base_url, tag['href'])
        else:
            tag.attrs = {}
