#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Excel文件内容
"""

import pandas as pd

def check_excel():
    try:
        # 读取Excel文件
        df = pd.read_excel('词频分析结果.xlsx')

        print("Excel文件信息:")
        print(f"行数: {len(df)}")
        print(f"列数: {len(df.columns)}")
        print(f"\n列名: {list(df.columns)}")

        print("\n前5行数据:")
        for i, row in df.head().iterrows():
            print(f"第{i+1}行:")
            for col in df.columns:
                print(f"  {col}: {row[col]}")
            print()

        # 检查数据类型
        print("\n数据类型:")
        print(df.dtypes)

    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    check_excel()