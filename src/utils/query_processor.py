"""
クエリ処理モジュール
長文のクエリからキーワードを抽出したり、検索クエリを最適化する
LLMを使用してキーワードを抽出する
"""
import re
from typing import List, Optional
from collections import Counter
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.llm_extractor import LLMKeywordExtractor


class QueryProcessor:
    """クエリを処理して最適化するクラス"""
    
    # 英語のストップワード（一般的すぎる単語）- フォールバック用
    ENGLISH_STOPWORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
        'had', 'what', 'said', 'each', 'which', 'their', 'time', 'if',
        'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her',
        'would', 'make', 'like', 'into', 'him', 'has', 'two', 'more',
        'very', 'after', 'words', 'long', 'about', 'get', 'through',
        'much', 'before', 'back', 'here', 'when', 'where', 'why', 'how',
        'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get',
        'come', 'made', 'may', 'part', 'over', 'new', 'sound', 'take',
        'only', 'little', 'work', 'know', 'place', 'year', 'live', 'me',
        'back', 'give', 'most', 'very', 'after', 'thing', 'our', 'just',
        'name', 'good', 'sentence', 'man', 'think', 'say', 'great', 'where',
        'help', 'through', 'much', 'before', 'line', 'right', 'too', 'mean',
        'old', 'any', 'same', 'tell', 'boy', 'follow', 'came', 'want',
        'show', 'also', 'around', 'form', 'three', 'small', 'set', 'put',
        'end', 'does', 'another', 'well', 'large', 'must', 'big', 'even',
        'such', 'because', 'turn', 'here', 'why', 'ask', 'went', 'men',
        'read', 'need', 'land', 'different', 'home', 'us', 'move', 'try',
        'kind', 'hand', 'picture', 'again', 'change', 'off', 'play',
        'spell', 'air', 'away', 'animal', 'house', 'point', 'page',
        'letter', 'mother', 'answer', 'found', 'study', 'still', 'learn',
        'should', 'America', 'world', 'high', 'every', 'near', 'add',
        'food', 'between', 'own', 'below', 'country', 'plant', 'last',
        'school', 'father', 'keep', 'tree', 'never', 'start', 'city',
        'earth', 'eye', 'light', 'thought', 'head', 'under', 'story',
        'saw', 'left', 'don\'t', 'few', 'while', 'along', 'might', 'close',
        'something', 'seem', 'next', 'hard', 'open', 'example', 'begin',
        'life', 'always', 'those', 'both', 'paper', 'together', 'got',
        'group', 'often', 'run', 'important', 'until', 'children', 'side',
        'feet', 'car', 'mile', 'night', 'walk', 'white', 'sea', 'began',
        'grow', 'took', 'river', 'four', 'carry', 'state', 'once',
        'book', 'hear', 'stop', 'without', 'second', 'later', 'miss',
        'idea', 'enough', 'eat', 'face', 'watch', 'far', 'indian',
        'really', 'almost', 'let', 'above', 'girl', 'sometimes', 'mountain',
        'cut', 'young', 'talk', 'soon', 'list', 'song', 'leave', 'family'
    }
    
    # 日本語のストップワード
    JAPANESE_STOPWORDS = {
        'の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し',
        'れ', 'さ', 'ある', 'いる', 'も', 'する', 'から', 'な', 'こと',
        'として', 'い', 'や', 'れる', 'など', 'なった', 'ありません',
        'です', 'ます', 'である', 'だ', 'である', 'である', 'である',
        'これ', 'それ', 'あれ', 'どれ', 'この', 'その', 'あの', 'どの',
        'ここ', 'そこ', 'あそこ', 'どこ', 'こちら', 'そちら', 'あちら',
        'どちら', '私', 'あなた', '彼', '彼女', '私たち', 'あなたたち',
        '彼ら', '彼女ら', '私達', 'あなた達', '彼達', '彼女達'
    }
    
    def __init__(self, use_llm: bool = True):
        """
        QueryProcessorの初期化
        
        Args:
            use_llm: LLMを使用してキーワードを抽出するか（デフォルト: True）
        """
        self.use_llm = use_llm
        if use_llm:
            try:
                self.llm_extractor = LLMKeywordExtractor()
            except Exception as e:
                print(f"警告: LLMの初期化に失敗しました。フォールバック方法を使用します: {e}")
                self.use_llm = False
                self.llm_extractor = None
        else:
            self.llm_extractor = None
    
    def extract_keywords(
        self,
        text: str,
        max_keywords: int = 10,
        min_word_length: int = 3,
        use_stopwords: bool = True
    ) -> List[str]:
        """
        テキストからキーワードを抽出する
        
        Args:
            text: 抽出元のテキスト
            max_keywords: 抽出する最大キーワード数
            min_word_length: 最小単語長（LLM使用時は無視される）
            use_stopwords: ストップワードを除去するか（LLM使用時は無視される）
        
        Returns:
            抽出されたキーワードのリスト
        """
        # LLMを使用する場合
        if self.use_llm and self.llm_extractor:
            try:
                keywords = self.llm_extractor.extract_keywords(text, max_keywords=max_keywords)
                if keywords:
                    return keywords
            except Exception as e:
                print(f"警告: LLMキーワード抽出に失敗しました。フォールバック方法を使用します: {e}")
        
        # フォールバック: 正規表現ベースの抽出
        return self._extract_keywords_regex(text, max_keywords, min_word_length, use_stopwords)
    
    def _extract_keywords_regex(
        self,
        text: str,
        max_keywords: int = 10,
        min_word_length: int = 3,
        use_stopwords: bool = True
    ) -> List[str]:
        """
        正規表現を使用してキーワードを抽出する（フォールバック用）
        
        Args:
            text: 抽出元のテキスト
            max_keywords: 抽出する最大キーワード数
            min_word_length: 最小単語長
            use_stopwords: ストップワードを除去するか
        
        Returns:
            抽出されたキーワードのリスト
        """
        # テキストを正規化
        text = text.lower()
        
        # 単語を抽出（英数字とハイフン、アンダースコアを含む）
        # 英語と日本語の両方に対応
        # 英語の単語（3文字以上）
        english_words = re.findall(r'\b[a-z]{3,}\b', text)
        # 日本語の単語（漢字、ひらがな、カタカナの連続）
        japanese_words = re.findall(r'[一-龠々]+|[あ-ん]+|[ア-ン]+', text)
        words = english_words + japanese_words
        
        # ストップワードを除去
        if use_stopwords:
            words = [w for w in words if w not in self.ENGLISH_STOPWORDS and w not in self.JAPANESE_STOPWORDS]
        
        # 最小長でフィルタ
        words = [w for w in words if len(w) >= min_word_length]
        
        # 頻度でソート
        word_counts = Counter(words)
        top_words = [word for word, count in word_counts.most_common(max_keywords)]
        
        return top_words
    
    def optimize_query(
        self,
        query: str,
        method: str = "auto",
        max_keywords: int = 10
    ) -> str:
        """
        クエリを最適化する
        
        Args:
            query: 元のクエリ
            method: 最適化方法
                - "auto": 自動判定（長文の場合はキーワード抽出、短文の場合はそのまま）
                - "keywords": キーワード抽出
                - "original": そのまま使用
            max_keywords: キーワード抽出時の最大数
        
        Returns:
            最適化されたクエリ
        """
        if method == "original":
            return query.strip()
        
        if method == "keywords":
            keywords = self.extract_keywords(query, max_keywords=max_keywords)
            return " ".join(keywords) if keywords else query.strip()
        
        # auto モード
        # 長文（50文字以上）の場合はキーワード抽出、短文の場合はそのまま
        if len(query) > 50:
            keywords = self.extract_keywords(query, max_keywords=max_keywords)
            optimized = " ".join(keywords) if keywords else query.strip()
            return optimized
        else:
            return query.strip()
    
    def split_long_query(
        self,
        query: str,
        max_length: int = 100
    ) -> List[str]:
        """
        長いクエリを複数のサブクエリに分割する
        
        Args:
            query: 元のクエリ
            max_length: サブクエリの最大長
        
        Returns:
            サブクエリのリスト
        """
        if len(query) <= max_length:
            return [query]
        
        # 文や句で分割を試みる
        sentences = re.split(r'[.!?。！？]\s*', query)
        sub_queries = []
        current_query = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_query) + len(sentence) + 1 <= max_length:
                if current_query:
                    current_query += " " + sentence
                else:
                    current_query = sentence
            else:
                if current_query:
                    sub_queries.append(current_query)
                current_query = sentence
        
        if current_query:
            sub_queries.append(current_query)
        
        return sub_queries if sub_queries else [query[:max_length]]


def main():
    """テスト用のメイン関数"""
    processor = QueryProcessor()
    
    # テストケース
    long_query = """
    I am interested in finding research papers about transformer neural networks
    that have been used for natural language processing tasks, particularly
    focusing on attention mechanisms and their applications in machine translation
    and text generation. I would like to see papers published after 2020 that
    discuss the architecture improvements and performance benchmarks.
    """
    
    print("元のクエリ:")
    print(long_query)
    print("\n" + "=" * 80)
    
    # キーワード抽出
    keywords = processor.extract_keywords(long_query, max_keywords=10)
    print("\n抽出されたキーワード:")
    print(keywords)
    
    # クエリ最適化
    optimized = processor.optimize_query(long_query, method="auto")
    print("\n最適化されたクエリ:")
    print(optimized)
    
    # 長文分割
    sub_queries = processor.split_long_query(long_query, max_length=100)
    print("\n分割されたサブクエリ:")
    for i, sub_query in enumerate(sub_queries, 1):
        print(f"{i}. {sub_query}")


if __name__ == "__main__":
    main()

