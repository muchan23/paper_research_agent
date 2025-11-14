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
    
    # LLM API設定（キーワード抽出用）
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai", "anthropic", "ollama"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    
    # その他の設定
    DEFAULT_PER_PAGE = int(os.getenv("DEFAULT_PER_PAGE", "25"))
    MAX_PER_PAGE = int(os.getenv("MAX_PER_PAGE", "200"))

