# BBC爬虫配置文件

# BBC网站URL
BBC_URL = 'https://www.bbc.com'
BBC_NEWS_URL = 'https://www.bbc.co.uk/search'

# 搜索关键词 - 中国航天相关
SEARCH_KEYWORDS = [
    'China space',
    'Chinese space program',
    'China aerospace',
    'Chinese rockets',
    'China satellite',
    'China space station',
    'China moon mission',
    'China mars mission',
    'Chinese space agency',
    'China tiangong',
    'Chinese lunar exploration',
    'China Chang\'e mission',
    'China Tianwen mission',
    'Chinese Long March rocket'
]

# 爬虫设置
MAX_PAGES_PER_KEYWORD = 15  # 每个关键词最多爬取的页数
TARGET_ARTICLE_COUNT = 200  # 目标文章数量
REQUEST_DELAY = (1, 3)  # 请求间隔时间范围（秒）
BATCH_PAUSE = 5  # 每批次处理后的暂停时间（秒）
BATCH_SIZE = 10  # 每批次处理的文章数

# 文件夹设置
ARTICLES_DIR = 'articles'
IMAGES_DIR = 'images'
VIDEOS_DIR = 'videos'

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
} 