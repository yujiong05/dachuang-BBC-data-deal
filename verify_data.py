#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证脚本：验证导入到数据库中的数据
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

def verify_data():
    """验证数据库中的数据"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("=" * 60)
        print("数据验证报告")
        print("=" * 60)

        # 1. 语料库数据统计
        cursor.execute("SELECT COUNT(*) FROM corpus")
        corpus_count = cursor.fetchone()[0]
        print(f"1. 语料库总记录数: {corpus_count}")

        cursor.execute("SELECT source, COUNT(*) FROM corpus GROUP BY source")
        sources = cursor.fetchall()
        print("   按来源统计:")
        for source, count in sources:
            print(f"   - {source}: {count} 条")

        # 2. 情感分析数据统计
        cursor.execute("SELECT COUNT(*) FROM sentiment_analysis")
        sentiment_count = cursor.fetchone()[0]
        print(f"\n2. 情感分析总记录数: {sentiment_count}")

        cursor.execute("""
            SELECT sa.sentiment, COUNT(*) as count, AVG(sa.sentiment_score) as avg_score
            FROM sentiment_analysis sa
            GROUP BY sa.sentiment
        """)
        sentiments = cursor.fetchall()
        print("   情感分布:")
        for sentiment, count, avg_score in sentiments:
            print(f"   - {sentiment}: {count} 条 (平均得分: {avg_score:.3f})")

        # 3. 查看一些示例数据
        cursor.execute("""
            SELECT c.title, c.source, sa.sentiment, sa.sentiment_score
            FROM corpus c
            JOIN sentiment_analysis sa ON c.id = sa.corpus_id
            ORDER BY sa.sentiment_score DESC
            LIMIT 5
        """)
        top_positive = cursor.fetchall()
        print(f"\n3. 最正面的5篇文章:")
        for title, source, sentiment, score in top_positive:
            print(f"   [{source}] {title[:60]}... (得分: {score:.3f})")

        cursor.execute("""
            SELECT c.title, c.source, sa.sentiment, sa.sentiment_score
            FROM corpus c
            JOIN sentiment_analysis sa ON c.id = sa.corpus_id
            ORDER BY sa.sentiment_score ASC
            LIMIT 5
        """)
        top_negative = cursor.fetchall()
        print(f"\n4. 最负面的5篇文章:")
        for title, source, sentiment, score in top_negative:
            print(f"   [{source}] {title[:60]}... (得分: {score:.3f})")

        # 4. 统计数据
        cursor.execute("SELECT * FROM statistics")
        stats = cursor.fetchall()
        print(f"\n5. 统计数据:")
        for stat in stats:
            print(f"   日期: {stat[1]}, 来源: {stat[2]}")
            print(f"   总数: {stat[3]}, 积极: {stat[7]}, 中性: {stat[8]}, 负面: {stat[9]}")
            print(f"   平均情感得分: {stat[10]}")

        print("\n" + "=" * 60)
        print("数据验证完成！")
        print("=" * 60)

    except mysql.connector.Error as e:
        print(f"数据库错误: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    verify_data()