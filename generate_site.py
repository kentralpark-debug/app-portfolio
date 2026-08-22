import json
import os
import urllib.parse
import urllib.request
import google.generativeai as genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeAI(model_name="gemini-1.5-flash")

# --------------------------------------------------
# ★ここをご自身のID・アプリIDに変更してください★
DEVELOPER_ID = "1861760912"  # あなたのデベロッパーID
PRIORITY_APP_IDS = [
    "6793532854",  # 推しアプリ 1番目
    "6794627399",  # 推しアプリ 2番目
    "6798088958",  # 推しアプリ 3番目
]
# --------------------------------------------------


def get_app_data_from_apple():
    url = f"https://itunes.apple.com/lookup?id={DEVELOPER_ID}&entity=software"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))
    return [
        item
        for item in data.get("results", [])
        if item.get("wrapperType") == "software"
    ]


def sort_apps(apps):
    """推しアプリ3つを固定で最上部に、残りは最新リリース順"""

    def get_sort_key(app):
        app_id = str(app.get("trackId"))
        if app_id in PRIORITY_APP_IDS:
            return (0, PRIORITY_APP_IDS.index(app_id), "")
        else:
            release_date = app.get("currentVersionReleaseDate", "")
            return (1, 0, release_date)

    # 優先度ソート後、リリース日は新しい順にするため逆順フラグ調整
    priority_apps = []
    other_apps = []
    for app in apps:
        if str(app.get("trackId")) in PRIORITY_APP_IDS:
            priority_apps.append(app)
        else:
            other_apps.append(app)

    # 推しアプリは指定配列の順番通りに整列
    priority_apps.sort(
        key=lambda x: PRIORITY_APP_IDS.index(str(x.get("trackId")))
    )
    # それ以外はリリース日時の新しい順にソート
    other_apps.sort(
        key=lambda x: x.get("currentVersionReleaseDate", ""), reverse=True
    )

    return priority_apps + other_apps


def generate_ai_content(app_name, description):
    prompt = f"""
あなたは優秀なアプリマーケターです。以下のアプリ情報からWebサイト掲載用の魅力的で簡潔な紹介文を作成してください。

アプリ名: {app_name}
説明文: {description}

以下のJSON形式でのみ出力してください。余計な解説文やバックトック(```)は不要です。
{{
  "subtitle": "刺さる1行キャッチコピー（20文字以内）",
  "summary": "ユーザーが得られるメリットを中心とした概要（120文字以内）",
  "keywords": ["キーワード1", "キーワード2", "キーワード3", "キーワード4", "キーワード5"]
}}
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        return json.loads(text)
    except Exception as e:
        print(f"AI Error for {app_name}: {e}")
        return {
            "subtitle": app_name,
            "summary": description[:100] + "...",
            "keywords": ["App", "iOS"],
        }


def build_html(apps_data):
    cards_html = ""
    for item in apps_data:
        app = item["raw"]
        ai = item["ai"]
        keywords_html = "".join(
            [
                f'<span class="tag">#{k}</span>'
                for k in ai.get("keywords", [])
            ]
        )

        cards_html += f"""
        <div class="card">
            <img src="{app.get('artworkUrl512', app.get('artworkUrl100'))}" alt="{app.get('trackName')}" class="icon">
            <div class="content">
                <h2>{app.get('trackName')}</h2>
                <p class="subtitle">{ai.get('subtitle')}</p>
                <p class="summary">{ai.get('summary')}</p>
                <div class="tags">{keywords_html}</div>
                <a href="{app.get('trackViewUrl')}" target="_blank" rel="noopener" class="btn">App Store で開く</a>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>App Portfolio</title>
    <style>
        :root {{ --bg: #0f111a; --card: #1a1d2e; --text: #e2e8f0; --accent: #ff4757; --sub: #94a3b8; }}
        body {{ background-color: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 40px 20px; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .header h1 {{ font-size: 2rem; margin-bottom: 8px; color: #fff; }}
        .header p {{ color: var(--sub); font-size: 0.95rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 24px; max-width: 1200px; margin: 0 auto; }}
        .card {{ background: var(--card); border-radius: 16px; padding: 24px; display: flex; flex-direction: column; align-items: center; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05); transition: transform 0.2s; }}
        .card:hover {{ transform: translateY(-4px); }}
        .icon {{ width: 96px; height: 96px; border-radius: 22px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); }}
        .content h2 {{ font-size: 1.25rem; margin: 0 0 6px 0; color: #fff; }}
        .subtitle {{ color: var(--accent); font-weight: bold; font-size: 0.9rem; margin: 0 0 12px 0; }}
        .summary {{ color: var(--sub); font-size: 0.85rem; line-height: 1.5; margin-bottom: 16px; }}
        .tags {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; margin-bottom: 20px; }}
        .tag {{ font-size: 0.75rem; color: #818cf8; background: rgba(129, 140, 248, 0.1); padding: 2px 8px; border-radius: 12px; }}
        .btn {{ display: inline-block; background: var(--accent); color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; transition: opacity 0.2s; }}
        .btn:hover {{ opacity: 0.9; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📱 Developer App Portfolio</h1>
        <p>リリース中のアプリ一覧</p>
    </div>
    <div class="grid">
        {cards_html}
    </div>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)


def main():
    raw_apps = get_app_data_from_apple()
    sorted_apps = sort_apps(raw_apps)

    apps_data = []
    print(f"取得アプリ数: {len(sorted_apps)}件")

    for app in sorted_apps:
        name = app.get("trackName")
        desc = app.get("description", "")
        print(f"AI解析中: {name}...")
        ai_info = generate_ai_content(name, desc)
        apps_data.append({"raw": app, "ai": ai_info})

    build_html(apps_data)
    print("完了！index.html が生成されました。")


if __name__ == "__main__":
    main()
