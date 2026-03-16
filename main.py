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
        found = []
        for eng, cn in TRANS_MAP.items():
            if re.search(eng, text, re.IGNORECASE):
                found.append(cn)
        prefix = f"【关注点：{'·'.join(found[:2])}】" if found else "【行业资讯】"
        return f"{prefix} 原文标题: {text}"

    def run(self):
        print(f"[{datetime.now()}] 开始抓取 RSS 源...")
        for url in RSS_SOURCES:
            try:
                feed = feedparser.parse(url)
                print(f"成功抓取: {url}, 发现条目: {len(feed.entries)}")
                for entry in feed.entries:
                    if entry.title in self.seen: continue
                    title_low = entry.title.lower()
                    desc = self.translate_desc(entry.title)
                    item = {"title": entry.title, "desc": desc, "link": entry.link}

                    if any(k in title_low for k in ["musk", "tesla", "spacex"]):
                        if len(self.musk_list) < 10: self.musk_list.append(item)
                    elif any(k in title_low for k in ["trump", "election", "maga"]):
                        if len(self.trump_list) < 10: self.trump_list.append(item)
                    else:
                        for cat, keywords in CATEGORIES.items():
                            if any(k in title_low for k in keywords):
                                if len(self.cat_list[cat]) < 5:
                                    self.cat_list[cat].append(item)
                                break
                    self.seen.add(entry.title)
            except Exception as e:
                print(f"抓取源 {url} 时出错: {e}")

    def build_report(self):
        utc_now = datetime.now(timezone.utc)
        beijing_time = (utc_now + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
        md = f"# 🗞️ 每日智讯 | {beijing_time}\n\n"

        if self.musk_list:
            md += "## 🚀 马斯克专栏\n" + "".join([f"- {n['desc']}\n  [查看详情]({n['link']})\n" for n in self.musk_list]) + "\n"
        if self.trump_list:
            md += "## 🎯 特朗普追踪\n" + "".join([f"- {n['desc']}\n  [查看详情]({n['link']})\n" for n in self.trump_list]) + "\n"
        
        md += "## 📊 行业分类简报\n"
        has_cat = False
        for cat, items in self.cat_list.items():
            if items:
                has_cat = True
                md += f"### {cat}\n" + "".join([f"- {i['title']} [🔗]({i['link']})\n" for i in items])
        
        if not self.musk_list and not self.trump_list and not has_cat:
            md += "> 今日暂无符合关键词的热点资讯。"
        return md

    def push(self, content):
        print("\n" + "="*30 + "\n开始进入推送环节\n" + "="*30)
        
        # 1. Server酱推送
        sc_key = os.getenv("SC_KEY")
        if sc_key:
            print(f"[DEBUG] 检测到 SC_KEY，准备向 Server酱 发送请求...")
            try:
                # 针对微信敏感词做脱敏处理，防止静默拦截
                safe_content = content.replace("Trump", "特*普").replace("特朗普", "特*普")
                res = requests.post(
                    f"https://sctapi.ftqq.com/{sc_key}.send", 
                    data={"title": f"每日智讯 {datetime.now().strftime('%m/%d')}", "desp": safe_content},
                    timeout=15
                )
                print(f"[SUCCESS] Server酱响应: {res.text}")
            except Exception as e:
                print(f"[ERROR] Server酱请求失败: {e}")
        else:
            print("[WARN] 未找到 SC_KEY，跳过微信推送。")

        # 2. Telegram推送
        tg_token = os.getenv("TG_TOKEN")
        tg_chat_id = os.getenv("TG_CHAT_ID")
        if tg_token and tg_chat_id:
            print(f"[DEBUG] 检测到 TG 配置，发送中...")
            try:
                res = requests.post(
                    f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                    data={"chat_id": tg_chat_id, "text": content, "parse_mode": "Markdown"},
                    timeout=15
                )
                print(f"[SUCCESS] Telegram 响应: {res.status_code}")
            except Exception as e:
                print(f"[ERROR] Telegram 请求失败: {e}")

        # 始终在控制台打印，方便调试
        print("\n--- 任务生成的报告预览 ---\n")
        print(content)
        print("\n" + "="*30 + "\n任务执行结束\n" + "="*30)

if __name__ == "__main__":
    bot = TechNewsBot()
    bot.run()
    report = bot.build_report()
    bot.push(report)
