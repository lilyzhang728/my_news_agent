import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")

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