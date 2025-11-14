"""
OpenAlex APIを使用して論文を検索するモジュール
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
from config import Config
from query_processor import QueryProcessor


class OpenAlexSearch:
    """OpenAlex APIを使用して論文を検索するクラス"""
    
    BASE_URL = "https://api.openalex.org/works"
    
    def __init__(self, user_email: Optional[str] = None, auto_optimize_query: bool = True):
        """
        OpenAlexSearchの初期化
        
        Args:
            user_email: User-Agentに設定するメールアドレス
                       （Noneの場合はconfig.pyから読み込む）
            auto_optimize_query: 長文クエリを自動的に最適化するか
        """
        self.session = requests.Session()
        # User-Agentを設定（OpenAlexの推奨事項）
        email = user_email or Config.OPENALEX_USER_EMAIL
        self.session.headers.update({
            'User-Agent': f'paper_research_agent/1.0 (mailto:{email})'
        })
        self.query_processor = QueryProcessor() if auto_optimize_query else None
    
    def _convert_filter_value(self, value: str) -> str:
        """
        OpenAlex APIのフィルタ構文に変換する
        
        Args:
            value: フィルタ値（例: ">=2020", "<=2020", "2020-2023"）
        
        Returns:
            OpenAlex APIの構文に変換された値
        """
        value = value.strip()
        
        # >=2020 -> 2020- (2020年以降)
        if value.startswith(">="):
            year = value[2:].strip()
            return f"{year}-"
        
        # <=2020 -> -2020 (2020年以前)
        if value.startswith("<="):
            year = value[2:].strip()
            return f"-{year}"
        
        # >2020 -> 2021- (2021年以降、厳密には2020より大きい)
        if value.startswith(">"):
            year = value[1:].strip()
            try:
                year_int = int(year)
                return f"{year_int + 1}-"
            except ValueError:
                return value
        
        # <2020 -> -2019 (2019年以前、厳密には2020より小さい)
        if value.startswith("<"):
            year = value[1:].strip()
            try:
                year_int = int(year)
                return f"-{year_int - 1}"
            except ValueError:
                return value
        
        # その他の場合はそのまま返す（既に正しい形式の場合）
        return value
    
    def search_papers(
        self,
        query: str,
            per_page: Optional[int] = None,
        page: int = 1,
        sort: str = "publication_date:desc",
        filter_params: Optional[Dict[str, str]] = None,
        optimize_query: Optional[bool] = None
    ) -> Dict:
        """
        指定されたクエリで論文を検索する
        
        Args:
            query: 検索クエリ（テーマやキーワード、長文も可）
            per_page: 1ページあたりの結果数（デフォルト: 25、最大: 200）
            page: ページ番号（デフォルト: 1）
            sort: ソート順（デフォルト: publication_date:desc）
            filter_params: 追加のフィルタパラメータ
                          （例: {"publication_year": ">=2020"} -> "2020-"に変換）
                          （例: {"publication_year": "2020-2023"} -> そのまま使用）
            optimize_query: クエリを最適化するか（Noneの場合はauto_optimize_queryの設定を使用）
        
        Returns:
            検索結果の辞書（results, meta, count等を含む）
        """
        # クエリの最適化
        if optimize_query is None:
            optimize_query = self.query_processor is not None
        
        if optimize_query and self.query_processor:
            original_query = query
            query = self.query_processor.optimize_query(query, method="auto")
            if query != original_query:
                print(f"クエリを最適化しました: '{original_query[:50]}...' -> '{query}'")
        
        # per_pageが指定されていない場合はデフォルト値を使用
        if per_page is None:
            per_page = Config.DEFAULT_PER_PAGE
        
        params = {
            "search": query,
            "per_page": min(per_page, Config.MAX_PER_PAGE),
            "page": page,
            "sort": sort
        }
        
        # フィルタパラメータを追加
        if filter_params:
            filter_strings = []
            for key, value in filter_params.items():
                # OpenAlex APIの構文に変換
                # >=2020 -> 2020- (2020年以降)
                # <=2020 -> -2020 (2020年以前)
                # 2020-2023 -> 2020-2023 (範囲指定)
                converted_value = self._convert_filter_value(value)
                filter_strings.append(f"{key}:{converted_value}")
            if filter_strings:
                params["filter"] = ",".join(filter_strings)
        
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"APIリクエストエラー: {e}")
            raise
    
    def get_all_papers(
        self,
        query: str,
        max_results: Optional[int] = None,
        sort: str = "publication_date:desc",
        filter_params: Optional[Dict[str, str]] = None,
        optimize_query: Optional[bool] = None
    ) -> List[Dict]:
        """
        指定されたクエリで論文を網羅的に取得する（複数ページにわたって取得）
        
        Args:
            query: 検索クエリ（テーマやキーワード）
            max_results: 取得する最大件数（Noneの場合は全て取得）
            sort: ソート順（デフォルト: publication_date:desc）
            filter_params: 追加のフィルタパラメータ
        
        Returns:
            論文のリスト
        """
        all_papers = []
        page = 1
        per_page = Config.MAX_PER_PAGE  # 1ページあたりの最大件数
        
        while True:
            result = self.search_papers(
                query=query,
                per_page=per_page,
                page=page,
                sort=sort,
                filter_params=filter_params,
                optimize_query=optimize_query
            )
            
            papers = result.get("results", [])
            if not papers:
                break
            
            all_papers.extend(papers)
            
            # 最大件数に達した場合は終了
            if max_results and len(all_papers) >= max_results:
                all_papers = all_papers[:max_results]
                break
            
            # 次のページがあるか確認
            meta = result.get("meta", {})
            page_count = meta.get("page_count", 1)
            if page >= page_count:
                break
            
            page += 1
        
        return all_papers
    
    def format_paper_info(self, paper: Dict) -> Dict:
        """
        論文情報を整形して返す
        
        Args:
            paper: OpenAlex APIから取得した論文データ
        
        Returns:
            整形された論文情報の辞書
        """
        # 著者情報を取得
        authors = []
        for authorship in paper.get("authorships", []):
            author = authorship.get("author", {})
            authors.append(author.get("display_name", "Unknown"))
        
        # DOIを取得
        doi = paper.get("doi")
        if doi:
            doi = doi.replace("https://doi.org/", "")
        
        # 公開URLを取得
        open_access = paper.get("open_access", {})
        pdf_url = None
        if open_access.get("is_oa"):
            pdf_url = open_access.get("oa_url")
        
        return {
            "id": paper.get("id"),
            "title": paper.get("title", "No title"),
            "authors": authors,
            "publication_year": paper.get("publication_year"),
            "publication_date": paper.get("publication_date"),
            "doi": doi,
            "abstract": paper.get("abstract", ""),
            "citation_count": paper.get("cited_by_count", 0),
            "pdf_url": pdf_url,
            "open_access": open_access.get("is_oa", False),
            "primary_location": paper.get("primary_location", {}).get("landing_page_url"),
        }


def main():
    """テスト用のメイン関数"""
    search = OpenAlexSearch()
    
    # テスト検索
    query = "machine learning"
    print(f"検索クエリ: {query}\n")
    
    # 最初の25件を取得
    result = search.search_papers(query, per_page=25)
    papers = result.get("results", [])
    
    print(f"検索結果: {len(papers)}件\n")
    
    # 最初の3件を表示
    for i, paper in enumerate(papers[:3], 1):
        formatted = search.format_paper_info(paper)
        print(f"【論文 {i}】")
        print(f"タイトル: {formatted['title']}")
        print(f"著者: {', '.join(formatted['authors'][:3])}{'...' if len(formatted['authors']) > 3 else ''}")
        print(f"発行年: {formatted['publication_year']}")
        print(f"DOI: {formatted['doi']}")
        print(f"被引用数: {formatted['citation_count']}")
        print(f"オープンアクセス: {'Yes' if formatted['open_access'] else 'No'}")
        if formatted['pdf_url']:
            print(f"PDF URL: {formatted['pdf_url']}")
        print("-" * 60)


if __name__ == "__main__":
    main()

