#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据处理脚本
"""

import os
import re

def test_read_articles():
    """测试读取文章文件"""
    articles_dir = 'articles'
    articles = []

    if not os.path.exists(articles_dir):
        print(f"✗ 文件夹不存在: {articles_dir}")
        return articles

    count = 0
    for filename in os.listdir(articles_dir)[:5]:  # 只测试前5个文件
        if filename.endswith('.txt'):
            filepath = os.path.join(articles_dir, filename)

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                title = filename.replace('.txt', '')
                articles.append({
                    'title': title,
                    'content': content[:100] + '...',  # 只显示前100字符
                    'file_path': filepath,
                    'type': 'text'
                })
                count += 1
                print(f"[OK] 成功读取: {filename}")

            except Exception as e:
                print(f"[ERROR] 读取文件失败 {filename}: {e}")

    print(f"\n总共成功读取 {count} 个文件")
    return articles

def test_parse_sentiment():
    """测试解析情感分析结果"""
    try:
        with open('sentiment_analysis_results.txt', 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = r'^\d+\.\s+(.+?)\s+\(得分:\s+(-?\d+\.\d+)\)'
        matches = re.findall(pattern, content, re.MULTILINE)

        print(f"[OK] 找到 {len(matches)} 条情感分析记录")

        # 显示前5条记录
        for i, (title, score) in enumerate(matches[:5]):
            print(f"{i+1}. {title[:50]}... (得分: {score})")

        return matches

    except Exception as e:
        print(f"[ERROR] 解析情感分析结果失败: {e}")
        return []

def main():
    print("=" * 50)
    print("测试数据读取功能")
    print("=" * 50)

    print("\n1. 测试读取文章文件:")
    articles = test_read_articles()

    print("\n2. 测试解析情感分析结果:")
    sentiment_matches = test_parse_sentiment()

    print("\n3. 测试数据匹配:")
    if articles and sentiment_matches:
        sentiment_dict = {title: float(score) for title, score in sentiment_matches}

        for article in articles[:3]:
            title = article['title']
            found_match = False

            # 直接匹配
            if title in sentiment_dict:
                print(f"[OK] 直接匹配: {title}")
                found_match = True
            else:
                # 模糊匹配
                for sentiment_title in sentiment_dict.keys():
                    if title.lower() in sentiment_title.lower() or sentiment_title.lower() in title.lower():
                        print(f"[OK] 模糊匹配: {title} -> {sentiment_title[:50]}...")
                        found_match = True
                        break

            if not found_match:
                print(f"[ERROR] 未找到匹配: {title}")

if __name__ == "__main__":
    main()