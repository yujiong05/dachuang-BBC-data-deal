#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import random
import requests
import urllib.parse
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
import json
import hashlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import ssl
from config import *

# 创建文件夹
os.makedirs(ARTICLES_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# 已下载的URL列表，避免重复下载
downloaded_urls = set()

# 已下载的图片和视频URL，避免重复下载
downloaded_media_urls = set()

# 创建会话对象，保持连接
session = requests.Session()

# 配置重试策略
retry_strategy = Retry(
    total=5,  # 最大重试次数
    backoff_factor=1,  # 重试间隔
    status_forcelist=[500, 502, 503, 504, 429],  # 需要重试的HTTP状态码
)

# 创建适配器并添加到会话
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# 更新请求头
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
})

# 禁用SSL验证警告
requests.packages.urllib3.disable_warnings()

def generate_filename(url, title=None, extension='.txt'):
    """生成唯一的文件名"""
    if title:
        # 移除不合法的文件名字符
        title = re.sub(r'[\\/*?:"<>|]', "", title)
        title = title.strip()
        if len(title) > 100:
            title = title[:100]  # 限制长度
        
        # 如果标题为空，使用URL的哈希值
        if not title:
            title = hashlib.md5(url.encode()).hexdigest()
        
        return f"{title}{extension}"
    else:
        return f"{hashlib.md5(url.encode()).hexdigest()}{extension}"

def get_article_title(soup):
    """从文章页面提取标题"""
    # 尝试多种可能的标题选择器
    title_selectors = [
        'h1.ssrcss-15xko80-StyledHeading',
        'h1.ssrcss-1f3bvyz-Headline',
        'h1.article__title',
        'h1.story-body__h1',
        'h1.article-headline',
        'h1.headline',
        'h1.title',
        'h1',
        'h2.ssrcss-15xko80-StyledHeading',
        'h2.ssrcss-1f3bvyz-Headline',
        'h2.article__title',
        'h2.story-body__h1',
        'h2.article-headline',
        'h2.headline',
        'h2.title',
        'h2'
    ]
    
    for selector in title_selectors:
        title_elem = soup.select_one(selector)
        if title_elem:
            title = title_elem.text.strip()
            if title and title != "BBC News":
                return title
    
    # 如果找不到标题，尝试从meta标签获取
    meta_title = soup.select_one('meta[property="og:title"]')
    if meta_title:
        title = meta_title.get('content', '').strip()
        if title and title != "BBC News":
            return title
    
    # 尝试从URL中提取标题
    url_title = soup.select_one('meta[property="og:url"]')
    if url_title:
        url = url_title.get('content', '')
        if url:
            # 从URL中提取最后一个路径部分
            url_parts = url.rstrip('/').split('/')
            if url_parts:
                title = url_parts[-1].replace('-', ' ').strip()
                if title:
                    return title
    
    return None

