import os
import re
import pandas as pd
from collections import Counter
import string

def extract_content(file_path):
    """从文章文件中提取正文内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则表达式提取正文部分
    # 正文在"正文内容:"和"图片列表:"之间
    # 如果没有图片列表，正文到文件末尾
    content_pattern = re.compile(r'正文内容:\n(.*?)(?:\n\n图片列表:|$)', re.DOTALL)
    match = content_pattern.search(content)
    
    if match:
        return match.group(1).strip()
    
    # 如果没有明确的"正文内容:"标记，尝试其他方法提取
    # 通常正文开始于第三行，结束于特定标记前
    lines = content.split('\n')
    if len(lines) > 2:
        content_start = "\n".join(lines[2:])
        
        # 找到结束标记
        end_markers = ["What are these?", "Most Popular Now", "These are links to other BBC pages"]
        for marker in end_markers:
            pos = content_start.find(marker)
            if pos > 0:
                return content_start[:pos].strip()
        
        return content_start.strip()
    
    return ""

def tokenize_english_text(text):
    """英文文本分词处理"""
    # 转为小写
    text = text.lower()
    
    # 预处理撇号（保留词内撇号，如 don't）
    text = re.sub(r'(\w+)\'(\w+)', r'\1\2', text)  # 处理单词内的撇号，如 don't -> dont
    
    # 移除标点符号，但排除处理过的撇号
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    
    # 按空格分词
    words = text.split()
    
    # 过滤掉数字和长度为1的词
    words = [word for word in words if not word.isdigit() and len(word) > 1]
    
    return words

def normalize_words(words):
    """标准化单词，处理复数形式和其他变形"""
    # 简单的复数处理
    normalized = []
    for word in words:
        # 处理常见的复数形式（简化处理，实际NLP会用词干提取或词形还原）
        if word.endswith('s') and len(word) > 3:
            singular = word[:-1]  # 移除末尾的's'
            normalized.append(singular)
        else:
            normalized.append(word)
    return normalized

def analyze_word_frequency():
    """分析所有文章的词频并保存结果"""
    articles_dir = 'articles'
    all_words = []
    
    # 确保articles文件夹存在
    if not os.path.exists(articles_dir):
        print(f"错误: {articles_dir}文件夹不存在")
        return
    
    # 读取所有文章文件
    article_files = [f for f in os.listdir(articles_dir) if f.endswith('.txt')]
    
    if not article_files:
        print(f"错误: {articles_dir}文件夹中没有txt文件")
        return
    
    print(f"开始分析{len(article_files)}篇文章...")
    
    # 定义停用词列表（常见的英文停用词）
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                  'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 
                  'about', 'against', 'between', 'into', 'through', 'during', 'before', 
                  'after', 'above', 'below', 'from', 'up', 'down', 'of', 'off', 'over', 
                  'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 
                  'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 
                  'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 
                  'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 
                  'now', 'that', 'this', 'it', 'its', 'has', 'have', 'had', 'would', 'could', 
                  'says', 'said', 'which', 'they', 'their', 'them', 'these', 'those', 
                  'who', 'what', 'whom', 'whose', 'may', 'might', 'must', 'shall', 'since', 
                  'does', 'did', 'done', 'doing', 'do', 'you', 'your', 'our', 'we', 
                  'he', 'she', 'him', 'her', 'his', 'hers', 'my', 'me', 'mine', 'am', 'im',
                  'also', 'as', 'if', 'because', 'while', 'until', 'unless', 'although',
                  'though', 'despite', 'however', 'nevertheless', 'nonetheless', 'therefore',
                  'thus', 'hence', 'consequently', 'accordingly', 'rather', 'instead',
                  'moreover', 'furthermore', 'additionally', 'besides', 'likewise', 'similarly',
                  'get', 'got', 'getting', 'make', 'made', 'making', 'take', 'took', 'taking',
                  'say', 'saying', 'go', 'going', 'went', 'come', 'coming', 'came', 'year',
                  'day', 'time', 'way', 'use', 'used', 'using', 'one', 'two', 'three', 'four',
                  'five', 'six', 'seven', 'eight', 'nine', 'ten'}
    
    # 提取并分析每篇文章的正文
    processed_files = 0
    for filename in article_files:
        file_path = os.path.join(articles_dir, filename)
        try:
            content = extract_content(file_path)
            
            if not content:
                print(f"警告: 无法从{filename}中提取正文内容")
                continue
            
            # 英文分词
            words = tokenize_english_text(content)
            
            # 过滤停用词
            words = [word for word in words if word not in stop_words]
            
            # 标准化单词（处理复数等变形）
            words = normalize_words(words)
            
            all_words.extend(words)
            processed_files += 1
            
            if processed_files % 10 == 0:
                print(f"已处理 {processed_files}/{len(article_files)} 篇文章")
                
        except Exception as e:
            print(f"处理文件 {filename} 时出错: {e}")
    
    print(f"共成功处理了 {processed_files} 篇文章")
    
    # 统计词频
    word_count = Counter(all_words)
    total_words = len(all_words)
    
    if total_words == 0:
        print("错误: 没有提取到任何有效单词")
        return
    
    # 获取前100个高频词
    top_100 = word_count.most_common(100)
    
    # 创建DataFrame
    df = pd.DataFrame(top_100, columns=['词语', '出现次数'])
    df['频率'] = df['出现次数'] / total_words
    # 将频率格式化为百分比
    df['频率'] = df['频率'].apply(lambda x: f"{x*100:.4f}%")
    
    # 保存到Excel
    output_file = '词频分析结果.xlsx'
    
    try:
        # 设置Excel写入选项
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='词频分析', index=False)
        
        # 获取xlsxwriter workbook和worksheet对象
        workbook = writer.book
        worksheet = writer.sheets['词频分析']
        
        # 设置列宽
        worksheet.set_column('A:A', 15)  # 词语列宽
        worksheet.set_column('B:B', 10)  # 出现次数列宽
        worksheet.set_column('C:C', 10)  # 频率列宽
        
        # 添加表头格式
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # 应用表头格式
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # 关闭Excel写入器
        writer.close()
        
        print(f"词频分析完成，共分析了{total_words}个词语")
        print(f"结果已保存到: {output_file}")
    except Exception as e:
        print(f"保存Excel时出错: {e}")
        # 尝试使用简单的保存方式
        df.to_excel(output_file, index=False)
        print(f"已使用简单格式保存结果到: {output_file}")

if __name__ == '__main__':
    analyze_word_frequency() 