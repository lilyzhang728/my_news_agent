print("程序启动了")
from llm import process_news_with_llm
from daily_ai_news import collect_news, send_to_wechat
from formatter import format_news_message_v2
import json
from rich import print

def main():
    news = collect_news()

    print(f"[yellow]原始新闻数量: {len(news)}[/yellow]")

    if not news:
        return

    # 👇 LLM处理
    llm_result = process_news_with_llm(news)

    print("[cyan]LLM返回结果：[/cyan]")
    print(llm_result)

    try:
        if llm_result.startswith('```json') and llm_result.endswith('```'):
            json_str = llm_result[7:-3].strip()   # 去掉 ```json 和 ```
        else:
            json_str = llm_result
        structured_news = json.loads(json_str)
        print('structured_news', structured_news)
    except:
        print("[red]JSON解析失败，直接发送原始内容[/red]")
        structured_news = news

    message = format_news_message_v2(structured_news)

    send_to_wechat(message)

if __name__ == "__main__":
    main()