#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词处理脚本：从词频分析结果.xlsx中提取数据并保存到keywords表
"""

import pandas as pd
import mysql.connector
from typing import List, Dict, Optional
import re

# 数据库配置
DB_CONFIG = {
    'user': 'root',
    'password': '1234',
    'database': 'public-opinion-analysis-system',
    'host': 'localhost',
    'port': 3306,
    'charset': 'utf8mb4'
}

class KeywordProcessor:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.setup_database()

    def setup_database(self):
        """建立数据库连接"""
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("[OK] 数据库连接成功")
        except mysql.connector.Error as e:
            print(f"[ERROR] 数据库连接失败: {e}")
            raise

    def close_database(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("[OK] 数据库连接已关闭")

    def read_frequency_excel(self) -> pd.DataFrame:
        """
        读取词频分析结果.xlsx文件
        """
        try:
            # 读取Excel文件
            df = pd.read_excel('词频分析结果.xlsx')
            print(f"[OK] 成功读取Excel文件，共 {len(df)} 行数据")

            # 显示列名
            print(f"Excel文件列名: {list(df.columns)}")

            # 显示前几行数据
            print("前10行数据预览:")
            print(df.head(10))

            return df

        except Exception as e:
            print(f"[ERROR] 读取Excel文件失败: {e}")
            return pd.DataFrame()

    def get_all_corpus_ids(self) -> List[int]:
        """
        获取所有corpus_id
        """
        try:
            self.cursor.execute("SELECT id FROM corpus")
            results = self.cursor.fetchall()
            corpus_ids = [row[0] for row in results]

            print(f"[OK] 获取到 {len(corpus_ids)} 个语料库ID")
            return corpus_ids

        except mysql.connector.Error as e:
            print(f"[ERROR] 获取语料库ID失败: {e}")
            return []

    def process_global_keywords(self, df: pd.DataFrame, corpus_ids: List[int]) -> List[Dict]:
        """
        处理全局关键词数据（将关键词分配给所有文章）
        """
        keywords_data = []

        if df.empty:
            print("[ERROR] Excel文件为空")
            return keywords_data

        print(f"[OK] 开始处理全局关键词数据...")
        print(f"[INFO] 将 {len(df)} 个关键词分配给 {len(corpus_ids)} 篇文章")

        for index, row in df.iterrows():
            try:
                # 提取关键词 - 使用列位置而不是列名
                keyword = str(row.iloc[0]).strip()
                if keyword == 'nan' or keyword == '':
                    continue

                # 提取词频
                frequency = int(row.iloc[1])

                # 从频率字符串中提取数值
                frequency_str = str(row.iloc[2]).strip()
                if '%' in frequency_str:
                    # 如果是百分比格式，提取数值
                    weight = float(frequency_str.replace('%', '')) / 100.0
                else:
                    # 否则使用词频作为权重
                    weight = frequency / 1000.0

                # 为每篇文章都添加这个关键词
                for corpus_id in corpus_ids:
                    keywords_data.append({
                        'corpus_id': corpus_id,
                        'keyword': keyword,
                        'weight': weight,
                        'frequency': frequency
                    })

                if index < 10:  # 显示前10个关键词的处理信息
                    print(f"   处理关键词: {keyword} (词频: {frequency}, 权重: {weight})")

            except Exception as e:
                print(f"[ERROR] 处理第 {index} 行数据失败: {e}")
                continue

        print(f"[OK] 成功处理 {len(keywords_data)} 条关键词数据")
        return keywords_data

    def save_keywords_data(self, keywords_data: List[Dict]):
        """
        保存关键词数据到keywords表
        """
        if not keywords_data:
            print("[WARNING] 没有关键词数据需要保存")
            return

        sql = """
        INSERT INTO keywords (corpus_id, keyword, weight, frequency)
        VALUES (%s, %s, %s, %s)
        """

        saved_count = 0
        error_count = 0

        # 分批保存数据，避免一次性插入太多
        batch_size = 1000
        total_batches = (len(keywords_data) + batch_size - 1) // batch_size

        for i in range(0, len(keywords_data), batch_size):
            batch = keywords_data[i:i + batch_size]
            batch_num = i // batch_size + 1

            print(f"[INFO] 正在保存第 {batch_num}/{total_batches} 批数据 ({len(batch)} 条)...")

            for keyword_data in batch:
                try:
                    values = (
                        keyword_data['corpus_id'],
                        keyword_data['keyword'],
                        keyword_data['weight'],
                        keyword_data['frequency']
                    )

                    self.cursor.execute(sql, values)
                    saved_count += 1

                except mysql.connector.Error as e:
                    error_count += 1
                    if error_count <= 5:  # 只显示前5个错误
                        print(f"[ERROR] 保存关键词数据失败: {e}")

            # 每批提交一次
            self.conn.commit()

        print(f"[OK] 成功保存 {saved_count} 条关键词数据")
        if error_count > 0:
            print(f"[WARNING] 有 {error_count} 条数据保存失败")

    def process_all_keywords(self):
        """
        处理所有关键词数据的主流程
        """
        print("=" * 60)
        print("开始处理关键词数据")
        print("=" * 60)

        try:
            # 1. 读取Excel文件
            df = self.read_frequency_excel()
            if df.empty:
                print("[ERROR] 无法读取Excel文件")
                return

            # 2. 获取所有corpus_id
            corpus_ids = self.get_all_corpus_ids()
            if not corpus_ids:
                print("[ERROR] 无法获取语料库ID")
                return

            # 3. 处理关键词数据
            keywords_data = self.process_global_keywords(df, corpus_ids)
            if not keywords_data:
                print("[ERROR] 没有可用的关键词数据")
                return

            # 4. 保存数据到数据库
            self.save_keywords_data(keywords_data)

            print("=" * 60)
            print("关键词数据处理完成！")
            print("=" * 60)

        except Exception as e:
            print(f"[ERROR] 关键词数据处理失败: {e}")
            raise

def main():
    """主函数"""
    processor = KeywordProcessor()

    try:
        processor.process_all_keywords()
    except Exception as e:
        print(f"程序执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.close_database()

if __name__ == "__main__":
    main()