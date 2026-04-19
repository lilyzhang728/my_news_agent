import json
import sys
from llm import process_news_with_llm
from daily_ai_news import collect_news, send_to_wechat
from formatter import format_news_message_v2
from rich import print
from fetch_news import main_with_topic

def get_topic_from_args():
    """从命令行参数获取主题，若无参数则提示输入或使用默认值"""
    if len(sys.argv) > 1:
        return sys.argv[1].strip()
    else:
        # 可选：交互输入
        topic = input("请输入您感兴趣的领域（例如：人工智能、量子计算）: ").strip()
        if not topic:
            topic = "人工智能"   # 默认主题
        return topic

def main():
    topic = get_topic_from_args()
    print(f"[green]正在为主题「{topic}」收集资讯...[/green]")

    # news = collect_news()
    news = main_with_topic(topic)

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