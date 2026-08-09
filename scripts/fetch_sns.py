import csv
import json
import os
import re
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

def fetch_ibuki_status(ibuki_url):
    """IBUKIの公開ページから最新の現在地・ステータス文字列を取得"""
    if not ibuki_url:
        return None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    try:
        resp = requests.get(ibuki_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = bs4.BeautifulSoup(resp.content, "html.parser")
            
            # IBUKIページのメタ情報や特定要素から最新ログ・チェックポイントを取得
            # ページタイトルやog:description等に含まれるテキストを抽出
            meta_desc = soup.find("meta", property="og:description")
            if meta_desc and meta_desc.get("content"):
                desc_text = meta_desc["content"].strip()
                if desc_text:
                    return desc_text
            
            # タイトルからの抽出フォールバック
            title_tag = soup.find("title")
            if title_tag:
                title_text = title_tag.get_text().strip()
                return title_text
    except Exception as e:
        print(f"IBUKI fetch failed for {ibuki_url}: {e}")
    return None

def fetch_rss_feed(feed_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    try:
        resp = requests.get(feed_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            if feed.entries:
                entry = feed.entries[0]
                
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6]).isoformat() + "Z"
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6]).isoformat() + "Z"
                else:
                    pub_date = datetime.utcnow().isoformat() + "Z"
                
                raw_text = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                text = clean_text(raw_text)
                
                media_url = None
                if 'media_content' in entry and len(entry.media_content) > 0:
                    media_url = entry.media_content[0].get('url')
                elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                    media_url = entry.media_thumbnail[0].get('url')
                else:
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
        print(f"Fetch failed for {feed_url}: {e}")
    return None

def fetch_latest_post(x_username, insta_username):
    if x_username:
        x_rss_urls = [
            f"https://nitter.poast.org/{x_username}/rss",
            f"https://nitter.cz/{x_username}/rss",
            f"https://nitter.net/{x_username}/rss",
            f"https://rsshub.app/twitter/user/{x_username}"
        ]
        for url in x_rss_urls:
            post = fetch_rss_feed(url)
            if post:
                return post, "X (Twitter)"

    if insta_username:
        insta_urls = [
            f"https://rsshub.app/instagram/user/{insta_username}",
            f"https://rsshub.moe/instagram/user/{insta_username}",
            f"https://rsshub.rss3.io/instagram/user/{insta_username}",
            f"https://hub.tanglu.me/instagram/user/{insta_username}"
        ]
        for url in insta_urls:
            post = fetch_rss_feed(url)
            if post:
                return post, "Instagram"

    return None, ""

def main():
    csv_path = "participants.csv"
    output_path = "data/feed.json"
    
    if not os.path.exists(csv_path):
        print("participants.csv not found.")
        return

    existing_data = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                old_list = json.load(f)
                for item in old_list:
                    existing_data[item.get("bib")] = item
        except Exception as e:
            print(f"Failed to load existing feed.json: {e}")

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
            ibuki_status = fetch_ibuki_status(ibuki_url)

            old_item = existing_data.get(bib, {})
            if not post_data and old_item.get("latest_post"):
                post_data = old_item["latest_post"]
                platform = old_item.get("platform", "")

            item = {
                "bib": bib,
                "name": name,
                "age": age,
                "avatar_url": avatar_url,
                "info": info,
                "x_username": x_user,
                "instagram_username": insta_user,
                "ibuki_url": ibuki_url,
                "ibuki_status": ibuki_status,
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
