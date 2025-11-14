"""
LLMを使用してキーワードを抽出するモジュール
"""
import json
import re
from typing import List, Optional
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config


class LLMKeywordExtractor:
    """LLMを使用してキーワードを抽出するクラス"""
    
    def __init__(self, provider: Optional[str] = None):
        """
        LLMKeywordExtractorの初期化
        
        Args:
            provider: LLMプロバイダー（"openai", "anthropic", "ollama"）
                      Noneの場合はconfig.pyから読み込む
        """
        self.provider = provider or Config.LLM_PROVIDER
        self._initialize_client()
    
    def _initialize_client(self):
        """LLMクライアントを初期化"""
        if self.provider == "openai":
            try:
                from openai import OpenAI
                if not Config.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEYが設定されていません。.envファイルに設定してください。")
                self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
                self.model = Config.OPENAI_MODEL
            except ImportError:
                raise ImportError("openaiライブラリがインストールされていません。pip install openai を実行してください。")
        
        elif self.provider == "anthropic":
            try:
                import anthropic
                if not Config.ANTHROPIC_API_KEY:
                    raise ValueError("ANTHROPIC_API_KEYが設定されていません。.envファイルに設定してください。")
                self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
                self.model = Config.ANTHROPIC_MODEL
            except ImportError:
                raise ImportError("anthropicライブラリがインストールされていません。pip install anthropic を実行してください。")
        
        elif self.provider == "ollama":
            import requests
            self.client = requests.Session()
            self.base_url = Config.OLLAMA_BASE_URL
            self.model = Config.OLLAMA_MODEL
        
        else:
            raise ValueError(f"サポートされていないプロバイダー: {self.provider}")
    
    def extract_keywords(
        self,
        text: str,
        max_keywords: int = 10,
        language: str = "auto"
    ) -> List[str]:
        """
        LLMを使用してテキストからキーワードを抽出する
        
        Args:
            text: 抽出元のテキスト
            max_keywords: 抽出する最大キーワード数
            language: 言語（"auto", "en", "ja"）
        
        Returns:
            抽出されたキーワードのリスト
        """
        prompt = self._create_prompt(text, max_keywords, language)
        
        try:
            if self.provider == "openai":
                response = self._call_openai(prompt)
            elif self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            elif self.provider == "ollama":
                response = self._call_ollama(prompt)
            else:
                raise ValueError(f"サポートされていないプロバイダー: {self.provider}")
            
            keywords = self._parse_response(response)
            return keywords[:max_keywords]
        
        except Exception as e:
            print(f"LLMキーワード抽出エラー: {e}")
            # フォールバック: シンプルな抽出方法
            return self._fallback_extract(text, max_keywords)
    
    def _create_prompt(self, text: str, max_keywords: int, language: str) -> str:
        """キーワード抽出用のプロンプトを作成"""
        lang_instruction = ""
        if language == "ja":
            lang_instruction = "日本語のテキストから、学術論文検索に有用なキーワードを抽出してください。"
        elif language == "en":
            lang_instruction = "Extract keywords that are useful for academic paper search from the English text."
        else:
            lang_instruction = "Extract keywords that are useful for academic paper search from the text. The text may be in English or Japanese."
        
        prompt = f"""あなたは学術論文検索の専門家です。以下のテキストから、論文検索に最も有用なキーワードを{max_keywords}個抽出してください。

{lang_instruction}

要件:
- 学術的な概念、技術用語、研究分野名を優先する
- 一般的すぎる単語（"the", "is", "の", "に"など）は除外する
- 複合語や専門用語はそのまま保持する（例: "neural network", "機械学習"）
- キーワードはカンマ区切りで出力する
- JSON形式で出力する（例: {{"keywords": ["keyword1", "keyword2", ...]}}）

テキスト:
{text}

キーワードをJSON形式で出力してください:"""
        
        return prompt
    
    def _call_openai(self, prompt: str) -> str:
        """OpenAI APIを呼び出す"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts keywords from text for academic paper search."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        return response.choices[0].message.content
    
    def _call_anthropic(self, prompt: str) -> str:
        """Anthropic APIを呼び出す"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    
    def _call_ollama(self, prompt: str) -> str:
        """Ollama APIを呼び出す"""
        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 200
                }
            }
        )
        response.raise_for_status()
        return response.json().get("response", "")
    
    def _parse_response(self, response: str) -> List[str]:
        """LLMのレスポンスをパースしてキーワードリストを取得"""
        # JSON形式を探す
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                if "keywords" in data and isinstance(data["keywords"], list):
                    return [kw.strip() for kw in data["keywords"] if kw.strip()]
            except json.JSONDecodeError:
                pass
        
        # JSONが見つからない場合、カンマ区切りのリストを探す
        # "keywords:" や "キーワード:" の後に続く部分を探す
        keyword_patterns = [
            r'keywords?[:\s]+\[(.*?)\]',
            r'キーワード[:\s]+\[(.*?)\]',
            r'\[(.*?)\]',
        ]
        
        for pattern in keyword_patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                keywords_str = match.group(1)
                keywords = [kw.strip().strip('"\'') for kw in keywords_str.split(',')]
                return [kw for kw in keywords if kw]
        
        # それでも見つからない場合、カンマ区切りのテキストを探す
        lines = response.split('\n')
        for line in lines:
            if ',' in line and len(line.split(',')) > 1:
                keywords = [kw.strip().strip('"\'') for kw in line.split(',')]
                if all(kw for kw in keywords):
                    return keywords
        
        # 最後の手段: 単語を抽出
        return self._fallback_extract(response, 10)
    
    def _fallback_extract(self, text: str, max_keywords: int) -> List[str]:
        """フォールバック: シンプルなキーワード抽出"""
        # 英語の単語（3文字以上）
        english_words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        # 日本語の単語
        japanese_words = re.findall(r'[一-龠々]+|[あ-ん]{2,}|[ア-ン]{2,}', text)
        words = english_words + japanese_words
        
        # ストップワードを除去
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'has', 'let', 'put', 'say', 'she', 'too', 'use'}
        words = [w for w in words if w not in stopwords]
        
        # 頻度でソート
        from collections import Counter
        word_counts = Counter(words)
        return [word for word, count in word_counts.most_common(max_keywords)]


def main():
    """テスト用のメイン関数"""
    extractor = LLMKeywordExtractor()
    
    test_text = """
    I am interested in finding research papers about transformer neural networks
    that have been used for natural language processing tasks, particularly
    focusing on attention mechanisms and their applications in machine translation
    and text generation.
    """
    
    print("テストテキスト:")
    print(test_text)
    print("\n" + "=" * 80)
    
    keywords = extractor.extract_keywords(test_text, max_keywords=10)
    print("\n抽出されたキーワード:")
    print(keywords)


if __name__ == "__main__":
    main()

