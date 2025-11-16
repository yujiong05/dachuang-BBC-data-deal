#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行数据处理脚本（测试模式）
"""

from data_processor import DataProcessor

def main():
    print("=" * 60)
    print("BBC情感分析数据处理系统")
    print("=" * 60)

    processor = DataProcessor()

    try:
        # 测试数据库连接
        print("1. 测试数据库连接...")
        if processor.conn and processor.conn.is_connected():
            print("   数据库连接正常")
        else:
            print("   数据库连接失败")
            return

        # 运行数据处理
        print("\n2. 开始处理数据...")
        processor.process_all_data()

        print("\n3. 数据处理完成！")

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.close_database()

if __name__ == "__main__":
    main()