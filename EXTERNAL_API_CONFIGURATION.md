# 外部情報収集 設定ガイド

## 1. 情報収集先のエンドポイント変更

### A. Web Scraping設定 (`external_api/web_scraper.py`)

#### Google検索の変更
```python
# 行109: Google検索URLを変更する場合
search_url = "https://www.google.com/search"  # 他のGoogle地域版に変更可能
# 例: 
# search_url = "https://www.google.co.jp/search"  # 日本版
# search_url = "https://www.google.com.hk/search"  # 香港版
```

#### Torディレクトリの変更
```python
# 行190-193: Torディレクトリのミラーサイトを変更
darkfail_mirrors = [
    "https://darkfailenbsdla5mal2mxn2uz66od5vtzd5qozslagrfzachha3f3id.onion.ws",
    "https://darkfailenbsdla5mal2mxn2uz66od5vtzd5qozslagrfzachha3f3id.onion.ly",
    # 新しいミラーを追加
    "https://your-tor-mirror.com"
]
```

#### 日本のセキュリティニュースサイトの変更
```python
# 行228-244: セキュリティニュースソースを変更/追加
self.jp_sources = [
    {
        "name": "Security NEXT",
        "url": "https://www.security-next.com",
        "search_path": "/search.php?q="  # 検索パスを変更
    },
    # 新しいソースを追加
    {
        "name": "Your Security Site",
        "url": "https://your-security-site.com",
        "search_path": "/search?query="
    }
]
```

### B. Twitter監視設定 (`external_api/twitter_monitor.py`)

#### Nitterインスタンスの変更
```python
# 行24-30: Nitterインスタンスを変更（定期的な更新が必要）
self.nitter_instances = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    # 動作するインスタンスに変更
    "https://new-nitter-instance.com"
]
```

#### 監視アカウントの変更
```python
# 行33-40: セキュリティアカウントを変更/追加
self.security_accounts = [
    "malwarebytes",
    "threatpost",
    # 新しいアカウントを追加
    "your_security_account"
]

# 行43-49: 日本のセキュリティアカウント
self.jp_security_accounts = [
    "IPA_anshin",
    "nisc_forecast",
    # 新しい日本のアカウントを追加
    "new_jp_security"
]
```

### C. 無料API設定 (`external_api/truly_free_apis.py`)

#### DuckDuckGo設定
```python
# 行44: DuckDuckGo APIエンドポイント
base_url = "https://api.duckduckgo.com/"
# 代替: Searxインスタンスなど
# base_url = "https://searx.instance.com/search"
```

#### Pastebin設定
```python
# 行92: Pastebin検索URL
search_url = "https://pste.link/search"
# 代替のPastebinサービス
# search_url = "https://alternative-pastebin.com/search"
```

## 2. プロキシ設定（Tor経由のアクセス）

### `external_api/web_scraper.py`で設定
```python
# 行36-40: プロキシを有効化する場合
if use_proxy:
    self.proxies = {
        'http': 'socks5://127.0.0.1:9050',  # Torのデフォルトポート
        'https': 'socks5://127.0.0.1:9050'
    }
    # カスタムプロキシに変更する場合:
    # self.proxies = {
    #     'http': 'http://your-proxy:8080',
    #     'https': 'https://your-proxy:8080'
    # }
```

## 3. API認証情報の設定（有料APIを使用する場合）

### `.env`ファイルに追加
```bash
# 有料API（使用する場合）
DARKOWL_API_KEY=your_actual_key_here
SPYCLOUD_API_KEY=your_actual_key_here
INTELLIGENCEX_API_KEY=your_actual_key_here

# 新しいAPIを追加する場合
YOUR_NEW_API_KEY=your_key_here
```

## 4. レート制限の調整

### `scripts/start_monitoring_free.py`で設定
```python
# 行235: 監視間隔を変更（デフォルト10分）
def start(self, interval_minutes: int = 10):
    # より頻繁に監視する場合
    # interval_minutes = 5
    
    # より控えめに監視する場合
    # interval_minutes = 30
```

## 5. タイムアウトの調整

### 各スクレイパーで個別に設定
```python
# web_scraper.py 行71: タイムアウトを変更
kwargs['timeout'] = kwargs.get('timeout', 30)  # 30秒から変更
# 例: kwargs['timeout'] = kwargs.get('timeout', 60)  # 60秒に延長
```

## 6. User-Agentの追加/変更

### `external_api/web_scraper.py`
```python
# 行27-33: User-Agentリストをカスタマイズ
self.user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
    # 新しいUser-Agentを追加
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Mobile/15E148'
]
```

## まとめ

外部情報収集を本番環境で使用する場合の主な変更点：

1. **エンドポイントの更新**
   - Nitterインスタンスを動作するものに変更
   - セキュリティニュースサイトのURLを更新
   - Torディレクトリのミラーを更新

2. **認証情報の設定**
   - `.env`ファイルに実際のAPIキーを設定
   - プロキシ認証情報（必要な場合）

3. **レート制限の調整**
   - 各APIのレート制限に合わせて間隔を調整
   - タイムアウト値を環境に合わせて変更

4. **監視対象の追加**
   - Twitterアカウントの追加
   - セキュリティサイトの追加
   - 新しい検索エンジンの追加