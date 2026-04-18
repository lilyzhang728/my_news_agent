#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日 AI 资讯收集 + 微信推送脚本
功能：抓取多个 RSS 源，提取当天发布的新闻标题+链接，通过 Server酱 推送到微信
定时：由外部系统定时任务触发（如 cron / 任务计划程序）
"""

import feedparser
import requests
from datetime import datetime, timezone, timedelta
import logging

# ==================== 配置区域 ====================
# Server酱 的 SendKey（从 https://sct.ft07.com/ 获取）
SEND_KEY = "SCT339503TgP7G2aENoCFWCCafXK7Ifrez"   # 替换成真实的 Key

# RSS 源列表（可以随意增删）
RSS_SOURCES = [
    "https://www.technologyreview.com/feed/artificial-intelligence/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.jiqizhixin.com/rss",
    "https://36kr.com/feed",
    "https://hnrss.org/ai"
]

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

# ==================== 核心函数 ====================

def fetch_rss_feed(url):
    """
    抓取单个 RSS 源，返回解析后的 feed 对象
    失败时返回 None
    """
    try:
        logger.debug(f"正在抓取: {url}")
        feed = feedparser.parse(url)
        if feed.bozo:  # bozo 表示解析异常
            logger.warning(f"RSS 解析警告（可能仍可用）: {url} - {feed.bozo_exception}")
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

def collect_news():
    """
    遍历所有 RSS 源，收集今天发布的新闻
    返回列表，每个元素为 {'title': xxx, 'link': xxx, 'source': xxx}
    """
    news_items = []
    for url in RSS_SOURCES:
        feed = fetch_rss_feed(url)
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
                news_items.append({
                    'title': title,
                    'link': link,
                    'source': source_name
                })
        logger.info(f"从 {source_name} 获取到 {len([e for e in feed.entries if is_today(e)])} 条今日新闻")
    
    # 去重（基于链接）
    seen = set()
    unique_items = []
    for item in news_items:
        if item['link'] not in seen:
            seen.add(item['link'])
            unique_items.append(item)
    
    return unique_items

def format_news_message(news_list):
    """
    将新闻列表格式化为适合微信推送的 Markdown 文本
    """
    if not news_list:
        return "今日暂无新的 AI 资讯 🧘"
    
    today_str = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    msg = f"## 🤖 {today_str} AI 资讯汇总\n\n"
    for idx, item in enumerate(news_list, 1):
        msg += f"{idx}. [{item['title']}]({item['link']})  \n"
        # 可选：加来源小字
        msg += f"   *来源: {item['source']}*\n\n"
    msg += f"\n共 {len(news_list)} 条 | [定制提醒](https://sct.ft07.com)"
    return msg

def send_to_wechat(message):
    """
    通过 Server酱 发送消息到微信
    """
    if not SEND_KEY or SEND_KEY != "SCT339503TgP7G2aENoCFWCCafXK7Ifrez":
        logger.error("未配置有效的 SEND_KEY，请检查！")
        return False
    
    # url = f"https://sctapi.ft07.com/send/{SEND_KEY}.send"
    # Server酱 Turbo API 地址
    url = f"https://sctapi.ftqq.com/{SEND_KEY}.send" 

    data = {
        "title": "每日 AI 资讯",          # 消息标题
        "desp": message,                 # 消息内容（支持 Markdown）
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        result = resp.json()
        if result.get('code') == 0:
            logger.info("推送成功！")
            return True
        else:
            logger.error(f"推送失败: {result}")
            return False
    except Exception as e:
        logger.error(f"网络错误: {e}")
        return False

# ==================== 主流程 ====================

def main():
    logger.info("========== 开始收集今日 AI 资讯 ==========")
    news = collect_news()
    logger.info(f"共收集到 {len(news)} 条去重后的今日新闻")
    
    message = format_news_message(news)
    if DEBUG:
        # 调试模式：打印消息内容到控制台，同时发送
        print("\n===== 即将推送的消息内容 =====\n")
        print(message)
        print("\n================================\n")
        # 调试时也可以选择不发真实消息，这里为方便测试，仍然发送（但会检查 SEND_KEY）
    
    send_to_wechat(message)
    logger.info("========== 任务结束 ==========")

if __name__ == "__main__":
    main()