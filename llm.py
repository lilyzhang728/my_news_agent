import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 处理新闻
def process_news_with_llm(news_list):
    content = "\n".join([
        f"{i+1}. {n['title']} ({n['link']})"
        for i, n in enumerate(news_list)
    ])

    prompt = f"""
你是一个专业的AI资讯编辑，请处理以下新闻：

要求：
1. 翻译成中文
2. 每条一句摘要
3. 分类
4. 去重
5. 按重要性排序

输出JSON格式：
[
  {{
    "title": "...",
    "summary": "...",
    "category": "...",
    "link": "..."
  }}
]

新闻：
{content}
"""

    url = "https://api.deepseek.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2048,  # 如果生成内容较长
        "temperature": 0.5
    }

    try:
        resp = requests.post(url, headers=headers, json=data, timeout=(5, 120))
        result = resp.json()

        return result["choices"][0]["message"]["content"]

    except Exception as e:
        print("❌ DeepSeek调用失败:", e)
        print("返回内容:", resp.text if 'resp' in locals() else "")
        return ""
    


# 生成 RSS 源列表
def discover_rss_by_llm(topic):
    """输入主题，返回 DeepSeek 推荐的 RSS 源 URL 列表"""
    prompt = f"""
你是一个资讯源发现专家。用户感兴趣的主题是：「{topic}」。
请提供 5-10 个与该主题高度相关的、更新活跃的 RSS/Atom 订阅源 URL。
要求：
1. 只输出一个 JSON 数组，每个元素是字符串格式的 URL。
2. 不要输出任何额外解释或标记。
3. 优先选择知名网站、博客、新闻媒体的 RSS 地址。
4. 确保 URL 是完整且可直接访问的（例如 https://example.com/rss.xml）。

输出示例：
["https://feeds.feedburner.com/example1", "https://example2.com/rss"]
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.3
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        # 提取 JSON 数组（防止模型输出多余内容）
        start = content.find('[')
        end = content.rfind(']') + 1
        if start != -1 and end != 0:
            json_str = content[start:end]
            urls = json.loads(json_str)
            print(f"发现的RSS源：{urls}")
            return urls
        else:
            print("⚠️ 模型未返回有效 JSON，返回空列表")
            return []
    except Exception as e:
        print(f"❌ 发现 RSS 源失败: {e}")
        return []