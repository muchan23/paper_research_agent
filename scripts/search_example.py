"""
論文検索の使用例
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.search.openalex_search import OpenAlexSearch
import json


def example_basic_search():
    """基本的な検索の例"""
    print("=" * 60)
    print("例1: 基本的な検索")
    print("=" * 60)
    
    search = OpenAlexSearch()
    query = "transformer neural network"
    
    # 最初の25件を取得
    result = search.search_papers(query, per_page=10)
    papers = result.get("results", [])
    
    print(f"\n検索クエリ: {query}")
    print(f"検索結果: {len(papers)}件\n")
    
    # 最初の3件を表示
    for i, paper in enumerate(papers[:3], 1):
        formatted = search.format_paper_info(paper)
        print(f"【論文 {i}】")
        print(f"タイトル: {formatted['title']}")
        print(f"著者: {', '.join(formatted['authors'][:3])}{'...' if len(formatted['authors']) > 3 else ''}")
        print(f"発行年: {formatted['publication_year']}")
        print(f"被引用数: {formatted['citation_count']}")
        print("-" * 60)


def example_filtered_search():
    """フィルタリングを使った検索の例"""
    print("\n" + "=" * 60)
    print("例2: フィルタリングを使った検索（2020年以降）")
    print("=" * 60)
    
    search = OpenAlexSearch()
    query = "large language model"
    
    # 2020年以降の論文を検索
    filter_params = {
        "publication_year": ">=2020"
    }
    
    result = search.search_papers(
        query=query,
        per_page=10,
        filter_params=filter_params
    )
    papers = result.get("results", [])
    
    print(f"\n検索クエリ: {query}")
    print(f"フィルタ: 2020年以降")
    print(f"検索結果: {len(papers)}件\n")
    
    for i, paper in enumerate(papers[:3], 1):
        formatted = search.format_paper_info(paper)
        print(f"【論文 {i}】")
        print(f"タイトル: {formatted['title']}")
        print(f"発行年: {formatted['publication_year']}")
        print("-" * 60)


def example_comprehensive_search():
    """網羅的な検索の例"""
    print("\n" + "=" * 60)
    print("例3: 網羅的な検索（最大50件）")
    print("=" * 60)
    
    search = OpenAlexSearch()
    query = "reinforcement learning"
    
    # 最大50件を取得
    papers = search.get_all_papers(
        query=query,
        max_results=50,
        sort="cited_by_count:desc"  # 被引用数順
    )
    
    print(f"\n検索クエリ: {query}")
    print(f"取得件数: {len(papers)}件（被引用数順）\n")
    
    # 上位5件を表示
    for i, paper in enumerate(papers[:5], 1):
        formatted = search.format_paper_info(paper)
        print(f"【論文 {i}】")
        print(f"タイトル: {formatted['title']}")
        print(f"被引用数: {formatted['citation_count']}")
        print(f"発行年: {formatted['publication_year']}")
        print("-" * 60)


def example_save_results():
    """検索結果をJSONファイルに保存する例"""
    print("\n" + "=" * 60)
    print("例4: 検索結果をJSONファイルに保存")
    print("=" * 60)
    
    search = OpenAlexSearch()
    query = "computer vision"
    
    # 論文を取得
    papers = search.get_all_papers(query=query, max_results=20)
    
    # 整形された情報に変換
    formatted_papers = [search.format_paper_info(paper) for paper in papers]
    
    # JSONファイルに保存
    output_file = "search_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(formatted_papers, f, ensure_ascii=False, indent=2)
    
    print(f"\n検索クエリ: {query}")
    print(f"取得件数: {len(formatted_papers)}件")
    print(f"結果を {output_file} に保存しました")


def interactive_search():
    """対話的な検索"""
    print("\n" + "=" * 60)
    print("対話的な検索")
    print("=" * 60)
    
    search = OpenAlexSearch()
    
    while True:
        query = input("\n検索クエリを入力してください（終了する場合は 'q'）: ").strip()
        
        if query.lower() == 'q':
            print("終了します。")
            break
        
        if not query:
            print("検索クエリを入力してください。")
            continue
        
        try:
            result = search.search_papers(query, per_page=5)
            papers = result.get("results", [])
            
            print(f"\n検索結果: {len(papers)}件\n")
            
            for i, paper in enumerate(papers, 1):
                formatted = search.format_paper_info(paper)
                print(f"【論文 {i}】")
                print(f"タイトル: {formatted['title']}")
                print(f"著者: {', '.join(formatted['authors'][:2])}{'...' if len(formatted['authors']) > 2 else ''}")
                print(f"発行年: {formatted['publication_year']}")
                print(f"DOI: {formatted['doi']}")
                print("-" * 60)
        
        except Exception as e:
            print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    # 各例を実行
    example_basic_search()
    example_filtered_search()
    example_comprehensive_search()
    example_save_results()
    
    # 対話的な検索を実行する場合は、以下のコメントを外してください
    # interactive_search()

