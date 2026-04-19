from datetime import datetime

def format_news_message_v2(news_list):
    # print('news_list', news_list)
    if not news_list:
        return "今日暂无重要AI资讯"

    today = datetime.now().strftime("%Y-%m-%d")

    msg = f"## 🤖 {today} AI精选资讯\n\n"

    categories = {}

    for item in news_list:
        cat = item.get("category", "其他")
        categories.setdefault(cat, []).append(item)

    # print('categories', categories)
    for cat, items in categories.items():
        msg += f"### 🔹 {cat}\n\n"
        for i, n in enumerate(items, 1):
            msg += f"{i}. {n['title']}\n"
            msg += f"👉 {n['summary']}\n"
            msg += f"[查看详情]({n['link']})\n\n"

    return msg