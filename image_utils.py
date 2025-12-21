import os
import re
import requests
import hashlib
from urllib.parse import urlparse

def download_image(url, save_folder):
    """
    下载图片并保存到指定文件夹
    返回保存的文件名，如果失败返回 None
    """
    try:
        # 简单的防盗链处理
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, stream=True, timeout=15)
        response.raise_for_status()
        
        # 使用 URL 哈希作为文件名，避免特殊字符和重名
        hash_name = hashlib.md5(url.encode()).hexdigest()
        
        # 尝试从 Content-Type 获取扩展名
        content_type = response.headers.get('content-type', '').lower()
        ext = '.jpg' # 默认扩展名
        if 'png' in content_type: ext = '.png'
        elif 'gif' in content_type: ext = '.gif'
        elif 'jpeg' in content_type or 'jpg' in content_type: ext = '.jpg'
        elif 'svg' in content_type: ext = '.svg'
        elif 'webp' in content_type: ext = '.webp'
        
        # 如果 URL 中有明确的扩展名，优先使用 URL 的 (防止 Content-Type 不准确)
        path = urlparse(url).path
        if path:
            _, url_ext = os.path.splitext(path)
            if url_ext and url_ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']:
                ext = url_ext.lower()
            
        filename = f"{hash_name}{ext}"
        filepath = os.path.join(save_folder, filename)
        
        # 如果文件已存在，直接返回 (避免重复下载)
        if os.path.exists(filepath):
            return filename
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
                
        return filename
    except Exception as e:
        print(f"Warning: Failed to download image {url}: {e}")
        return None

def process_markdown_images(markdown_content, base_folder, assets_dir_name="assets"):
    """
    扫描 Markdown 内容中的图片链接，下载图片，并替换为本地相对路径
    """
    assets_path = os.path.join(base_folder, assets_dir_name)
    if not os.path.exists(assets_path):
        os.makedirs(assets_path)
        
    # 匹配 Markdown 图片语法: ![alt](url "title")
    # 简单的正则，可能无法处理极其复杂的嵌套括号，但对标准 Markdown 足够
    pattern = r'!\[(.*?)\]\((.*?)\)'
    
    def replace_match(match):
        alt_text = match.group(1)
        full_url_part = match.group(2)
        
        # 处理可能存在的 title 部分: "http://example.com/img.jpg \"Image Title\""
        # 简单分割，取第一部分作为 URL
        parts = full_url_part.split(maxsplit=1)
        url = parts[0].strip()
        title_part = ""
        if len(parts) > 1:
            title_part = " " + parts[1]
            
        # 跳过非 HTTP 链接
        if not url.startswith(('http://', 'https://')):
            return match.group(0)
            
        print(f"Downloading image: {url}")
        filename = download_image(url, assets_path)
        
        if filename:
            # 使用相对路径
            relative_path = f"{assets_dir_name}/{filename}"
            return f"![{alt_text}]({relative_path}{title_part})"
        else:
            return match.group(0)
            
    new_content = re.sub(pattern, replace_match, markdown_content)
    return new_content
