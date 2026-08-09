import csv
import json
import os
import re
import urllib.parse
from datetime import datetime
import bs4
import feedparser
import requests

def clean_text(html_text):
    if not html_text:
        return ""
    soup = bs4.BeautifulSoup(html_text, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_rss_feed(feed_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        resp = requests.get(feed_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            if feed.entries:
                entry = feed.entries[0]
                
                # 日時のパース
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6]).isoformat() + "Z"
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6]).isoformat() + "Z"
                else:
                    pub_date = datetime.utcnow().isoformat() + "Z"
                
                # 本文抽出
                raw_text = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                text = clean_text(raw_text)
                
                # 画像メディアURL抽出
                media_url = None
                if 'media_content' in entry and len(entry.media_content) > 0:
                    media_url = entry.media_content[0].get('url')
                elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                    media_url = entry.media_thumbnail[0].get('url')
                else:
                    # 本文タグ内のimgタグを検索
                    soup = bs4.BeautifulSoup(raw_text, "html.parser")
                    img = soup.find('img')
                    if img and img.get('src'):
                        media_url = img.get('src')

                return {
                    "text": text[:300] + ("..." if len(text) > 300 else ""),
                    "pub_date": pub_date,
                    "media_url": media_url,
                    "link": getattr(entry, 'link', '')
                }
    except Exception as e:
        print(f"Error fetching {feed_url}: {e}")
    return None

def fetch_latest_post(x_username, insta_username):
    # 1. Instagram の取得試行 (RSSHub プロキシ経由)
    if insta_username:
        insta_url = f"https://rsshub.app/instagram/user/{insta_username}"
        post = fetch_rss_feed(insta_url)
        if post:
            return post, "Instagram"

    # 2. X (Twitter) の取得試行 (Nitter / RSSHub 経由)
    if x_username:
        x_rss_urls = [
            f"https://rsshub.app/twitter/user/{x_username}",
            f"https://nitter.net/{x_username}/rss",
            f"https://nitter.privacydev.net/{x_username}/rss"
        ]
        for url in x_rss_urls:
            post = fetch_rss_feed(url)
            if post:
                return post, "X (Twitter)"

    return None, ""

def main():
    csv_path = "participants.csv"
    output_path = "data/feed.json"
    
    if not os.path.exists(csv_path):
        print("participants.csv not found.")
        return

    results = []

    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bib = row.get("bib", "").strip()
            name = row.get("name", "").strip()
            age = row.get("age", "").strip()
            avatar_url = row.get("avatar_url", "").strip()
            info = row.get("info", "").strip()
            x_user = row.get("x_username", "").strip()
            insta_user = row.get("instagram_username", "").strip()
            ibuki_url = row.get("ibuki_url", "").strip()

            print(f"Processing No.{bib} {name}...")
            post_data, platform = fetch_latest_post(x_user, insta_user)

            item = {
                "bib": bib,
                "name": name,
                "age": age,
                "avatar_url": avatar_url,
                "info": info,
                "x_username": x_user,
                "instagram_username": insta_user,
                "ibuki_url": ibuki_url,
                "platform": platform,
                "latest_post": post_data,
                "updated_at": post_data["pub_date"] if post_data else "1970-01-01T00:00:00Z"
            }
            results.append(item)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Successfully updated feed.json!")

if __name__ == "__main__":
    main()
