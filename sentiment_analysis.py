import os
import re
import nltk
import pandas as pd
from collections import Counter

# 确保下载NLTK资源
print("正在下载NLTK资源...")
nltk.download('vader_lexicon')

from nltk.sentiment.vader import SentimentIntensityAnalyzer

# 初始化情感分析器
print("初始化情感分析器...")
sia = SentimentIntensityAnalyzer()

# 文章目录
articles_dir = 'articles'

# 结果存储
results = {
    'positive': [],
    'neutral': [],
    'negative': []
}

# 情感统计
sentiment_counts = Counter()

# 处理每篇文章
print(f"开始处理文章...")
article_count = 0

for filename in os.listdir(articles_dir):
    if not filename.endswith('.txt'):
        continue
    
    article_count += 1
    if article_count % 10 == 0:
        print(f"已处理 {article_count} 篇文章...")
    
    file_path = os.path.join(articles_dir, filename)
    
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 提取正文
        match = re.search(r'正文内容:(.*?)(?:图片列表:|$)', content, re.DOTALL)
        if match:
            text = match.group(1).strip()
        else:
            # 如果没有找到"正文内容:"标记，则使用整个内容
            text = content
        
        # 过滤掉太短的文章
        if len(text.split()) < 10:
            print(f"跳过过短的文章: {filename}")
            continue
        
        # 计算情感得分
        sentiment_score = sia.polarity_scores(text)
        compound_score = sentiment_score['compound']
        
        # 确定情感类别
        if compound_score >= 0.05:
            sentiment = 'positive'
        elif compound_score <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # 更新统计
        sentiment_counts[sentiment] += 1
        
        # 保存文章信息
        results[sentiment].append({
            'filename': filename,
            'score': compound_score
        })
    except Exception as e:
        print(f"处理文章 {filename} 时出错: {str(e)}")

# 输出结果
print("\n===== 情感分析结果 =====")
print(f"正向报道: {sentiment_counts['positive']} 篇")
print(f"中性报道: {sentiment_counts['neutral']} 篇")
print(f"负面报道: {sentiment_counts['negative']} 篇")
print(f"总计: {sum(sentiment_counts.values())} 篇")

# 保存结果到Excel
df_results = pd.DataFrame({
    '正向报道数': [sentiment_counts['positive']],
    '中性报道数': [sentiment_counts['neutral']],
    '负面报道数': [sentiment_counts['negative']],
    '总计': [sum(sentiment_counts.values())]
})

df_results.to_excel('情感分析结果.xlsx', index=False)
print("已保存总体结果到 '情感分析结果.xlsx'")

# 保存每篇文章的情感分类详情
details = []
for sentiment, articles in results.items():
    for article in articles:
        details.append({
            '文件名': article['filename'],
            '情感类别': sentiment,
            '情感得分': article['score']
        })

df_details = pd.DataFrame(details)
if not df_details.empty:
    df_details.sort_values(by='情感得分', ascending=False, inplace=True)
    df_details.to_excel('情感分析详情.xlsx', index=False)
    print("已保存详细结果到 '情感分析详情.xlsx'") 