# プロジェクト構造

```
paper_research_agent/
├── src/                          # メインのPythonコード
│   ├── __init__.py
│   ├── api/                      # API関連
│   │   ├── __init__.py
│   │   └── app.py               # FastAPIアプリケーション
│   ├── agents/                   # エージェント関連
│   │   ├── __init__.py
│   │   └── paper_research_agent.py  # 論文研究エージェント
│   ├── search/                   # 検索関連
│   │   ├── __init__.py
│   │   └── openalex_search.py   # OpenAlex API検索
│   └── utils/                    # ユーティリティ
│       ├── __init__.py
│       ├── config.py            # 設定管理
│       ├── llm_extractor.py     # LLMキーワード抽出
│       └── query_processor.py   # クエリ処理
│
├── frontend/                     # フロントエンド
│   ├── package.json             # npm設定
│   ├── tsconfig.json            # TypeScript設定
│   ├── src/
│   │   └── ts/
│   │       └── main.ts          # TypeScriptソース
│   └── static/                   # 静的ファイル
│       ├── index.html           # HTML
│       ├── css/
│       │   └── style.css        # スタイルシート
│       └── js/                  # コンパイル後のJavaScript
│
├── scripts/                      # スクリプト
│   ├── main.py                  # CLIメインスクリプト
│   └── search_example.py        # 検索例
│
├── tests/                        # テスト（将来用）
│
├── run_server.py                # サーバー起動スクリプト
├── requirements.txt             # Python依存関係
├── README.md                    # プロジェクト説明
└── .gitignore                   # Git除外設定
```

## ディレクトリの説明

### `src/`
メインのPythonアプリケーションコード。機能別にサブディレクトリに分割されています。

- **`api/`**: FastAPIを使用したWeb APIサーバー
- **`agents/`**: 対話型エージェントの実装
- **`search/`**: 論文検索機能（OpenAlex API）
- **`utils/`**: 設定、LLM、クエリ処理などのユーティリティ

### `frontend/`
TypeScriptで実装されたWebフロントエンド。

- **`src/ts/`**: TypeScriptソースコード
- **`static/`**: HTML、CSS、コンパイル後のJavaScript

### `scripts/`
コマンドラインで使用するスクリプト。

- **`main.py`**: CLIインターフェース
- **`search_example.py`**: 使用例

### `tests/`
テストコード（将来実装予定）

