#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试关键词处理
"""

import pandas as pd
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

def test_keyword_processing():
    try:
        # 1. 读取Excel文件
        df = pd.read_excel('词频分析结果.xlsx')
        print(f"[OK] 读取到 {len(df)} 行关键词数据")

        # 2. 连接数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 3. 获取所有corpus_id
        cursor.execute("SELECT id FROM corpus")
        corpus_ids = [row[0] for row in cursor.fetchall()]
        print(f"[OK] 获取到 {len(corpus_ids)} 个文章ID")

        # 4. 处理前5个关键词作为测试
        test_keywords = []
        print("前5行数据详细检查:")
        for index, row in df.head(5).iterrows():
            print(f"行 {index}: {dict(row)}")
            keyword = str(row.iloc[0]).strip()  # 使用第一列
            frequency = int(row.iloc[1])        # 使用第二列
            frequency_str = str(row.iloc[2]).strip()  # 使用第三列
            weight = float(frequency_str.replace('%', '')) / 100.0

            print(f"处理关键词: {keyword}, 词频: {frequency}, 权重: {weight}")

            # 只为前3篇文章添加这个关键词作为测试
            for corpus_id in corpus_ids[:3]:
                test_keywords.append({
                    'corpus_id': corpus_id,
                    'keyword': keyword,
                    'weight': weight,
                    'frequency': frequency
                })

        # 5. 保存测试数据
        sql = """
        INSERT INTO keywords (corpus_id, keyword, weight, frequency)
        VALUES (%s, %s, %s, %s)
        """

        for kw_data in test_keywords:
            try:
                cursor.execute(sql, (kw_data['corpus_id'], kw_data['keyword'],
                                   kw_data['weight'], kw_data['frequency']))
                print(f"   [OK] 保存关键词 '{kw_data['keyword']}' 到文章 {kw_data['corpus_id']}")
            except Exception as e:
                print(f"   [ERROR] 保存失败: {e}")

        conn.commit()
        print(f"[OK] 成功保存 {len(test_keywords)} 条测试关键词数据")

        # 6. 关闭连接
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR] 处理失败: {e}")

if __name__ == "__main__":
    test_keyword_processing()