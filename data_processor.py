#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理脚本：将BBC报道和情感分析结果保存到MySQL数据库
"""

import os
import re
import json
import mysql.connector
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional

# 数据库配置
DB_CONFIG = {
    'user': 'root',
    'password': '1234',
    'database': 'public-opinion-analysis-system',
    'host': 'localhost',
    'port': 3306,
    'charset': 'utf8mb4'
}

class DataProcessor:
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

    def parse_sentiment_results(self) -> Dict[str, Dict]:
        """
        解析情感分析结果文件
        返回格式: {标题: {sentiment: str, score: float}}
        """
        sentiment_data = {}
        current_section = None

        with open('sentiment_analysis_results.txt', 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配情感分析条目
        pattern = r'^\d+\.\s+(.+?)\s+\(得分:\s+(-?\d+\.\d+)\)'
        matches = re.findall(pattern, content, re.MULTILINE)

        for title, score in matches:
            # 清理标题
            title = title.strip()
            score = float(score)

            # 确定情感倾向
            if score > 0.1:
                sentiment = 'positive'
            elif score < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            sentiment_data[title] = {
                'sentiment': sentiment,
                'score': score,
                'confidence': abs(score) * 100,
                'positive_rate': max(0, score) * 100 if score > 0 else 0,
                'negative_rate': max(0, -score) * 100 if score < 0 else 0,
                'neutral_rate': 100 - (abs(score) * 100)
            }

        print(f"[OK] 解析情感分析结果: {len(sentiment_data)} 条记录")
        return sentiment_data

    def read_article_files(self) -> List[Dict]:
        """
        读取articles文件夹中的文章文件
        """
        articles = []
        articles_dir = 'articles'

        if not os.path.exists(articles_dir):
            print(f"[ERROR] 文件夹不存在: {articles_dir}")
            return articles

        for filename in os.listdir(articles_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(articles_dir, filename)

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read().strip()

                    # 使用文件名作为标题（去掉扩展名）
                    title = filename.replace('.txt', '')

                    articles.append({
                        'title': title,
                        'content': content,
                        'file_path': filepath,
                        'type': 'text'
                    })

                except Exception as e:
                    print(f"[ERROR] 读取文件失败 {filename}: {e}")

        print(f"[OK] 读取文章文件: {len(articles)} 个文件")
        return articles

    def extract_publish_date(self, title: str, content: str) -> Optional[date]:
        """
        从标题或内容中提取发布日期
        """
        # 简单的日期匹配模式
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{1,2})\s+(\w+)\s+(\d{4})'
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, content[:500])  # 只在前500字符中搜索
            if matches:
                try:
                    match = matches[0]
                    if len(match[0]) == 4:  # YYYY-MM-DD format
                        return date(int(match[0]), int(match[1]), int(match[2]))
                except ValueError:
                    continue

        # 如果无法提取日期，使用默认日期
        return date(2024, 1, 1)

    def save_corpus_data(self, articles: List[Dict]) -> List[int]:
        """
        保存文章数据到corpus表
        """
        corpus_ids = []

        sql = """
        INSERT INTO corpus (title, content, source, media_name, type, file_path, publish_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        for article in articles:
            values = (
                article['title'],
                article['content'],
                'uk',  # BBC属于英国媒体
                'BBC',
                article['type'],
                article['file_path'],
                self.extract_publish_date(article['title'], article['content'])
            )

            try:
                self.cursor.execute(sql, values)
                corpus_id = self.cursor.lastrowid
                corpus_ids.append(corpus_id)
            except mysql.connector.Error as e:
                print(f"[ERROR] 保存corpus数据失败: {e}")
                corpus_ids.append(None)

        self.conn.commit()
        print(f"[OK] 保存corpus数据: {len([x for x in corpus_ids if x is not None])} 条记录")
        return corpus_ids

    def save_sentiment_data(self, articles: List[Dict], corpus_ids: List[int], sentiment_data: Dict):
        """
        保存情感分析结果到sentiment_analysis表
        """
        sql = """
        INSERT INTO sentiment_analysis (
            corpus_id, sentiment, sentiment_score, confidence,
            positive_rate, negative_rate, neutral_rate
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        saved_count = 0

        for i, article in enumerate(articles):
            if corpus_ids[i] is None:
                continue

            title = article['title']

            # 查找对应的情感分析结果
            sentiment_info = sentiment_data.get(title)
            if not sentiment_info:
                # 尝试模糊匹配
                for sentiment_title, info in sentiment_data.items():
                    if self.similarity_match(title, sentiment_title):
                        sentiment_info = info
                        break

            if sentiment_info:
                values = (
                    corpus_ids[i],
                    sentiment_info['sentiment'],
                    sentiment_info['score'],
                    sentiment_info['confidence'],
                    sentiment_info['positive_rate'],
                    sentiment_info['negative_rate'],
                    sentiment_info['neutral_rate']
                )

                try:
                    self.cursor.execute(sql, values)
                    saved_count += 1
                except mysql.connector.Error as e:
                    print(f"[ERROR] 保存sentiment数据失败: {e}")

        self.conn.commit()
        print(f"[OK] 保存sentiment数据: {saved_count} 条记录")

    def similarity_match(self, title1: str, title2: str) -> bool:
        """
        简单的标题相似度匹配
        """
        # 转换为小写并移除特殊字符
        t1 = re.sub(r'[^\w\s]', '', title1.lower())
        t2 = re.sub(r'[^\w\s]', '', title2.lower())

        # 简单的包含关系检查
        return t1 in t2 or t2 in t1 or len(set(t1.split()) & set(t2.split())) >= 3

    def generate_statistics(self):
        """
        生成统计数据
        """
        # 删除现有统计数据
        self.cursor.execute("DELETE FROM statistics")

        # 生成统计查询
        stats_sql = """
        INSERT INTO statistics (
            stat_date, source, total_count, text_count,
            positive_count, neutral_count, negative_count, avg_sentiment
        )
        SELECT
            CURDATE() as stat_date,
            source,
            COUNT(*) as total_count,
            SUM(CASE WHEN type = 'text' THEN 1 ELSE 0 END) as text_count,
            SUM(CASE WHEN sa.sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
            SUM(CASE WHEN sa.sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
            SUM(CASE WHEN sa.sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
            AVG(sa.sentiment_score) as avg_sentiment
        FROM corpus c
        LEFT JOIN sentiment_analysis sa ON c.id = sa.corpus_id
        GROUP BY source
        """

        try:
            self.cursor.execute(stats_sql)
            self.conn.commit()
            print("[OK] 生成统计数据完成")
        except mysql.connector.Error as e:
            print(f"[ERROR] 生成统计数据失败: {e}")

    def process_all_data(self):
        """
        处理所有数据的主流程
        """
        print("=" * 50)
        print("开始处理BBC报道数据")
        print("=" * 50)

        try:
            # 1. 读取文章文件
            articles = self.read_article_files()
            if not articles:
                print("[ERROR] 没有找到文章文件")
                return

            # 2. 解析情感分析结果
            sentiment_data = self.parse_sentiment_results()
            if not sentiment_data:
                print("[ERROR] 没有找到情感分析结果")
                return

            # 3. 保存corpus数据
            corpus_ids = self.save_corpus_data(articles)

            # 4. 保存sentiment数据
            self.save_sentiment_data(articles, corpus_ids, sentiment_data)

            # 5. 生成统计数据
            self.generate_statistics()

            print("=" * 50)
            print("数据处理完成！")
            print("=" * 50)

        except Exception as e:
            print(f"[ERROR] 数据处理失败: {e}")
            raise

def main():
    """主函数"""
    processor = DataProcessor()

    try:
        processor.process_all_data()
    except Exception as e:
        print(f"程序执行失败: {e}")
    finally:
        processor.close_database()

if __name__ == "__main__":
    main()