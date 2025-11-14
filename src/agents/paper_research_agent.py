"""
論文研究エージェント
ChatGPTのような対話型インターフェースで論文を検索する
"""
import json
from typing import Dict, List, Optional, Tuple
from enum import Enum
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.llm_extractor import LLMKeywordExtractor
from src.search.openalex_search import OpenAlexSearch
from src.utils.config import Config


class ConversationState(Enum):
    """会話の状態"""
    COLLECTING_INFO = "collecting_info"  # 情報収集中
    SEARCHING = "searching"  # 検索中
    COMPLETED = "completed"  # 完了


class PaperResearchAgent:
    """論文研究エージェントクラス"""
    
    def __init__(self, llm_provider: Optional[str] = None):
        """
        PaperResearchAgentの初期化
        
        Args:
            llm_provider: LLMプロバイダー（Noneの場合はconfig.pyから読み込む）
        """
        self.llm_extractor = LLMKeywordExtractor(provider=llm_provider)
        self.search = OpenAlexSearch(auto_optimize_query=False)  # LLMで最適化するのでFalse
        self.state = ConversationState.COLLECTING_INFO
        self.conversation_history: List[Dict[str, str]] = []
        self.collected_info: Dict[str, str] = {
            "query": "",
            "year_filter": "",
            "max_results": "25"
        }
        self.search_results: List[Dict] = []
    
    def process_user_input(self, user_input: str) -> Tuple[str, bool]:
        """
        ユーザーの入力を処理する
        
        Args:
            user_input: ユーザーの入力テキスト
        
        Returns:
            (レスポンスメッセージ, 検索を実行するかどうか)
        """
        # 会話履歴に追加
        self.conversation_history.append({"role": "user", "content": user_input})
        
        if self.state == ConversationState.COLLECTING_INFO:
            # 情報収集フェーズ
            response, should_search = self._collect_information(user_input)
            self.conversation_history.append({"role": "assistant", "content": response})
            
            if should_search:
                self.state = ConversationState.SEARCHING
                return response, True
            else:
                return response, False
        
        elif self.state == ConversationState.SEARCHING:
            # 検索フェーズ（通常はここには来ないが、追加の質問などに対応）
            return "検索を実行中です。しばらくお待ちください。", False
        
        else:
            # 完了後（追加の質問など）
            return "検索は完了しました。新しい検索を開始する場合は、調べたい論文について教えてください。", False
    
    def _collect_information(self, user_input: str) -> Tuple[str, bool]:
        """
        情報を収集する
        
        Args:
            user_input: ユーザーの入力
        
        Returns:
            (レスポンスメッセージ, 検索を実行するかどうか)
        """
        # LLMに情報が十分かどうか判断させる
        analysis_prompt = self._create_analysis_prompt(user_input)
        
        try:
            analysis = self._call_llm_for_analysis(analysis_prompt)
            
            # 分析結果をパース
            if analysis.get("sufficient", False):
                # 情報が十分な場合
                query = analysis.get("extracted_query", user_input)
                year_filter = analysis.get("year_filter", "")
                max_results = analysis.get("max_results", "25")
                
                self.collected_info = {
                    "query": query,
                    "year_filter": year_filter,
                    "max_results": max_results
                }
                
                return f"了解しました。以下の条件で検索を開始します：\n- 検索クエリ: {query}\n- 発行年フィルタ: {year_filter if year_filter else '指定なし'}\n- 取得件数: {max_results}件\n\n検索を実行しますか？", True
            else:
                # 情報が不足している場合、質問を生成
                question = analysis.get("question", "もう少し詳しく教えてください。")
                return question, False
        
        except Exception as e:
            print(f"エラー: {e}")
            # エラー時は、入力されたテキストをそのままクエリとして使用
            self.collected_info = {
                "query": user_input,
                "year_filter": "",
                "max_results": "25"
            }
            return f"了解しました。'{user_input}' で検索を開始します。", True
    
    def _create_analysis_prompt(self, user_input: str) -> str:
        """情報分析用のプロンプトを作成"""
        prompt = f"""あなたは論文検索アシスタントです。ユーザーの入力から、論文検索に必要な情報を抽出し、不足している情報があれば質問してください。

現在の会話履歴:
{json.dumps(self.conversation_history[-5:], ensure_ascii=False, indent=2)}

ユーザーの最新の入力:
{user_input}

以下のJSON形式で回答してください:
{{
    "sufficient": true/false,  // 検索に十分な情報があるか
    "extracted_query": "検索クエリ（キーワードを抽出）",
    "year_filter": "発行年フィルタ（例: >=2020, 2020-2023、指定がない場合は空文字）",
    "max_results": "取得件数（デフォルト: 25）",
    "question": "情報が不足している場合の質問（sufficientがfalseの場合）"
}}

情報が十分な場合の例:
{{
    "sufficient": true,
    "extracted_query": "transformer neural network attention mechanism",
    "year_filter": ">=2020",
    "max_results": "50",
    "question": ""
}}

情報が不足している場合の例:
{{
    "sufficient": false,
    "extracted_query": "",
    "year_filter": "",
    "max_results": "25",
    "question": "どのような研究分野やトピックについて調べたいですか？具体的なキーワードやテーマを教えてください。"
}}

JSON形式で回答してください:"""
        
        return prompt
    
    def _call_llm_for_analysis(self, prompt: str) -> Dict:
        """LLMを呼び出して分析結果を取得"""
        try:
            if Config.LLM_PROVIDER == "openai":
                from openai import OpenAI
                if not Config.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEYが設定されていません")
                client = OpenAI(api_key=Config.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that helps users search for academic papers. Always respond in valid JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content
                result = json.loads(result_text)
            
            elif Config.LLM_PROVIDER == "anthropic":
                import anthropic
                if not Config.ANTHROPIC_API_KEY:
                    raise ValueError("ANTHROPIC_API_KEYが設定されていません")
                client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
                message = client.messages.create(
                    model=Config.ANTHROPIC_MODEL,
                    max_tokens=500,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                result_text = message.content[0].text
                # JSON部分を抽出
                import re
                json_match = re.search(r'\{[^}]+\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = json.loads(result_text)
            
            else:
                # フォールバック
                result = {
                    "sufficient": True,
                    "extracted_query": "",
                    "year_filter": "",
                    "max_results": "25",
                    "question": ""
                }
            
            # 結果の検証
            if "sufficient" not in result:
                result["sufficient"] = False
            if "extracted_query" not in result:
                result["extracted_query"] = ""
            if "year_filter" not in result:
                result["year_filter"] = ""
            if "max_results" not in result:
                result["max_results"] = "25"
            if "question" not in result:
                result["question"] = ""
            
            return result
        
        except json.JSONDecodeError as e:
            print(f"JSON解析エラー: {e}")
            # フォールバック
            return {
                "sufficient": True,
                "extracted_query": "",
                "year_filter": "",
                "max_results": "25",
                "question": ""
            }
        except Exception as e:
            print(f"LLM呼び出しエラー: {e}")
            # フォールバック
            return {
                "sufficient": True,
                "extracted_query": "",
                "year_filter": "",
                "max_results": "25",
                "question": ""
            }
    
    def execute_search(self) -> List[Dict]:
        """
        検索を実行する
        
        Returns:
            検索結果のリスト
        """
        if self.state != ConversationState.SEARCHING:
            return []
        
        try:
            query = self.collected_info["query"]
            year_filter = self.collected_info.get("year_filter", "")
            max_results = int(self.collected_info.get("max_results", "25"))
            
            # フィルタパラメータを構築
            filter_params = None
            if year_filter:
                filter_params = {"publication_year": year_filter}
            
            # 検索を実行
            if max_results > 200:
                # 網羅的に取得
                papers = self.search.get_all_papers(
                    query=query,
                    max_results=max_results,
                    filter_params=filter_params
                )
            else:
                # 通常の検索
                result = self.search.search_papers(
                    query=query,
                    per_page=min(max_results, 200),
                    filter_params=filter_params
                )
                papers = result.get("results", [])
            
            # 結果を整形
            self.search_results = [self.search.format_paper_info(paper) for paper in papers]
            self.state = ConversationState.COMPLETED
            
            return self.search_results
        
        except Exception as e:
            print(f"検索エラー: {e}")
            self.state = ConversationState.COMPLETED
            return []
    
    def get_search_summary(self) -> str:
        """検索結果のサマリーを取得"""
        if not self.search_results:
            return "検索結果がありません。"
        
        summary = f"検索結果: {len(self.search_results)}件\n\n"
        summary += "【上位5件】\n\n"
        
        for i, paper in enumerate(self.search_results[:5], 1):
            summary += f"{i}. {paper['title']}\n"
            summary += f"   著者: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}\n"
            summary += f"   発行年: {paper['publication_year']}\n"
            summary += f"   被引用数: {paper['citation_count']}\n"
            if paper['doi']:
                summary += f"   DOI: {paper['doi']}\n"
            summary += "\n"
        
        return summary
    
    def reset(self):
        """会話をリセット"""
        self.state = ConversationState.COLLECTING_INFO
        self.conversation_history = []
        self.collected_info = {
            "query": "",
            "year_filter": "",
            "max_results": "25"
        }
        self.search_results = []


def main():
    """対話型のメイン関数"""
    print("=" * 80)
    print("論文研究エージェント")
    print("=" * 80)
    print("\n調べたい論文について教えてください。")
    print("情報が不足している場合は、質問させていただきます。")
    print("'quit' または 'exit' で終了します。\n")
    
    agent = PaperResearchAgent()
    
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


if __name__ == "__main__":
    main()

