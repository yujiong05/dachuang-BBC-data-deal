#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证关键词数据导入结果
"""

import mysql.connector

# 数据库配置
DB_CONFIG = {
    'user': 'root',
    'password': '1234',
    'database': 'public-opinion-analysis-system',
    'host': 'localhost',
    'port': 3306,
    'charset': 'utf8mb4'
}

def verify_keywords():
    try:
        # 连接数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("=" * 60)
        print("关键词数据验证报告")
        print("=" * 60)

        # 1. 总体统计
        cursor.execute("SELECT COUNT(*) FROM keywords")
        total_keywords = cursor.fetchone()[0]
        print(f"1. 关键词总记录数: {total_keywords}")

        # 2. 独立关键词数量
        cursor.execute("SELECT COUNT(DISTINCT keyword) FROM keywords")
        unique_keywords = cursor.fetchone()[0]
        print(f"2. 独立关键词数量: {unique_keywords}")

        # 3. 有关键词的文章数量
        cursor.execute("SELECT COUNT(DISTINCT corpus_id) FROM keywords")
        articles_with_keywords = cursor.fetchone()[0]
        print(f"3. 有关键词的文章数量: {articles_with_keywords}")

        # 4. 高频关键词TOP 10
        cursor.execute("""
            SELECT keyword, COUNT(*) as article_count, AVG(frequency) as avg_frequency, AVG(weight) as avg_weight
            FROM keywords
            GROUP BY keyword
            ORDER BY avg_weight DESC
            LIMIT 10
        """)
        top_keywords = cursor.fetchall()
        print(f"\n4. 权重最高的10个关键词:")
        for i, (keyword, count, freq, weight) in enumerate(top_keywords, 1):
            print(f"   {i:2d}. {keyword:<15} - 出现文章数: {count:3d}, 平均词频: {freq:6.1f}, 平均权重: {weight:.4f}")

        # 5. 每篇文章的关键词数量分布
        cursor.execute("""
            SELECT
                keyword_count,
                COUNT(*) as article_count
            FROM (
                SELECT corpus_id, COUNT(*) as keyword_count
                FROM keywords
                GROUP BY corpus_id
            ) as article_keywords
            GROUP BY keyword_count
            ORDER BY keyword_count
        """)
        keyword_distribution = cursor.fetchall()
        print(f"\n5. 每篇文章关键词数量分布:")
        for count, articles in keyword_distribution[:10]:  # 只显示前10个
            print(f"   {count:3d} 个关键词: {articles:3d} 篇文章")

        # 6. 按来源统计关键词
        cursor.execute("""
            SELECT c.source, COUNT(*) as keyword_count, COUNT(DISTINCT k.keyword) as unique_keywords
            FROM keywords k
            JOIN corpus c ON k.corpus_id = c.id
            GROUP BY c.source
        """)
        source_stats = cursor.fetchall()
        print(f"\n6. 按媒体来源统计:")
        for source, total, unique in source_stats:
            print(f"   {source:<5}: 总关键词数: {total:6d}, 独立关键词数: {unique:4d}")

        # 7. 查看一些具体示例
        cursor.execute("""
            SELECT c.title, k.keyword, k.weight, k.frequency
            FROM keywords k
            JOIN corpus c ON k.corpus_id = c.id
            WHERE k.keyword IN ('china', 'space', 'moon')
            ORDER BY k.weight DESC, k.frequency DESC
            LIMIT 10
        """)
        examples = cursor.fetchall()
        print(f"\n7. 关键词示例 (china, space, moon):")
        for title, keyword, weight, freq in examples:
            print(f"   [{keyword:<8}] {title[:50]}... (权重: {weight:.4f}, 词频: {freq})")

        print("\n" + "=" * 60)
        print("关键词数据验证完成！")
        print("=" * 60)

        # 关闭连接
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"验证失败: {e}")

if __name__ == "__main__":
    verify_keywords()