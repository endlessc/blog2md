from .toutiao import ToutiaoScraper
from .weixin import WeixinScraper
from .juejin import JuejinScraper
from .generic import GenericScraper

# Registry of specialized scrapers
# Order matters: specific first, generic last
SCRAPERS = [
    ToutiaoScraper(),
    WeixinScraper(),
    JuejinScraper(),
    GenericScraper()
]

def get_scraper(url):
    for scraper in SCRAPERS:
        if scraper.can_handle(url):
            return scraper
    return SCRAPERS[-1] # Should be generic
