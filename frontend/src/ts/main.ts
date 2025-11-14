/**
 * 論文研究エージェント - フロントエンド
 * TypeScript実装
 */

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: Date;
}

interface ChatResponse {
    session_id: string;
    response: string;
    should_search: boolean;
    collected_info?: {
        query: string;
        year_filter: string;
        max_results: string;
    };
}

interface SearchResponse {
    session_id: string;
    results: any[];
    summary: string;
    count: number;
}

class PaperResearchAgentUI {
    private sessionId: string | null = null;
    private chatContainer: HTMLElement;
    private messageInput: HTMLTextAreaElement;
    private sendButton: HTMLButtonElement;
    private resetButton: HTMLButtonElement;
    private loadingIndicator: HTMLElement;
    private apiBaseUrl: string = '/api';

    constructor() {
        this.chatContainer = document.getElementById('chatContainer')!;
        this.messageInput = document.getElementById('messageInput') as HTMLTextAreaElement;
        this.sendButton = document.getElementById('sendButton')!;
        this.resetButton = document.getElementById('resetButton')!;
        this.loadingIndicator = document.getElementById('loadingIndicator')!;

        this.setupEventListeners();
        this.autoResizeTextarea();
    }

    private setupEventListeners(): void {
        // 送信ボタン
        this.sendButton.addEventListener('click', () => this.handleSendMessage());
        
        // Enterキーで送信（Shift+Enterで改行）
        this.messageInput.addEventListener('keydown', (e: KeyboardEvent) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });

