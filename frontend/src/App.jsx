import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './index.css';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [url, setUrl] = useState('');
  const [token, setToken] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [metadata, setMetadata] = useState(null);
  const [isIngesting, setIsIngesting] = useState(false);
  
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [isThinking, setIsThinking] = useState(false);

  const handleIngest = async () => {
    if (!url) return;
    setIsIngesting(true);
    try {
      const res = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, ...(token ? { token } : {}) })
      });
      const data = await res.json();
      if (res.ok) {
        setSessionId(data.session_id);
        setMetadata(data.metadata);
        setMessages([{ role: 'ai', content: `Successfully ingested repository **${data.metadata.repo_name}**! What would you like to know?`, sources: [] }]);
      } else {
        const errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail || 'Error ingesting repository');
        alert(errorMsg);
      }
    } catch (e) {
      alert('Network error communicating with the API');
    }
    setIsIngesting(false);
  };

  const handleChat = async (e) => {
    e.preventDefault();
    if (!query || !sessionId || isThinking) return;

    const userMessage = { role: 'user', content: query, sources: [] };
    setMessages(prev => [...prev, userMessage]);
    const currentQuery = query;
    setQuery('');
    setIsThinking(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuery, session_id: sessionId })
      });
      const data = await res.json();
      if (res.ok) {
        setMessages(prev => [...prev, { role: 'ai', content: data.answer, sources: data.sources }]);
      } else {
        setMessages(prev => [...prev, { role: 'ai', content: `Error: ${data.detail}`, sources: [] }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'ai', content: 'Network error communicating with the API.', sources: [] }]);
    }
    setIsThinking(false);
  };

  const clearChat = async () => {
    if (!sessionId) return;
    await fetch(`${API_BASE}/clear?session_id=${sessionId}`, { method: 'POST' });
    setMessages([]);
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <h2>Configuration</h2>
        
        <div className="input-group">
          <label>GitHub Repository</label>
          <div style={{ display: 'flex', alignItems: 'stretch', borderRadius: '0.75rem', border: '1px solid var(--border)', background: 'rgba(15, 17, 26, 0.6)', overflow: 'hidden', transition: 'all 0.3s ease' }}>
            <div style={{ padding: '0.85rem 0.5rem 0.85rem 1rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.02)', borderRight: '1px solid rgba(255,255,255,0.05)', userSelect: 'none', display: 'flex', alignItems: 'center', fontFamily: 'Inter, sans-serif', fontSize: '0.95rem' }}>
              https://github.com/
            </div>
            <input 
              type="text" 
              placeholder="owner/repo" 
              value={url.replace('https://github.com/', '')}
              onChange={(e) => {
                 let val = e.target.value;
                 if (val.startsWith('https://github.com/')) {
                     val = val.replace('https://github.com/', '');
                 }
                 setUrl(`https://github.com/${val}`);
              }}
              style={{ border: 'none', borderRadius: 0, background: 'transparent', flex: 1, boxShadow: 'none', outline: 'none' }}
            />
          </div>
        </div>

        <div className="input-group">
          <label>GitHub Token (Optional)</label>
          <input 
            type="password" 
            placeholder="Avoid rate limits"
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
        </div>

        <button 
          className="primary" 
          onClick={handleIngest}
          disabled={isIngesting || !url}
        >
          {isIngesting ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
              <div className="loading-spinner" style={{ width: '1rem', height: '1rem', borderWidth: '2px' }}></div>
              Ingesting...
            </span>
          ) : 'Ingest Repository'}
        </button>

        {metadata && (
          <div className="metadata-card">
            <p>Files: <span>{metadata.file_count}</span></p>
            <p>Chunks: <span>{metadata.chunk_count}</span></p>
            <p>Languages: <span>{metadata.languages.join(', ')}</span></p>
          </div>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="chat-area">
        <div className="chat-header">
          <h2>Code Chat Assistant</h2>
          {sessionId && (
            <button className="primary" onClick={clearChat} style={{ padding: '0.5rem 1rem' }}>
              Clear Chat
            </button>
          )}
        </div>

        <div className="messages">
          {!sessionId && (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '2rem' }}>
              Enter a repository URL in the sidebar to get started.
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <ReactMarkdown>{msg.content}</ReactMarkdown>
              {msg.sources?.length > 0 && (
                <div className="message-sources">
                  <strong>Sources:</strong>
                  <ul>
                    {msg.sources.map((s, i) => (
                      <li key={i}><a href={s.url} target="_blank" rel="noreferrer">{s.file_path}</a></li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
          
          {isThinking && (
            <div className="message ai">
              <div className="loading-spinner"></div>
            </div>
          )}
        </div>

        <div className="chat-input-container">
          <form className="chat-form" onSubmit={handleChat}>
            <input 
              type="text" 
              placeholder="Ask a question about the codebase..." 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={!sessionId || isThinking}
            />
            <button className="primary" type="submit" disabled={!sessionId || !query || isThinking}>
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
