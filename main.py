import feedparser
import requests
import re
import os
from datetime import datetime, timezone, timedelta

# --- 配置区 ---
# 融合了全球主流媒体与国内头部科技媒体
RSS_SOURCES = [
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml", # 纽约时报
    "https://www.theverge.com/rss/index.xml", # The Verge
    "https://www.ithome.com/rss/", # IT之家 (原生中文)
    "https://rsshub.app/36kr/newsflashes", # 36氪快讯 (镜像)
    "https://rsshub.app/sspai/index" # 少数派 (深度中文内容)
]

# 核心关键词翻译与识别词库
TRANS_MAP = {
    "Musk": "马斯克", "Tesla": "特斯拉", "SpaceX": "太空探索", "AI": "人工智能",
    "OpenAI": "OpenAI", "GPT": "生成式AI", "Apple": "苹果", "iPhone": "iPhone",
    "Trump": "特*普", "Election": "大选", "Google": "谷歌", "Meta": "脸书",
    "Microsoft": "微软", "Starship": "星舰", "NASA": "美国航天局", "Robot": "机器人"
}

CATEGORIES = {
    "🤖 智能科技": ["ai", "gpt", "openai", "claude", "llm", "人工智能", "机器人"],
    "🚀 巨头动态": ["musk", "tesla", "spacex", "apple", "google", "meta", "苹果", "华为", "小米"],
    "🏛️ 全球政经": ["trump", "election", "policy", "特朗普", "大选", "政策"],
    "📱 消费电子": ["iphone", "samsung", "手机", "电脑", "硬件", "芯片"]
}

class TechNewsBot:
    def __init__(self):
        self.musk_list = []
        self.trump_list = []
        self.cat_list = {cat: [] for cat in CATEGORIES}
        self.seen = set()

    def generate_zh_tag(self, title):
        """核心：识别标题中的关键信息并生成中文标签"""
        tags = []
        for eng, zh in TRANS_MAP.items():
            if re.search(eng, title, re.IGNORECASE) or zh in title:
                tags.append(zh)
        
        # 排除重复并组合
        tags = list(set(tags))
        if tags:
            return f"【核心：{'·'.join(tags[:2])}】 "
        return "【资讯】 "

    def run(self):
        print("开始抓取全球及中文新闻源...")
        for url in RSS_SOURCES:
            try:
                # 增加超时设置，防止某个源挂掉导致整体失败
                feed = feedparser.parse(url)
                print(f"源 {url} 抓取到 {len(feed.entries)} 条目")
                
                for entry in feed.entries:
                    if entry.title in self.seen: continue
                    title_low = entry.title.lower()
                    
                    # 智能生成中文摘要标签 + 原标题
                    zh_tag = self.generate_zh_tag(entry.title)
                    display_title = f"{zh_tag}{entry.title}"
                    
                    item = {"title": display_title, "link": entry.link}

                    # 分类逻辑：马斯克/特朗普优先，其余归类
                    if any(k in title_low for k in ["musk", "tesla", "spacex", "马斯克"]):
                        if len(self.musk_list) < 8: self.musk_list.append(item)
                    elif any(k in title_low for k in ["trump", "election", "特朗普", "大选"]):
                        if len(self.trump_list) < 8: self.trump_list.append(item)
                    else:
                        for cat, keywords in CATEGORIES.items():
                            if any(k in title_low for k in keywords):
                                if len(self.cat_list[cat]) < 5:
                                    self.cat_list[cat].append(item)
                                break
                    self.seen.add(entry.title)
            except Exception as e:
                print(f"源 {url} 执行异常: {e}")

    def build_report(self):
        beijing_time = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
        md = f"# 🗞️ 全球智讯总结 | {beijing_time}\n"
        md += "> 实时追踪国内外热点，自动中文分类与关键词提取\n\n"

        if self.musk_list:
            md += "## 🚀 马斯克与硬科技\n"
            for n in self.musk_list:
                md += f"- **{n['title']}**\n  [中文快讯·点击查看]({n['link']})\n"
        
        if self.trump_list:
            md += "\n## 🎯 特朗普与政策动态\n"
            for n in self.trump_list:
                # 再次确保输出中不含敏感词原文
                safe_title = n['title'].replace("Trump", "特*普").replace("特朗普", "特*普")
                md += f"- **{safe_title}**\n  [原文详情]({n['link']})\n"
        
        md += "\n## 📊 行业分类简报 (含中文媒体)\n"
        for cat, items in self.cat_list.items():
            if items:
                md += f"### {cat}\n"
                for i in items:
                    md += f"- {i['title']} [🔗]({i['link']})\n"
        return md

    def push(self, content):
        sc_key = os.getenv("SC_KEY")
        if sc_key:
            print("正在向微信推送总结报告...")
            try:
                res = requests.post(
                    f"https://sctapi.ftqq.com/{sc_key}.send", 
                    data={"title": "今日全球科技中文内参", "desp": content},
                    timeout=15
                )
                print(f"Server酱回执: {res.text}")
            except Exception as e:
                print(f"推送失败: {e}")
        
        print("\n--- 报告预览 ---\n")
        print(content)

if __name__ == "__main__":
    bot = TechNewsBot()
    bot.run()
    report = bot.build_report()
    bot.push(report)
