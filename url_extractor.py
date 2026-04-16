import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_content_from_url(url: str, timeout: int = 30) -> dict:
    if not is_valid_url(url):
        raise ValueError(f"无效的URL: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except requests.exceptions.RequestException as e:
        raise Exception(f"请求URL失败: {e}")
    
    soup = BeautifulSoup(response.content, 'lxml')
    
    for script in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
        script.decompose()
    
    title = ""
    if soup.title:
        title = soup.title.string.strip() if soup.title.string else ""
    
    article_tags = soup.find_all('article')
    if article_tags:
        main_content = ' '.join([tag.get_text(separator='\n', strip=True) for tag in article_tags])
    else:
        main_content_selectors = [
            'div[class*="content"]',
            'div[class*="article"]',
            'div[class*="post"]',
            'div[class*="main"]',
            'main',
            'section[class*="content"]',
        ]
        
        main_content = ""
        for selector in main_content_selectors:
            elements = soup.select(selector)
            if elements:
                main_content = ' '.join([el.get_text(separator='\n', strip=True) for el in elements])
                break
        
        if not main_content:
            paragraphs = soup.find_all('p')
            main_content = '\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
    
    main_content = re.sub(r'\n{3,}', '\n\n', main_content)
    main_content = re.sub(r' +', ' ', main_content)
    main_content = main_content.strip()
    
    if not main_content:
        main_content = soup.get_text(separator='\n', strip=True)
        main_content = re.sub(r'\n{3,}', '\n\n', main_content)
    
    return {
        'title': title,
        'content': main_content,
        'url': url,
        'full_text': f"标题: {title}\n\n来源: {url}\n\n内容:\n{main_content}" if title else f"来源: {url}\n\n内容:\n{main_content}"
    }

if __name__ == "__main__":
    test_url = "https://example.com"
    try:
        result = extract_content_from_url(test_url)
        print("URL内容提取测试:")
        print(f"标题: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"内容长度: {len(result['content'])} 字符")
        print("\n内容预览:")
        print(result['content'][:500] if len(result['content']) > 500 else result['content'])
    except Exception as e:
        print(f"测试失败: {e}")