def search_articles(keyword, start_page=1, max_pages=MAX_PAGES_PER_KEYWORD):
    """搜索BBC关于中国航天的文章"""
    articles = []
    
    for page in range(start_page, start_page + max_pages):
        try:
            params = {
                'q': keyword,
                'page': page
            }
            
            # 添加verify=False参数禁用SSL验证
            response = session.get(BBC_NEWS_URL, params=params, verify=False, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            search_results = soup.select('div.ssrcss-1v7bxtk-StyledContainer')
            
            if not search_results:
                search_results = soup.select('div.ssrcss-1qt4x4l-PromoContent')
            
            if not search_results:
                # 尝试寻找其他可能的文章容器
                search_results = soup.select('div.PromoContent')
            
            if not search_results:
                print(f"未在第{page}页找到结果，可能已到达最后一页或搜索格式已更改")
                break
                
            for result in search_results:
                link_elem = result.find('a')
                if not link_elem:
                    continue
                    
                article_url = link_elem.get('href')
                if not article_url:
                    continue
                
                # 确保URL是绝对路径
                if article_url.startswith('/'):
                    article_url = urljoin(BBC_URL, article_url)
                
                # 检查是否已下载过
                if article_url in downloaded_urls:
                    continue
                
                # 提取标题
                title_elem = result.select_one('h3') or result.select_one('h2') or result.select_one('span.promo-heading__title')
                title = title_elem.text.strip() if title_elem else "No Title"
                
                articles.append({
                    'url': article_url,
                    'title': title
                })
            
            # 随机休眠，避免请求过快
            time.sleep(random.uniform(REQUEST_DELAY[0], REQUEST_DELAY[1]))
            
        except Exception as e:
            print(f"搜索页面{page}时出错: {e}")
            time.sleep(BATCH_PAUSE)  # 出错后等待更长时间
    
    return articles

def download_image(img_url, article_dir):
    """下载图片"""
    if img_url in downloaded_media_urls:
        return None
        
    try:
        # 确保URL是绝对路径
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif img_url.startswith('/'):
            img_url = urljoin(BBC_URL, img_url)
            
        # 添加verify=False参数禁用SSL验证
        response = session.get(img_url, stream=True, verify=False, timeout=30)
        response.raise_for_status()
        
        # 获取文件扩展名
        content_type = response.headers.get('Content-Type', '')
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        elif 'gif' in content_type:
            ext = '.gif'
        elif 'webp' in content_type:
            ext = '.webp'
        else:
            ext = '.jpg'  # 默认扩展名
        
        # 生成图片文件名
        img_filename = f"{hashlib.md5(img_url.encode()).hexdigest()}{ext}"
        img_path = os.path.join(IMAGES_DIR, img_filename)
        
        # 保存图片
        with open(img_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        downloaded_media_urls.add(img_url)
        return img_filename
        
    except Exception as e:
        print(f"下载图片失败: {img_url}, 错误: {e}")
        return None

def download_video(video_url, article_dir):
    """下载视频"""
    if video_url in downloaded_media_urls:
        return None
        
    try:
        # 确保URL是绝对路径
        if video_url.startswith('//'):
            video_url = 'https:' + video_url
        elif video_url.startswith('/'):
            video_url = urljoin(BBC_URL, video_url)
            
        # 添加verify=False参数禁用SSL验证
        response = session.get(video_url, stream=True, verify=False, timeout=30)
        response.raise_for_status()
        
        # 获取文件扩展名
        content_type = response.headers.get('Content-Type', '')
        if 'mp4' in content_type:
            ext = '.mp4'
        elif 'webm' in content_type:
            ext = '.webm'
        else:
            ext = '.mp4'  # 默认扩展名
        
        # 生成视频文件名
        video_filename = f"{hashlib.md5(video_url.encode()).hexdigest()}{ext}"
        video_path = os.path.join(VIDEOS_DIR, video_filename)
        
        # 保存视频
        with open(video_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        downloaded_media_urls.add(video_url)
        return video_filename
        
    except Exception as e:
        print(f"下载视频失败: {video_url}, 错误: {e}")
        return None

def extract_article_content(url, title):
    """提取文章内容、图片和视频"""
    try:
        # 添加verify=False参数禁用SSL验证
        response = session.get(url, verify=False, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 获取文章标题
        article_title = get_article_title(soup)
        if not article_title:
            article_title = title if title != "No Title" else None
        
        # 查找文章主体
        article_body = None
        body_selectors = [
            'article',
            'div.ssrcss-1ocoo3l-Wrap',
            'div.story-body__inner',
            'div.article__body',
            'div.article-body',
            'div.article-content',
            'div.article-text',
            'div.article-body-content',
            'div.article__body-content',
            'div.article__content'
        ]
        
        for selector in body_selectors:
            article_body = soup.select_one(selector)
            if article_body:
                break
        
        if not article_body:
            # 如果找不到标准文章主体，尝试查找包含段落文本的容器
            text_containers = soup.select('div[class*="content"] p, div[class*="body"] p, div[class*="text"] p')
            if text_containers:
                # 创建一个新的div来包含所有段落
                article_body = soup.new_tag('div')
                for p in text_containers:
                    article_body.append(p)
        
        if not article_body:
            print(f"无法找到文章主体: {url}")
            return None
            
        # 提取文章段落
        paragraphs = []
        for p in article_body.select('p'):
            # 排除不相关的段落
            if 'footer' in str(p.parent).lower() or 'caption' in str(p.parent).lower():
                continue
            text = p.get_text().strip()
            if text:
                paragraphs.append(text)
        
        # 如果没有找到任何段落，尝试直接获取所有文本
        if not paragraphs:
            text = article_body.get_text().strip()
            if text:
                paragraphs = [text]
        
        if not paragraphs:
            print(f"无法提取文章内容: {url}")
            return None
        
        # 提取图片
        images = []
        for img in article_body.select('img'):
            # 忽略小图标和广告图片
            if img.get('width') and int(img.get('width')) < 100:
                continue
                
            img_url = img.get('src')
            if not img_url:
                continue
                
            img_filename = download_image(img_url, IMAGES_DIR)
            if img_filename:
                # 获取图片说明
                figcaption = img.find_parent('figure').find('figcaption') if img.find_parent('figure') else None
                caption = figcaption.text.strip() if figcaption else "无说明"
                
                images.append({
                    'url': img_url,
                    'filename': img_filename,
                    'caption': caption
                })
        
        # 提取视频
        videos = []
        video_elements = article_body.select('video') + article_body.select('iframe[src*="player"]')
        
        # 尝试查找可能包含视频的div元素
        video_containers = article_body.select('div[data-e2e="media-player"]')
        for container in video_containers:
            video_elem = container.select_one('video') or container.select_one('iframe')
            if video_elem:
                video_elements.append(video_elem)
        
        for video in video_elements:
            video_url = video.get('src')
            if not video_url:
                continue
                
            video_filename = download_video(video_url, VIDEOS_DIR)
            if video_filename:
                videos.append({
                    'url': video_url,
                    'filename': video_filename
                })
        
        # 生成文章文件名
        article_filename = generate_filename(url, article_title)
        article_path = os.path.join(ARTICLES_DIR, article_filename)
        
        # 保存文章内容
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(f"标题: {article_title}\n")
            f.write(f"网址: {url}\n\n")
            f.write("正文内容:\n")
            f.write("\n\n".join(paragraphs))
            
            if images:
                f.write("\n\n图片列表:\n")
                for i, img in enumerate(images, 1):
                    f.write(f"{i}. {img['filename']} - {img['caption']}\n")
                    
            if videos:
                f.write("\n\n视频列表:\n")
                for i, vid in enumerate(videos, 1):
                    f.write(f"{i}. {vid['filename']}\n")
                    
        downloaded_urls.add(url)
        
        return {
            'filename': article_filename,
            'title': article_title,
            'images': len(images),
            'videos': len(videos)
        }
            
    except Exception as e:
        print(f"处理文章失败: {url}, 错误: {e}")
        return None

def main():
    """主函数"""
    all_articles = []
    no_title_counter = 1  # 用于无标题文章的编号
    
    # 遍历所有搜索关键词
    for keyword in SEARCH_KEYWORDS:
        print(f"\n搜索关键词: {keyword}")
        articles = search_articles(keyword)
        all_articles.extend(articles)
        print(f"找到 {len(articles)} 篇文章")
        
        # 每找到一个文章就立即下载
        for article in articles:
            print(f"\n处理文章: {article['title']}")
            result = extract_article_content(article['url'], article['title'])
            if result:
                if not result['title']:
                    # 如果文章没有标题，使用编号作为标题
                    result['title'] = f"Untitled Article {no_title_counter}"
                    no_title_counter += 1
                    # 重新生成文件名
                    article_filename = generate_filename(article['url'], result['title'])
                    article_path = os.path.join(ARTICLES_DIR, article_filename)
                    # 重命名文件
                    if os.path.exists(os.path.join(ARTICLES_DIR, result['filename'])):
                        os.rename(
                            os.path.join(ARTICLES_DIR, result['filename']),
                            article_path
                        )
                    result['filename'] = article_filename
                
                print(f"成功下载: {result['title']}")
                print(f"包含 {result['images']} 张图片和 {result['videos']} 个视频")
            time.sleep(random.uniform(REQUEST_DELAY[0], REQUEST_DELAY[1]))
    
    # 去重
    unique_articles = []
    unique_urls = set()
    
    for article in all_articles:
        if article['url'] not in unique_urls:
            unique_articles.append(article)
            unique_urls.add(article['url'])
    
    print(f"\n总共找到 {len(unique_articles)} 篇独特文章")
    
    # 保存下载记录
    with open('download_report.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_articles': len(unique_articles),
            'articles': unique_articles
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main() 