# paper_research_agent

## 概要

このリポジトリは、論文研究を支援するためのエージェントです。以下の2つの主要な機能を提供します。

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、以下の設定を追加してください：

```env
# OpenAlex API設定
# OpenAlexはAPIキー不要ですが、User-Agentにメールアドレスを設定することが推奨されています
OPENALEX_USER_EMAIL=your-email@example.com

# Semantic Scholar API設定（将来使用）
SEMANTIC_SCHOLAR_API_KEY=

# その他の設定
DEFAULT_PER_PAGE=25
MAX_PER_PAGE=200
```

**注意**: `.env` ファイルは `.gitignore` に含まれているため、Gitにはコミットされません。機密情報を安全に管理できます。

## 使い方

### 基本的な論文検索

```python
from openalex_search import OpenAlexSearch

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

### 網羅的な論文取得

```python
# 最大100件の論文を取得（複数ページにわたって自動取得）
papers = search.get_all_papers(
    query="transformer neural network",
    max_results=100,
    sort="cited_by_count:desc"  # 被引用数順
)
```

### フィルタリングを使った検索

```python
# 2020年以降の論文を検索
filter_params = {"publication_year": ">=2020"}
result = search.search_papers(
    query="large language model",
    filter_params=filter_params
)
```

### サンプルスクリプトの実行

```bash
# 様々な使用例を実行
python search_example.py

# または、対話的な検索を実行
python -c "from search_example import interactive_search; interactive_search()"
```

## 機能

### 1. OpenAlex APIを使用した論文の網羅的取得

ユーザーが入力したテーマに基づいて、以下の流れで論文を取得します：

1. **OpenAlex APIで論文検索**: 指定されたテーマに関連する論文を網羅的に検索します
2. **Semantic Scholarで要約・PDF取得**: 検索結果の各論文について、Semantic ScholarのAPIを使用して要約情報を取得し、PDFファイルをダウンロードします

これにより、特定の研究テーマに関する最新の論文を効率的に収集し、要約情報とPDFを一括で取得できます。

### 2. PDF論文の詳細解説

ユーザーがアップロードしたPDF論文の内容を詳細に解説します。論文の要点、研究方法、結果、考察などを分かりやすく説明することで、論文の理解を深めることができます。
