"""
論文研究エージェント - Web APIサーバー
FastAPIを使用したバックエンドAPI
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.paper_research_agent import PaperResearchAgent

app = FastAPI(title="論文研究エージェント API")

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# セッション管理（簡易版：本番環境ではRedisなどを使用）
sessions: Dict[str, PaperResearchAgent] = {}


class MessageRequest(BaseModel):
    """メッセージリクエスト"""
    session_id: Optional[str] = None
    message: str


class SearchRequest(BaseModel):
    """検索実行リクエスト"""
    session_id: str


class ResetRequest(BaseModel):
    """セッションリセットリクエスト"""
    session_id: str


# 静的ファイルを提供
frontend_dir = project_root / "frontend" / "static"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """フロントエンドを返す"""
    return FileResponse(str(frontend_dir / "index.html"))


@app.post("/api/chat")
async def chat(request: MessageRequest):
    """
    チャットメッセージを処理する
    
    Args:
        request: メッセージリクエスト
    
    Returns:
        レスポンスメッセージと検索実行フラグ
    """
    # セッションIDがなければ新規作成
    if not request.session_id or request.session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = PaperResearchAgent()
    else:
        session_id = request.session_id
    
    agent = sessions[session_id]
    
    try:
        # ユーザーの入力を処理
        response, should_search = agent.process_user_input(request.message)
        
        return {
            "session_id": session_id,
            "response": response,
            "should_search": should_search,
            "collected_info": agent.collected_info if should_search else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search(request: SearchRequest):
    """
    検索を実行する
    
    Args:
        request: 検索リクエスト
    
    Returns:
        検索結果
    """
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    agent = sessions[request.session_id]
    
    try:
        # 検索を実行
        results = agent.execute_search()
        
        return {
            "session_id": request.session_id,
            "results": results,
            "summary": agent.get_search_summary(),
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
async def reset_session(request: ResetRequest):
    """
    セッションをリセットする
    
    Args:
        request: リセットリクエスト
    
    Returns:
        成功メッセージ
    """
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    agent = sessions[request.session_id]
    agent.reset()
    
    return {
        "message": "セッションをリセットしました",
        "session_id": request.session_id
    }


@app.get("/api/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

