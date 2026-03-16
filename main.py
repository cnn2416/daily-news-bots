import feedparser
import requests
import re
import os
from datetime import datetime, timezone, timedelta

# --- 配置区 ---
RSS_SOURCES = [
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://feeds.feedburner.com/TechCrunch/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss"
]

# 本地词库翻译
TRANS_MAP = {
    "Musk": "马斯克", "Tesla": "特斯拉", "SpaceX": "太空探索", "Neuralink": "脑机接口",
    "Trump": "特朗普", "Donald": "唐纳德", "Election": "大选", "White House": "白宫",
    "AI": "人工智能", "OpenAI": "OpenAI", "GPT": "生成式AI", "Apple": "苹果",
    "iPhone": "iPhone", "Microsoft": "微软", "Google": "谷歌", "Space": "航天",
    "NASA": "美国航天局", "Rocket": "火箭", "Starship": "星舰", "Crypto": "加密货币",
    "Bitcoin": "比特币", "Security": "安全", "Hack": "黑客", "Policy": "政策"
}

CATEGORIES = {
    "🤖 人工智能": ["ai", "gpt", "openai", "claude", "llm", "intelligence"],
    "🚀 商业大亨": ["musk", "tesla", "spacex", "x.ai", "starlink"],
    "🏛️ 政治动态": ["trump", "election", "campaign", "white house", "maga"],
    "🌌 宇宙探索": ["space", "nasa", "rocket", "mars", "moon", "starship"],
    "💰 金融财讯": ["finance", "crypto", "bitcoin", "stock", "economy", "fed"],
    "📱 消费电子": ["apple", "iphone", "samsung", "gadget", "hardware", "chips"],
    "💻 互联网文化": ["google", "meta", "tiktok", "social media", "twitter"],
    "🔒 安全隐私": ["hack", "security", "privacy", "cyber", "leak"],
    "🔋 能源交通": ["ev", "battery", "energy", "autonomous", "driving"],
    "🔬 前沿科学": ["science", "physics", "dna", "discovery"]
}

class TechNewsBot:
    def __init__(self):
        self.musk_list = []
        self.trump_list = []
        self.cat_list = {cat: [] for cat in CATEGORIES}
        self.seen = set()

    def translate_desc(self, text):
        """局部关键词翻译：识别英文关键词并标注中文描述"""
        found = []
        for eng, cn in TRANS_MAP.items():
            if re.search(eng, text, re.IGNORECASE):
                found.append(cn)
        prefix = f"【关注点：{'·'.join(found[:2])}】" if found else "【行业资讯】"
        return f"{prefix} 原文标题: {text}"

    def run(self):
        for url in RSS_SOURCES:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if entry.title in self.seen: continue
                title_low = entry.title.lower()
                desc = self.translate_desc(entry.title)
                item = {"title": entry.title, "desc": desc, "link": entry.link}

                # 策略1：马斯克/特朗普专项 (最优先)
                if any(k in title_low for k in ["musk", "tesla", "spacex"]):
                    if len(self.musk_list) < 15: self.musk_list.append(item)
                elif any(k in title_low for k in ["trump", "election", "maga"]):
                    if len(self.trump_list) < 15: self.trump_list.append(item)
                else:
                    # 策略2：自动归类
                    for cat, keywords in CATEGORIES.items():
                        if any(k in title_low for k in keywords):
                            if len(self.cat_list[cat]) < 5:
                                self.cat_list[cat].append(item)
                            break
                self.seen.add(entry.title)

    def build_report(self):
        utc_now = datetime.now(timezone.utc)
        beijing_time = (utc_now + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
        md = f"# 🗞️ 每日智讯 | {beijing_time}\n\n"

        if self.musk_list:
            md += "## 🚀 马斯克专栏\n" + "".join([f"- {n['desc']}\n  [查看详情]({n['link']})\n" for n in self.musk_list]) + "\n"
        if self.trump_list:
            md += "## 🎯 特朗普追踪\n" + "".join([f"- {n['desc']}\n  [查看详情]({n['link']})\n" for n in self.trump_list]) + "\n"
        
        md += "## 📊 行业分类简报\n"
        for cat, items in self.cat_list.items():
            if items:
                md += f"### {cat}\n" + "".join([f"- {i['title']} [🔗]({i['link']})\n" for i in items])
        return md

    def push(self, content):
        # 1. Server酱推送
        def push(self, content):
        sc_key = os.getenv("SC_KEY")
        print(f"--- 准备推送内容 ---")
        print(content) # 看看日志里到底生成的报告是什么样
        
        if sc_key:
            print(f"正在调用 Server酱...")
            res = requests.post(
                f"https://sctapi.ftqq.com/{sc_key}.send", 
                data={"title": "每日智讯", "desp": content}
            )
            print(f"Server酱服务器响应: {res.text}") # 关键：看看服务器报不报错
        else:
            print("错误：未检测到 SC_KEY 环境变量！请检查 Github Secrets 配置。")
        
        # 2. Telegram推送
        # tg_token = os.getenv("TG_TOKEN")
        # tg_chat_id = os.getenv("TG_CHAT_ID")
        # if tg_token and tg_chat_id:
            # requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", data={"chat_id": tg_chat_id, "text": content, "parse_mode": "Markdown"})
        
        print(content) # 控制台也打印一份结果

if __name__ == "__main__":
    bot = TechNewsBot()
    bot.run()
    report = bot.build_report()
    bot.push(report)
