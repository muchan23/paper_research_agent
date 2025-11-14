# paper_research_agent

## 概要

このリポジトリは、論文研究を支援するためのエージェントです。以下の2つの主要な機能を提供します。

## セットアップ

### 1. 仮想環境の作成と有効化

```bash
# 仮想環境を作成（既に作成済みの場合はスキップ）
python3 -m venv venv

# 仮想環境を有効化
# macOS/Linuxの場合:
source venv/bin/activate

# Windowsの場合:
# venv\Scripts\activate
```

仮想環境が有効化されると、プロンプトに `(venv)` が表示されます。

### 2. 依存関係のインストール

**Python依存関係:**
```bash
pip install -r requirements.txt
```

**TypeScript依存関係（フロントエンド用）:**
```bash
cd frontend
npm install
cd ..
```

**TypeScriptのコンパイル:**
```bash
cd frontend
npm run build
cd ..
```

開発中は、変更を自動的にコンパイルするために以下を実行できます：
```bash
cd frontend
npm run watch
```

### 3. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、以下の設定を追加してください：

```env
# OpenAlex API設定
# OpenAlexはAPIキー不要ですが、User-Agentにメールアドレスを設定することが推奨されています
OPENALEX_USER_EMAIL=your-email@example.com

# Semantic Scholar API設定（将来使用）
SEMANTIC_SCHOLAR_API_KEY=

# LLM API設定（キーワード抽出用）
# プロバイダー選択: "openai", "anthropic", "ollama"
LLM_PROVIDER=openai

# OpenAI設定（LLM_PROVIDER=openaiの場合）
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Anthropic設定（LLM_PROVIDER=anthropicの場合）
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
# ANTHROPIC_MODEL=claude-3-haiku-20240307

# Ollama設定（LLM_PROVIDER=ollamaの場合、ローカルでOllamaを実行している必要があります）
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama2

# その他の設定
DEFAULT_PER_PAGE=25
MAX_PER_PAGE=200
```

**注意**: `.env` ファイルは `.gitignore` に含まれているため、Gitにはコミットされません。機密情報を安全に管理できます。

## 使い方

このプロジェクトには、以下の3つの使用方法があります：

1. **Webアプリケーション**（推奨）- ブラウザで使用
2. **エージェントモード** - CLIで対話型インターフェース
3. **CLIスクリプト** - コマンドライン引数で直接検索

### Webアプリケーション（推奨）

ChatGPTのようなWebインターフェースで論文を検索できます。

```bash
# TypeScriptをコンパイル（初回のみ、または変更時）
cd frontend
npm install
npm run build
cd ..

# サーバーを起動
python run_server.py

# または
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

ブラウザで `http://localhost:8000` にアクセスしてください。

**機能:**
- ChatGPT風のチャットインターフェース
- LLMが情報不足を検出して質問
- 検索結果の表示とJSONダウンロード
- レスポンシブデザイン（モバイル対応）

### エージェントモード（CLI対話型）

ChatGPTのような対話型インターフェースで論文を検索できます。LLMが情報が不足している場合に質問を返し、十分な情報が集まったら検索を実行します。

```bash
# エージェントモードで起動
python scripts/main.py --agent
```

**使用例:**

```
あなた: transformerについて調べたいです
アシスタント: どのような観点からtransformerについて調べたいですか？例えば、アーキテクチャ、応用、性能評価など、具体的なトピックを教えてください。

あなた: アーキテクチャの改善について、2020年以降の論文を探しています
アシスタント: 了解しました。以下の条件で検索を開始します：
- 検索クエリ: transformer architecture improvements
- 発行年フィルタ: >=2020
- 取得件数: 25件

検索を実行しますか？ (y/n): y
```

### 長文クエリの対応

このツールは、単語レベルの検索だけでなく、**長文の指定文**にも対応しています。

- **LLMベースの自動最適化（デフォルト）**: 長文（50文字以上）を入力すると、LLMを使用して重要なキーワードを自動抽出して検索します
- **そのまま検索**: `--no-optimize` オプションを使用すると、長文をそのまま検索クエリとして使用します

**LLMによるキーワード抽出の特徴:**
- 文脈を理解して適切なキーワードを抽出
- 学術的な概念や専門用語を優先
- 複合語や専門用語をそのまま保持（例: "neural network", "機械学習"）
- 一般的すぎる単語を自動的に除外

```bash
# 長文のクエリ（LLMで自動的にキーワードが抽出される）
python scripts/main.py "I am interested in finding research papers about transformer neural networks that have been used for natural language processing tasks, particularly focusing on attention mechanisms"

# 長文をそのまま検索（最適化を無効化）
python scripts/main.py "長い文章をそのまま検索したい場合..." --no-optimize
```

**注意**: LLMを使用するには、`.env`ファイルに適切なAPIキーを設定する必要があります（OpenAI、Anthropic、またはOllama）。

### Pythonコードでの使用

プログラムから直接使用する場合：

```python
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.search.openalex_search import OpenAlexSearch

# 検索オブジェクトを作成
search = OpenAlexSearch()

# 論文を検索（最初の25件を取得）
result = search.search_papers("machine learning", per_page=25)
papers = result.get("results", [])

# 論文情報を整形して表示
for paper in papers:
    formatted = search.format_paper_info(paper)
    print(f"タイトル: {formatted['title']}")
    print(f"著者: {', '.join(formatted['authors'])}")
    print(f"発行年: {formatted['publication_year']}")
    print(f"DOI: {formatted['doi']}")
```

**その他の使用例:**

```python
# 網羅的な論文取得（最大100件）
papers = search.get_all_papers(
    query="transformer neural network",
    max_results=100,
    sort="cited_by_count:desc"  # 被引用数順
)

# フィルタリングを使った検索（2020年以降）
filter_params = {"publication_year": ">=2020"}
result = search.search_papers(
    query="large language model",
    filter_params=filter_params
)
```

### CLIスクリプトの使用

`scripts/main.py` を使用すると、簡単に論文を検索できます：

```bash
# 対話モード（最も簡単）
python scripts/main.py

# または、コマンドライン引数で直接検索
python scripts/main.py "machine learning"

# 2020年以降の論文を検索
python scripts/main.py "transformer" --year ">=2020"

# 最大100件を取得してJSONに保存
python scripts/main.py "neural network" --all --max-results 100 --output results.json

# 被引用数順でソート
python scripts/main.py "deep learning" --sort "cited_by_count:desc"

# 要約も表示
python scripts/main.py "computer vision" --abstract

# ヘルプを表示
python scripts/main.py --help
```

### サンプルスクリプトの実行

```bash
# 様々な使用例を実行
python scripts/search_example.py
```

**注意**: サンプルスクリプトは、プロジェクトの構造を理解するための参考例です。

## 機能

### 1. OpenAlex APIを使用した論文の網羅的取得

ユーザーが入力したテーマに基づいて、以下の流れで論文を取得します：

1. **OpenAlex APIで論文検索**: 指定されたテーマに関連する論文を網羅的に検索します
2. **Semantic Scholarで要約・PDF取得**: 検索結果の各論文について、Semantic ScholarのAPIを使用して要約情報を取得し、PDFファイルをダウンロードします

これにより、特定の研究テーマに関する最新の論文を効率的に収集し、要約情報とPDFを一括で取得できます。

### 2. PDF論文の詳細解説

ユーザーがアップロードしたPDF論文の内容を詳細に解説します。論文の要点、研究方法、結果、考察などを分かりやすく説明することで、論文の理解を深めることができます。
