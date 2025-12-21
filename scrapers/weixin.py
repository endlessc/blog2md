import requests
from .base import BaseScraper

class WeixinScraper(BaseScraper):
    def can_handle(self, url):
        return "mp.weixin.qq.com" in url

    def fetch(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = self._get_soup(response.text)
            
            # WeChat titles are usually in meta og:title or h1
            title = ""
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title = og_title.get('content')
            if not title:
                h1 = soup.find('h1', class_='rich_media_title')
                if h1:
                    title = h1.get_text()
            
            # Content is usually in #js_content
            content_div = soup.find('div', {'id': 'js_content'})
            if not content_div:
                # Fallback
                content_div = soup.find('div', class_='rich_media_content')
            
            if content_div:
                # WeChat specific image handling
                # They use data-src="url" and often don't have src, or src is a spacer
                for img in content_div.find_all('img'):
                    if 'data-src' in img.attrs:
                        img['src'] = img['data-src']
                        del img['data-src']
                    # Some wechat images have data-type (jpeg, png etc) but the URL usually doesn't have ext
                    # Our image downloader handles ext detection from content-type header, so we are good.
                
                clean_content = self._clean_html(str(content_div), url)
                return {
                    'title': self.clean_text(title),
                    'content': clean_content,
                    'url': url
                }
                
        except Exception as e:
            print(f"Weixin fetch error: {e}")
            
        return None
