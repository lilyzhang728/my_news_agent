import feedparser

def is_valid_rss(url):
    """检查 URL 是否为有效 RSS 源（至少能解析出 feed 标题或条目）"""
    try:
        f = feedparser.parse(url)
        if f.bozo:  # 解析异常
            return False
        # 检查是否有条目或 feed 标题
        if len(f.entries) > 0 or f.feed.get('title'):
            return True
        return False
    except:
        return False