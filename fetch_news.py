from llm import discover_rss_by_llm
from validator import is_valid_rss
import feedparser
import logging
from datetime import datetime, timezone, timedelta

# 是否启用调试模式（调试时会打印更多信息，并发送测试消息）
DEBUG = True

# 时区（用于判断“今天”的新闻，中国时区 UTC+8）
LOCAL_TZ = timezone(timedelta(hours=8))

# 日志配置
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 根据RSS发现的源返回news-list
def main_with_topic(topic):
    print(f"🔍 正在为「{topic}」发现 RSS 源...")
    rss_urls = discover_rss_by_llm(topic)
    if not rss_urls:
        print("❌ 未发现任何 RSS 源，使用备用手动源")
        # 备选：可以回退到默认的几个 AI 源
        rss_urls = [
            "https://www.technologyreview.com/feed/artificial-intelligence/",
            "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
        ]
    
    # 验证并保留有效源
    valid_urls = []
    for url in rss_urls:
        if is_valid_rss(url):
            valid_urls.append(url)
            print(f"✅ 有效源: {url}")
        else:
            print(f"❌ 无效源: {url}")
    
    if not valid_urls:
        print("⚠️ 没有可用的 RSS 源，退出")
        return
    
    # 抓取所有新闻
    all_news = []
    for url in valid_urls:
        # news = fetch_rss_feed(url, max_items=8)  # 每个源最多8条，避免太长
        # all_news.extend(news)
        # print(f"从 {url} 抓取 {len(news)} 条")

        feed = fetch_rss_feed(url, max_items=8)
        if not feed or not feed.entries:
            continue
        
        source_name = feed.feed.get('title', url.split('/')[2])  # 从 feed 获取站点名
        for entry in feed.entries:
            if is_today(entry):
                title = entry.get('title', '无标题')
                link = entry.get('link', '')
                # 过滤掉明显不是新闻的条目（可选）
                if not link:
                    continue
                all_news.append({
                    'title': title,
                    'link': link,
                    'source': source_name
                })
        logger.info(f"从 {source_name} 获取到 {len([e for e in feed.entries if is_today(e)])} 条今日新闻")
    
    # 基于链接去重
    seen = set()
    unique_news = []
    for item in all_news:
        if item['link'] and item['link'] not in seen:
            seen.add(item['link'])
            unique_news.append(item)
    print(f"去重后剩余 {len(unique_news)} 条新闻")
    
    if not unique_news:
        print("无新闻可处理")
        return
    
    return unique_news
    
    



def fetch_rss_feed(url, max_items=10):
    """
    抓取单个 RSS 源，返回解析后的 feed 对象
    失败时返回 None
    """
    try:
        logger.debug(f"正在抓取: {url}")
        feed = feedparser.parse(url)
        if feed.bozo:  # bozo 表示解析异常
            logger.warning(f"RSS 解析警告（可能仍可用）: {url} - {feed.bozo_exception}")
        # 截断 entries 列表，最多 max_items 条
        if hasattr(feed, 'entries') and feed.entries:
            feed.entries = feed.entries[:max_items]
        return feed
    except Exception as e:
        logger.error(f"抓取失败 {url}: {e}")
        return None
    


def is_today(entry):
    """
    判断 RSS 条目是否属于“今天”（基于本地时区）
    因为不同 RSS 源的时间格式可能不同，这里尝试几种常见字段
    """
    # 尝试获取时间字段
    pub_time = None
    for time_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
        if time_field in entry and entry[time_field]:
            pub_time = entry[time_field]
            break
    
    if pub_time is None:
        # 没有时间信息，保守返回 False（不推送）
        logger.debug(f"条目无时间信息，跳过: {entry.get('title', 'no title')}")
        return False
    
    # pub_time 是一个 struct_time，需要转为带时区的 datetime
    # feedparser 返回的时间通常是 UTC
    dt_utc = datetime(*pub_time[:6], tzinfo=timezone.utc)
    dt_local = dt_utc.astimezone(LOCAL_TZ)
    today_local = datetime.now(LOCAL_TZ).date()
    return dt_local.date() == today_local