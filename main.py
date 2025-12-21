import os
import argparse
import sys
import re
from scraper import fetch_content
from converter import convert_to_markdown
from image_utils import process_markdown_images

def sanitize_filename(name):
    """
    将字符串转换为合法的文件名/文件夹名
    """
    # 替换非法字符
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # 将空格替换为下划线
    name = name.replace(" ", "_")
    # 限制长度
    return name[:100]

def process_url(url, base_output_dir="output", progress_callback=None):
    """
    Core logic to fetch, convert, and save a webpage.
    """
    def log(msg):
        if progress_callback:
            progress_callback(msg)
        else:
            print(msg)

    if not url:
        raise ValueError("No URL provided")

    log(f"Step 1/4: Fetching content from: {url} ...")
    data = fetch_content(url)
    log(f"Successfully fetched: {data['title']}")
    
    log("Step 2/4: Converting to Markdown and Analyzing Category (LLM)...")
    result = convert_to_markdown(data['content'], data['title'])
    
    category = result.get('category', 'Uncategorized')
    markdown_content = result.get('markdown_content', '')
    
    log(f"Category identified: {category}")
    
    # Prepare directory structure
    # Split category by '-' to create nested folders
    # Merge the first two parts (DDC Code + Root Category) to keep them together
    # E.g. "600-Applied_Sciences-Software-Java" -> "output/600-Applied_Sciences/Software/Java"
    category_parts = category.split('-')
    
    final_parts = []
    # Check if the first part is a 3-digit DDC code (e.g., 000, 600)
    if len(category_parts) >= 2 and category_parts[0].isdigit() and len(category_parts[0]) == 3:
         final_parts.append(f"{category_parts[0]}-{category_parts[1]}")
         final_parts.extend(category_parts[2:])
    else:
         final_parts = category_parts

    safe_category_parts = [sanitize_filename(part) for part in final_parts]
    
    category_dir = os.path.join(base_output_dir, *safe_category_parts)
    if not os.path.exists(category_dir):
        os.makedirs(category_dir)
        
    safe_title = sanitize_filename(data['title'])
    article_dir = os.path.join(category_dir, safe_title)
    if not os.path.exists(article_dir):
        os.makedirs(article_dir)
        
    log(f"Step 3/4: Processing images and downloading to: {article_dir}/assets ...")
    final_content = process_markdown_images(markdown_content, article_dir)
    
    log("Step 4/4: Saving file...")
    output_path = os.path.join(article_dir, "index.md")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        f.write(f"\n\n---\nOriginal URL: {url}\n")
        
    log(f"Done! Saved to: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Fetch a webpage and convert it to Markdown using LLM.")
    parser.add_argument("url", nargs="?", help="The URL of the webpage to convert")
    args = parser.parse_args()

    url = args.url
    if not url:
        url = input("Please enter the URL: ").strip()

    if not url:
        print("Error: No URL provided.")
        sys.exit(1)

    try:
        process_url(url)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