        // リセットボタン
        this.resetButton.addEventListener('click', () => this.handleReset());
    }

    private autoResizeTextarea(): void {
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = `${Math.min(this.messageInput.scrollHeight, 200)}px`;
        });
    }

    private async handleSendMessage(): Promise<void> {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // ユーザーメッセージを表示
        this.addMessage('user', message);
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        
        // ローディング表示
        this.setLoading(true);
        this.sendButton.disabled = true;

        try {
            // APIに送信
            const response = await this.sendMessage(message);
            
            // アシスタントの応答を表示
            this.addMessage('assistant', response.response);

            // 検索が必要な場合
            if (response.should_search && response.collected_info) {
                this.showSearchConfirmation(response.collected_info);
            }
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('assistant', `エラーが発生しました: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            this.setLoading(false);
            this.sendButton.disabled = false;
        }
    }

    private async sendMessage(message: string): Promise<ChatResponse> {
        const response = await fetch(`${this.apiBaseUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: this.sessionId,
                message: message,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: ChatResponse = await response.json();
        this.sessionId = data.session_id;
        return data;
    }

    private showSearchConfirmation(collectedInfo: { query: string; year_filter: string; max_results: string }): void {
        const confirmationDiv = document.createElement('div');
        confirmationDiv.className = 'search-confirmation';
        confirmationDiv.innerHTML = `
            <div class="confirmation-content">
                <h3>検索条件の確認</h3>
                <div class="search-info">
                    <p><strong>検索クエリ:</strong> ${collectedInfo.query}</p>
                    <p><strong>発行年フィルタ:</strong> ${collectedInfo.year_filter || '指定なし'}</p>
                    <p><strong>取得件数:</strong> ${collectedInfo.max_results}件</p>
                </div>
                <div class="confirmation-buttons">
                    <button class="confirm-button" id="confirmSearchButton">検索を実行</button>
                    <button class="cancel-button" id="cancelSearchButton">キャンセル</button>
                </div>
            </div>
        `;

        this.chatContainer.appendChild(confirmationDiv);

        // 確認ボタン
        document.getElementById('confirmSearchButton')?.addEventListener('click', () => {
            this.executeSearch();
            confirmationDiv.remove();
        });

        // キャンセルボタン
        document.getElementById('cancelSearchButton')?.addEventListener('click', () => {
            confirmationDiv.remove();
        });
    }

    private async executeSearch(): Promise<void> {
        if (!this.sessionId) return;

        this.setLoading(true);
        this.addMessage('assistant', '検索を実行中です。しばらくお待ちください...');

        try {
            const response = await fetch(`${this.apiBaseUrl}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data: SearchResponse = await response.json();
            
            // 検索結果を表示
            this.displaySearchResults(data);

        } catch (error) {
            console.error('Error:', error);
            this.addMessage('assistant', `検索エラーが発生しました: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            this.setLoading(false);
        }
    }

    private displaySearchResults(data: SearchResponse): void {
        const resultsDiv = document.createElement('div');
        resultsDiv.className = 'search-results';
        resultsDiv.innerHTML = `
            <div class="results-header">
                <h3>検索結果: ${data.count}件</h3>
            </div>
            <div class="results-summary">
                ${this.formatSummary(data.summary)}
            </div>
            <div class="results-list">
                ${this.formatResults(data.results)}
            </div>
            <div class="results-actions">
                <button class="download-button" id="downloadResultsButton">結果をJSONでダウンロード</button>
            </div>
        `;

        this.chatContainer.appendChild(resultsDiv);

        // ダウンロードボタン
        document.getElementById('downloadResultsButton')?.addEventListener('click', () => {
            this.downloadResults(data.results);
        });

        // スクロール
        this.scrollToBottom();
    }

    private formatSummary(summary: string): string {
        // サマリーを整形
        return summary.split('\n').map(line => {
            if (line.trim().startsWith('【')) {
                return `<h4>${line.trim()}</h4>`;
            }
            return `<p>${line.trim()}</p>`;
        }).join('');
    }

    private formatResults(results: any[]): string {
        if (results.length === 0) {
            return '<p>検索結果が見つかりませんでした。</p>';
        }

        return results.slice(0, 10).map((paper, index) => `
            <div class="paper-item">
                <div class="paper-header">
                    <span class="paper-number">${index + 1}</span>
                    <h4 class="paper-title">${this.escapeHtml(paper.title)}</h4>
                </div>
                <div class="paper-details">
                    <p class="paper-authors">著者: ${paper.authors.slice(0, 3).join(', ')}${paper.authors.length > 3 ? '...' : ''}</p>
                    <p class="paper-meta">
                        <span>発行年: ${paper.publication_year || '不明'}</span>
                        <span>被引用数: ${paper.citation_count || 0}</span>
                        ${paper.open_access ? '<span class="oa-badge">オープンアクセス</span>' : ''}
                    </p>
                    ${paper.doi ? `<p class="paper-doi">DOI: <a href="https://doi.org/${paper.doi}" target="_blank">${paper.doi}</a></p>` : ''}
                    ${paper.pdf_url ? `<p class="paper-pdf"><a href="${paper.pdf_url}" target="_blank">PDFを開く</a></p>` : ''}
                </div>
            </div>
        `).join('');
    }

    private escapeHtml(text: string): string {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    private downloadResults(results: any[]): void {
        const dataStr = JSON.stringify(results, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `search_results_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    private addMessage(role: 'user' | 'assistant', content: string): void {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        this.chatContainer.appendChild(messageDiv);
        
        this.scrollToBottom();
    }

    private scrollToBottom(): void {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    private setLoading(loading: boolean): void {
        this.loadingIndicator.style.display = loading ? 'flex' : 'none';
        if (loading) {
            this.scrollToBottom();
        }
    }

    private async handleReset(): Promise<void> {
        if (!this.sessionId) return;

        if (!confirm('会話をリセットしますか？')) return;

        try {
            await fetch(`${this.apiBaseUrl}/reset`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                }),
            });

            // チャットをクリア
            this.chatContainer.innerHTML = `
                <div class="message assistant-message">
                    <div class="message-content">
                        会話をリセットしました。新しい検索を開始できます。
                    </div>
                </div>
            `;

            this.sessionId = null;
        } catch (error) {
            console.error('Error:', error);
            alert('リセットに失敗しました');
        }
    }
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    new PaperResearchAgentUI();
});

