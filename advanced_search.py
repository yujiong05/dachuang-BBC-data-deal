#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import requests
from bs4 import BeautifulSoup
import json
import time
from config import *
from urllib.parse import urljoin
import random

def advanced_search(keyword, start_date=None, end_date=None, max_pages=5):
    """
    使用BBC高级搜索功能
    
    参数:
    - keyword: 搜索关键词
    - start_date: 开始日期 (YYYY-MM-DD)
    - end_date: 结束日期 (YYYY-MM-DD)
    - max_pages: 最大页数
    
    返回:
    - 符合条件的文章URL列表
    """
    articles = []
    
    # 创建会话
    session = requests.Session()
    session.headers.update(HEADERS)
    
    for page in range(1, max_pages + 1):
        try:
            # 构造高级搜索参数
            params = {
                'q': keyword,
                'page': page
            }
            
            # 添加日期筛选条件
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            # 添加类型筛选：新闻
            params['category'] = 'news'
            
            response = session.get(BBC_NEWS_URL, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 检查各种可能的结果容器
            search_results = (
                soup.select('div.ssrcss-1v7bxtk-StyledContainer') or 
                soup.select('div.ssrcss-1qt4x4l-PromoContent') or
                soup.select('div.PromoContent') or
                soup.select('div.search-results')
            )
            
            if not search_results:
                print(f"未在第{page}页找到结果")
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
                
                # 提取标题
                title_elem = (
                    result.select_one('h3') or 
                    result.select_one('h2') or 
                    result.select_one('span.promo-heading__title')
                )
                title = title_elem.text.strip() if title_elem else "No Title"
                
                articles.append({
                    'url': article_url,
                    'title': title
                })
            
            # 避免请求过快
            time.sleep(random.uniform(REQUEST_DELAY[0], REQUEST_DELAY[1]))
            
        except Exception as e:
            print(f"搜索页面{page}时出错: {e}")
    
    return articles

def save_search_results(results, filename='search_results.json'):
    """保存搜索结果到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"已保存 {len(results)} 个搜索结果到 {filename}")

def main():
    """主函数"""
    print("BBC中国航天高级搜索")
    print("-" * 30)
    
    # 定义搜索关键词和时间范围
    search_configs = [
        {
            'keyword': 'China space program',
            'start_date': '2010-01-01',
            'end_date': '2023-12-31'
        },
        {
            'keyword': 'Chinese space station',
            'start_date': '2015-01-01',
            'end_date': '2023-12-31'
        },
        {
            'keyword': 'China mars mission',
            'start_date': '2018-01-01',
            'end_date': '2023-12-31'
        },
        {
            'keyword': 'China moon mission',
            'start_date': '2013-01-01',
            'end_date': '2023-12-31'
        },
        {
            'keyword': 'China Chang\'e mission',
            'start_date': '2013-01-01',
            'end_date': '2023-12-31'
        }
    ]
    
    all_results = []
    
    for config in search_configs:
        print(f"\n搜索 '{config['keyword']}' ({config['start_date']} 至 {config['end_date']})")
        results = advanced_search(
            config['keyword'], 
            start_date=config['start_date'],
            end_date=config['end_date'],
            max_pages=10
        )
        print(f"找到 {len(results)} 篇文章")
        all_results.extend(results)
    
    # 去重
    unique_results = []
    unique_urls = set()
    
    for article in all_results:
        if article['url'] not in unique_urls:
            unique_results.append(article)
            unique_urls.add(article['url'])
    
    print(f"\n总共找到 {len(unique_results)} 篇独特文章")
    
    # 保存结果
    save_search_results(unique_results, 'advanced_search_results.json')
    
    print("\n您可以使用这些搜索结果作为爬虫的输入，以获得更精确的与中国航天相关的文章。")
    print("使用方法: 将advanced_search_results.json文件作为bbc_crawler.py的输入。")

if __name__ == "__main__":
    main() 