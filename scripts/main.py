#!/usr/bin/env python3
"""
論文検索メインスクリプト
ユーザーが自由に論文を検索できるCLIツール
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.search.openalex_search import OpenAlexSearch
from src.agents.paper_research_agent import PaperResearchAgent


def print_paper(paper_info: Dict, index: int, show_abstract: bool = False):
    """論文情報を整形して表示"""
    print(f"\n【論文 {index}】")
    print(f"タイトル: {paper_info['title']}")
    print(f"著者: {', '.join(paper_info['authors'][:5])}{'...' if len(paper_info['authors']) > 5 else ''}")
    print(f"発行年: {paper_info['publication_year']}")
    if paper_info['doi']:
        print(f"DOI: {paper_info['doi']}")
    print(f"被引用数: {paper_info['citation_count']}")
    print(f"オープンアクセス: {'Yes' if paper_info['open_access'] else 'No'}")
    if paper_info['pdf_url']:
        print(f"PDF URL: {paper_info['pdf_url']}")
    if paper_info['primary_location']:
        print(f"URL: {paper_info['primary_location']}")
    if show_abstract and paper_info['abstract']:
        print(f"\n要約:\n{paper_info['abstract'][:500]}...")
    print("-" * 80)


def interactive_mode():
    """対話的な検索モード"""
    print("=" * 80)
    print("論文検索ツール - 対話モード")
    print("=" * 80)
    print("\n検索クエリを入力してください。'q' または 'quit' で終了します。")
    print("長文のクエリも入力できます。自動的にキーワードが抽出されます。\n")
    
    search = OpenAlexSearch()
    
    while True:
        try:
            query = input("検索クエリ: ").strip()
            
            if query.lower() in ['q', 'quit', 'exit']:
                print("\n終了します。")
                break
            
            if not query:
                print("検索クエリを入力してください。")
                continue
            
            # 検索オプションを入力
            print("\n検索オプション（Enterでスキップ）:")
            per_page_input = input("取得件数 (デフォルト: 25): ").strip()
            per_page = int(per_page_input) if per_page_input else 25
            
            year_filter = input("発行年フィルタ (例: >=2020, <=2020, 2020-2023): ").strip()
            filter_params = None
            if year_filter:
                filter_params = {"publication_year": year_filter}
            
            print(f"\n検索中: '{query}'...")
            
            result = search.search_papers(
                query=query,
                per_page=per_page,
                filter_params=filter_params
            )
            papers = result.get("results", [])
            
            if not papers:
                print("検索結果が見つかりませんでした。")
                continue
            
            print(f"\n検索結果: {len(papers)}件\n")
            
            # 論文を表示
            for i, paper in enumerate(papers, 1):
                formatted = search.format_paper_info(paper)
                print_paper(formatted, i)
            
            # 保存オプション
            save = input("\n結果をJSONファイルに保存しますか？ (y/n): ").strip().lower()
            if save == 'y':
                filename = input("ファイル名 (デフォルト: search_results.json): ").strip()
                filename = filename if filename else "search_results.json"
                
                formatted_papers = [search.format_paper_info(p) for p in papers]
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(formatted_papers, f, ensure_ascii=False, indent=2)
                print(f"結果を {filename} に保存しました。\n")
        
        except KeyboardInterrupt:
            print("\n\n中断されました。終了します。")
            break
        except Exception as e:
            print(f"\nエラーが発生しました: {e}\n")


def command_line_mode(args):
    """コマンドライン引数モード"""
    search = OpenAlexSearch(auto_optimize_query=not args.no_optimize)
    
    # フィルタパラメータを構築
    filter_params = None
    if args.year:
        filter_params = {"publication_year": args.year}
    
    print(f"検索中: '{args.query}'...")
    
    try:
        if args.all:
            # 網羅的に取得
            papers = search.get_all_papers(
                query=args.query,
                max_results=args.max_results,
                sort=args.sort,
                filter_params=filter_params
            )
            print(f"\n取得完了: {len(papers)}件\n")
        else:
            # 通常の検索
            result = search.search_papers(
                query=args.query,
                per_page=args.per_page,
                page=args.page,
                sort=args.sort,
                filter_params=filter_params
            )
            papers = result.get("results", [])
            meta = result.get("meta", {})
            total_count = meta.get("count", len(papers))
            print(f"\n検索結果: {len(papers)}件 / 全{total_count}件\n")
        
        if not papers:
            print("検索結果が見つかりませんでした。")
            return
        
        # 論文を表示
        for i, paper in enumerate(papers, 1):
            formatted = search.format_paper_info(paper)
            print_paper(formatted, i, show_abstract=args.abstract)
        
        # 結果を保存
        if args.output:
            formatted_papers = [search.format_paper_info(p) for p in papers]
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(formatted_papers, f, ensure_ascii=False, indent=2)
            print(f"\n結果を {args.output} に保存しました。")
    
    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="OpenAlex APIを使用して論文を検索するツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 対話モード
  python main.py

  # 基本的な検索
  python main.py "machine learning"

  # 2020年以降の論文を検索
  python main.py "transformer" --year ">=2020"

  # 最大100件を取得してJSONに保存
  python main.py "neural network" --all --max-results 100 --output results.json

  # 被引用数順でソート
  python main.py "deep learning" --sort "cited_by_count:desc"
        """
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="検索クエリ（テーマやキーワード）"
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="対話モードで実行（従来の検索モード）"
    )
    
    parser.add_argument(
        "-a", "--agent",
        action="store_true",
        help="エージェントモードで実行（ChatGPT風の対話型インターフェース）"
    )
    
    parser.add_argument(
        "-n", "--per-page",
        type=int,
        default=25,
        help="1ページあたりの取得件数（デフォルト: 25）"
    )
    
    parser.add_argument(
        "-p", "--page",
        type=int,
        default=1,
        help="ページ番号（デフォルト: 1）"
    )
    
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="網羅的に取得（複数ページにわたって取得）"
    )
    
    parser.add_argument(
        "-m", "--max-results",
        type=int,
        help="取得する最大件数（--allオプション使用時）"
    )
    
    parser.add_argument(
        "-y", "--year",
        type=str,
        help="発行年フィルタ（例: >=2020, <=2020, 2020-2023）"
    )
    
    parser.add_argument(
        "-s", "--sort",
        type=str,
        default="publication_date:desc",
        help="ソート順（デフォルト: publication_date:desc）"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="結果をJSONファイルに保存するファイル名"
    )
    
    parser.add_argument(
        "--abstract",
        action="store_true",
        help="要約も表示する"
    )
    
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="クエリの自動最適化を無効化（長文をそのまま検索）"
    )
    
    args = parser.parse_args()
    
    # エージェントモード
    if args.agent:
        agent = PaperResearchAgent()
        print("=" * 80)
        print("論文研究エージェント")
        print("=" * 80)
        print("\n調べたい論文について教えてください。")
        print("情報が不足している場合は、質問させていただきます。")
        print("'quit' または 'exit' で終了します。\n")
        
        while True:
            try:
                user_input = input("あなた: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n終了します。ありがとうございました。")
                    break
                
                if not user_input:
                    continue
                
                # ユーザーの入力を処理
                response, should_search = agent.process_user_input(user_input)
                print(f"\nアシスタント: {response}\n")
                
                # 検索を実行する場合
                if should_search:
                    confirm = input("検索を実行しますか？ (y/n): ").strip().lower()
                    if confirm == 'y':
                        print("\n検索を実行中...")
                        results = agent.execute_search()
                        
                        if results:
                            print("\n" + "=" * 80)
                            print(agent.get_search_summary())
                            print("=" * 80)
                            
                            # 結果を保存するか確認
                            save = input("\n結果をJSONファイルに保存しますか？ (y/n): ").strip().lower()
                            if save == 'y':
                                filename = input("ファイル名 (デフォルト: search_results.json): ").strip()
                                filename = filename if filename else "search_results.json"
                                with open(filename, "w", encoding="utf-8") as f:
                                    json.dump(results, f, ensure_ascii=False, indent=2)
                                print(f"結果を {filename} に保存しました。")
                        else:
                            print("検索結果が見つかりませんでした。")
                        
                        # 新しい検索を開始
                        agent.reset()
                        print("\n新しい検索を開始します。調べたい論文について教えてください。\n")
                    else:
                        print("検索をキャンセルしました。\n")
            
            except KeyboardInterrupt:
                print("\n\n中断されました。終了します。")
                break
            except Exception as e:
                print(f"\nエラーが発生しました: {e}\n")
    
    # 対話モードまたはクエリが指定されていない場合
    elif args.interactive or not args.query:
        interactive_mode()
    else:
        command_line_mode(args)


if __name__ == "__main__":
    main()

