#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证热门关键词数据导入结果
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

def verify_hot_keywords():
    try:
        # 连接数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("=" * 60)
        print("热门关键词数据验证报告")
        print("=" * 60)

        # 1. 总体统计
        cursor.execute("SELECT COUNT(*) FROM hot_keywords")
        total_hot_keywords = cursor.fetchone()[0]
        print(f"1. 热门关键词总记录数: {total_hot_keywords}")

        # 2. 独立关键词数量
        cursor.execute("SELECT COUNT(DISTINCT keyword) FROM hot_keywords")
        unique_keywords = cursor.fetchone()[0]
        print(f"2. 独立关键词数量: {unique_keywords}")

        # 3. 按来源统计
        cursor.execute("""
            SELECT source, COUNT(*) as keyword_count, AVG(heat_score) as avg_heat_score
            FROM hot_keywords
            GROUP BY source
        """)
        source_stats = cursor.fetchall()
        print(f"\n3. 按来源统计:")
        for source, count, avg_score in source_stats:
            print(f"   {source:<5}: 关键词数: {count:3d}, 平均热度: {avg_score:6.2f}")

        # 4. 热度最高的关键词TOP 15
        cursor.execute("""
            SELECT keyword, source, count, heat_score, stat_date
            FROM hot_keywords
            ORDER BY heat_score DESC
            LIMIT 15
        """)
        top_keywords = cursor.fetchall()
        print(f"\n4. 热度最高的15个关键词:")
        for i, (keyword, source, count, heat_score, stat_date) in enumerate(top_keywords, 1):
            print(f"   {i:2d}. {keyword:<12} - {source:<3} (词频: {count:4d}, 热度: {heat_score:6.2f})")

        # 5. 查看今天的统计日期
        cursor.execute("SELECT DISTINCT stat_date FROM hot_keywords ORDER BY stat_date DESC")
        dates = cursor.fetchall()
        print(f"\n5. 统计日期:")
        for date_tuple in dates:
            print(f"   {date_tuple[0]}")

        # 6. 按热度得分分布
        cursor.execute("""
            SELECT
                CASE
                    WHEN heat_score >= 50 THEN '高热度 (>=50)'
                    WHEN heat_score >= 10 THEN '中热度 (10-50)'
                    WHEN heat_score >= 1 THEN '低热度 (1-10)'
                    ELSE '极低热度 (<1)'
                END as heat_level,
                COUNT(*) as keyword_count
            FROM hot_keywords
            GROUP BY
                CASE
                    WHEN heat_score >= 50 THEN '高热度 (>=50)'
                    WHEN heat_score >= 10 THEN '中热度 (10-50)'
                    WHEN heat_score >= 1 THEN '低热度 (1-10)'
                    ELSE '极低热度 (<1)'
                END
            ORDER BY MIN(heat_score) DESC
        """)
        heat_distribution = cursor.fetchall()
        print(f"\n6. 热度分布:")
        for level, count in heat_distribution:
            print(f"   {level:<20}: {count:3d} 个关键词")

        print("\n" + "=" * 60)
        print("热门关键词数据验证完成！")
        print("=" * 60)

        # 关闭连接
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"验证失败: {e}")

if __name__ == "__main__":
    verify_hot_keywords()