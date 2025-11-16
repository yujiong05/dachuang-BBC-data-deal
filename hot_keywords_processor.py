#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热门关键词处理脚本：从词频分析结果.xlsx中提取数据并保存到hot_keywords表
"""

import pandas as pd
import mysql.connector
from datetime import date
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

class HotKeywordsProcessor:
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

    def process_hot_keywords(self, df: pd.DataFrame) -> list:
        """
        处理热门关键词数据
        """
        hot_keywords_data = []

        if df.empty:
            print("[ERROR] Excel文件为空")
            return hot_keywords_data

        print(f"[OK] 开始处理热门关键词数据...")
        print(f"[INFO] 处理 {len(df)} 个关键词")

        current_date = date.today()

        for index, row in df.iterrows():
            try:
                # 提取关键词 - 使用列位置而不是列名
                keyword = str(row.iloc[0]).strip()
                if keyword == 'nan' or keyword == '':
                    continue

                # 提取词频
                count = int(row.iloc[1])

                # 从频率字符串中提取数值作为热度得分
                frequency_str = str(row.iloc[2]).strip()
                if '%' in frequency_str:
                    # 如果是百分比格式，提取数值
                    heat_score = float(frequency_str.replace('%', ''))
                else:
                    # 否则使用词频作为热度得分
                    heat_score = float(count)

                # 确定来源（由于这是全局统计，使用'uk'作为默认值）
                source = 'uk'

                hot_keywords_data.append({
                    'keyword': keyword,
                    'source': source,
                    'count': count,
                    'heat_score': heat_score,
                    'stat_date': current_date
                })

                # 显示前10个关键词的处理信息
                if index < 10:
                    print(f"   处理关键词: {keyword} (词频: {count}, 热度得分: {heat_score})")

            except Exception as e:
                print(f"[ERROR] 处理第 {index} 行数据失败: {e}")
                continue

        print(f"[OK] 成功处理 {len(hot_keywords_data)} 条热门关键词数据")
        return hot_keywords_data

    def save_hot_keywords_data(self, hot_keywords_data: list):
        """
        保存热门关键词数据到hot_keywords表
        """
        if not hot_keywords_data:
            print("[WARNING] 没有热门关键词数据需要保存")
            return

        sql = """
        INSERT INTO hot_keywords (keyword, source, count, heat_score, stat_date)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        count = VALUES(count),
        heat_score = VALUES(heat_score),
        update_time = CURRENT_TIMESTAMP
        """

        saved_count = 0
        error_count = 0

        print(f"[INFO] 开始保存热门关键词数据...")

        for keyword_data in hot_keywords_data:
            try:
                values = (
                    keyword_data['keyword'],
                    keyword_data['source'],
                    keyword_data['count'],
                    keyword_data['heat_score'],
                    keyword_data['stat_date']
                )

                self.cursor.execute(sql, values)
                saved_count += 1

            except mysql.connector.Error as e:
                error_count += 1
                if error_count <= 5:  # 只显示前5个错误
                    print(f"[ERROR] 保存热门关键词数据失败: {e}")

        self.conn.commit()
        print(f"[OK] 成功保存 {saved_count} 条热门关键词数据")
        if error_count > 0:
            print(f"[WARNING] 有 {error_count} 条数据保存失败")

    def process_all_hot_keywords(self):
        """
        处理所有热门关键词数据的主流程
        """
        print("=" * 60)
        print("开始处理热门关键词数据")
        print("=" * 60)

        try:
            # 1. 读取Excel文件
            df = self.read_frequency_excel()
            if df.empty:
                print("[ERROR] 无法读取Excel文件")
                return

            # 2. 处理热门关键词数据
            hot_keywords_data = self.process_hot_keywords(df)
            if not hot_keywords_data:
                print("[ERROR] 没有可用的热门关键词数据")
                return

            # 3. 保存数据到数据库
            self.save_hot_keywords_data(hot_keywords_data)

            print("=" * 60)
            print("热门关键词数据处理完成！")
            print("=" * 60)

        except Exception as e:
            print(f"[ERROR] 热门关键词数据处理失败: {e}")
            raise

def main():
    """主函数"""
    processor = HotKeywordsProcessor()

    try:
        processor.process_all_hot_keywords()
    except Exception as e:
        print(f"程序执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.close_database()

if __name__ == "__main__":
    main()