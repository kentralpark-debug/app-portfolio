import urllib.request
import json

# ★ご自身のデベロッパーIDを指定
DEVELOPER_ID = "1861760912"  # 例: "123456789"

# ★上にピン留めしたい推しアプリの App ID（数字）を3つ指定
PRIORITY_APP_IDS = [
    "6793532854",  # 1番上に固定したいアプリID
    "6798088958",  # 2番目に固定したいアプリID
    "6794627399",  # 3番目に固定したいアプリID
]

def fetch_apps(developer_id):
    url = f"https://itunes.apple.com/lookup?id={developer_id}&entity=software"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            results = data.get("results", [])
            apps = [item for item in results if item.get("wrapperType") == "software"]
            return apps
    except Exception as e:
        print(f"データ取得エラー: {e}")
        return []

def sort_apps(apps, priority_ids):
    priority_apps = []
    other_apps = []
    
    # IDで検索しやすく辞書化
    app_dict = {str(app.get("trackId")): app for app in apps}
    
    # 優先アプリを指定順に追加
    for pid in priority_ids:
        pid_str = str(pid).strip()
        if pid_str in app_dict:
            priority_apps.append(app_dict.pop(pid_str))
            
    # 残りのアプリを一覧に追加
    other_apps = list(app_dict.values())
    
    return priority_apps + other_apps

def generate_html(apps):
    app_cards = ""
    for app in apps:
        name = app.get("trackName", "App")
        icon = app.get("artworkUrl512", app.get("artworkUrl100", ""))
        store_url = app.get("trackViewUrl", "#")
        description = app.get("description", "")
        short_desc = description[:100] + "..." if len(description) > 100 else description

        app_cards += f'''
        <div class="card">
            <img src="{icon}" alt="{name}" class="icon">
            <div class="info">
                <h2>{name}</h2>
                <p>{short_desc}</p>
                <a href="{store_url}" target="_blank" class="btn">App Storeで開く</a>
            </div>
        </div>
        '''

    html_content = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>App Portfolio</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        h1 {{
            margin-bottom: 30px;
            font-size: 1.8rem;
        }}
        .container {{
            width: 100%;
            max-width: 600px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        .card {{
            background: #1e293b;
            border-radius: 16px;
            padding: 16px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }}
        .icon {{
            width: 80px;
            height: 80px;
            border-radius: 18px;
            object-fit: cover;
        }}
        .info {{
            flex: 1;
        }}
        .info h2 {{
            margin: 0 0 6px 0;
            font-size: 1.1rem;
        }}
        .info p {{
            margin: 0 0 12px 0;
            font-size: 0.85rem;
            color: #94a3b8;
            line-height: 1.4;
        }}
        .btn {{
            display: inline-block;
            background: #38bdf8;
            color: #0f172a;
            padding: 8px 16px;
            border-radius: 20px;
            text-decoration: none;
            font-weight: bold;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <h1>App Portfolio</h1>
    <div class="container">
        {app_cards}
    </div>
</body>
</html>
'''
    return html_content

if __name__ == "__main__":
    print("Appleからアプリ情報を取得中...")
    raw_apps = fetch_apps(DEVELOPER_ID)
    if raw_apps:
        print(f"{len(raw_apps)} 件のアプリを取得しました。並び替えを実行します。")
        sorted_apps = sort_apps(raw_apps, PRIORITY_APP_IDS)
        html = generate_html(sorted_apps)
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("index.html の生成が完了しました！")
    else:
        print("アプリが取得できませんでした。DEVELOPER_IDを確認してください。")