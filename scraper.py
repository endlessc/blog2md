from scrapers import get_scraper, GenericScraper

def fetch_content(url):
    """
    抓取URL内容并提取标题和正文
    Delegates to the appropriate scraper adapter.
    """
    scraper = get_scraper(url)
    print(f"Using scraper: {scraper.__class__.__name__}")
    
    result = scraper.fetch(url)
    
    # If specific scraper fails, try GenericScraper as fallback
    if not result and not isinstance(scraper, GenericScraper):
        print(f"Specific scraper {scraper.__class__.__name__} failed, falling back to GenericScraper...")
        scraper = GenericScraper()
        result = scraper.fetch(url)
        
    if not result:
        raise Exception("Failed to fetch content with available scrapers.")
        
    return result
