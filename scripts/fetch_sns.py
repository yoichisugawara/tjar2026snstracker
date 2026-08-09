import csv
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

# 利用する RSS-Bridge の公開インスタンスリスト（自動切り替え用）
RSS_BRIDGES = [
    "https://rss-bridge.org/bridge01",
    "https://rssbridge.pw",
    "https://bridge.site" # 動作状況に応じて自動フォールバック
]

def fetch_rss(url):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_rss_item(xml_data):
    if not xml_data:
        return None
    try:
        root = ET.fromstring(xml_data)
        item = root.find('.//item')
        if item is None:
            return None
            
        title = item.findtext('title') or ""
        description = item.findtext('description') or ""
        pub_date = item.findtext('pubDate') or ""
        link = item.findtext('link') or ""
        
        # HTMLタグを除去してプレーンテキスト化
        clean_text = re.sub('<[^<]+?>', '', description if description else title).strip()
        
        # 画像URLの抽出 (<img> タグがある場合)
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description)
        media_url = img_match.group(1) if img_match else ""
        
        return {
            "pub_date": pub_date,
            "text": clean_text[:200],  # 冒頭200文字
            "media_url": media_url,
            "link": link
        }
    except Exception as e:
        print(f"XML parse error: {e}")
        return None

def main():
    participants = []
    
    # CSVファイルの読み込み
    with open('participants.csv', mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            participants.append(row)
            
    feed_data = []

    for p in participants:
        latest_post = None
        platform_used = ""
        
        # Instagramの巡回チェック
        if p.get('instagram_username'):
            insta_user = p['instagram_username'].strip()
            for bridge in RSS_BRIDGES:
                rss_url = f"{bridge}/?action=display&bridge=InstagramBridge&context=Username&u={insta_user}&format=Atom"
                xml_data = fetch_rss(rss_url)
                post = parse_rss_item(xml_data)
                if post:
                    latest_post = post
                    platform_used = "Instagram"
                    break

        # X (Twitter) の巡回チェック（Instagramが無かった、または失敗した場合）
        if not latest_post and p.get('x_username'):
            x_user = p['x_username'].strip()
            for bridge in RSS_BRIDGES:
                rss_url = f"{bridge}/?action=display&bridge=NitterBridge&name={x_user}&format=Atom"
                xml_data = fetch_rss(rss_url)
                post = parse_rss_item(xml_data)
                if post:
                    latest_post = post
                    platform_used = "X"
                    break

        # データ項目の結合
        feed_data.append({
            "bib": p.get('bib', ''),
            "name": p.get('name', ''),
            "age": p.get('age', ''),
            "avatar_url": p.get('avatar_url', ''),
            "info": p.get('info', ''),
            "x_username": p.get('x_username', ''),
            "instagram_username": p.get('instagram_username', ''),
            "ibuki_url": p.get('ibuki_url', ''),
            "platform": platform_used,
            "latest_post": latest_post,
            "updated_at": latest_post["pub_date"] if latest_post else "1970-01-01T00:00:00Z"
        })

    # 最新投稿日時が新しい順（降順）にソート
    feed_data.sort(key=lambda x: x['updated_at'], reverse=True)

    # 判定結果を JSON に書き出し
    with open('data/feed.json', 'w', encoding='utf-8') as f:
        json.dump(feed_data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
