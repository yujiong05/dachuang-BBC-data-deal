#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys
from tqdm import tqdm
import time
from bbc_crawler import extract_article_content, session
from config import BATCH_SIZE, BATCH_PAUSE, TARGET_ARTICLE_COUNT

def load_search_results(filename='advanced_search_results.json'):
    """加载搜索结果"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {filename}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"错误: 无法解析JSON文件 {filename}")
        sys.exit(1)

def main():
    """主函数"""
    print("从搜索结果下载BBC中国航天文章")
    print("-" * 35)
    
    # 确定结果文件名
    if len(sys.argv) > 1:
        results_file = sys.argv[1]
    else:
        # 尝试寻找可能的结果文件
        if os.path.exists('advanced_search_results.json'):
            results_file = 'advanced_search_results.json'
        elif os.path.exists('search_results.json'):
            results_file = 'search_results.json'
        else:
            print("请提供搜索结果文件路径作为参数")
            print("例如: python download_from_results.py advanced_search_results.json")
            sys.exit(1)
    
    # 加载搜索结果
    articles = load_search_results(results_file)
    
    print(f"已加载 {len(articles)} 篇文章的搜索结果")
    
    # 限制文章数量
    if len(articles) > TARGET_ARTICLE_COUNT:
        print(f"限制下载数量为 {TARGET_ARTICLE_COUNT} 篇文章")
        articles_to_process = articles[:TARGET_ARTICLE_COUNT]
    else:
        articles_to_process = articles
    
    # 下载文章
    successful_articles = []
    
    for i, article in enumerate(tqdm(articles_to_process, desc="下载文章")):
        result = extract_article_content(article['url'], article['title'])
        if result:
            successful_articles.append(result)
            
        # 每处理一批次文章休息
        if (i + 1) % BATCH_SIZE == 0:
            time.sleep(BATCH_PAUSE)
    
    print(f"\n成功下载 {len(successful_articles)} 篇文章")
    
    # 保存下载报告
    with open('download_report.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_articles': len(successful_articles),
            'articles': successful_articles
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main() 