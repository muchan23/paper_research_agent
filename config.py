"""
設定ファイル
環境変数から設定を読み込む
"""
import os
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()


class Config:
    """アプリケーションの設定クラス"""
    
    # OpenAlex API設定
    OPENALEX_USER_EMAIL = os.getenv("OPENALEX_USER_EMAIL", "your-email@example.com")
    
    # Semantic Scholar API設定（将来使用）
    SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    
    # その他の設定
    DEFAULT_PER_PAGE = int(os.getenv("DEFAULT_PER_PAGE", "25"))
    MAX_PER_PAGE = int(os.getenv("MAX_PER_PAGE", "200"))

