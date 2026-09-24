import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { assistantService } from '../services/api';

// ─── Small sub-components ────────────────────────────────────────────────────

const TypingDot = () => (
  <div className="typing-indicator">
    <span /><span /><span />
  </div>
);

const Message = ({ msg }) => {
  const isUser = msg.role === 'user';
  return (
    <motion.div
      className={`chat-message ${isUser ? 'user' : 'assistant'}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      {!isUser && (
        <div className="chat-avatar assistant-avatar">💧</div>
      )}
      <div className="chat-bubble">
        <p>{msg.message || msg.text}</p>
      </div>
      {isUser && (
        <div className="chat-avatar user-avatar">You</div>
      )}
    </motion.div>
  );
};

// ─── Conversation Sidebar ────────────────────────────────────────────────────

const ConversationSidebar = ({ conversations, activeId, onSelect, onNew }) => (
  <div className="chat-sidebar">
    <div className="chat-sidebar-header">
      <span>History</span>
      <button className="btn-icon-sm" onClick={onNew} title="New conversation">＋</button>
    </div>
    <div className="chat-sidebar-list">
      {conversations.length === 0 ? (
        <p className="chat-sidebar-empty">No conversations yet.</p>
      ) : (
        conversations.map(c => (
          <button
            key={c.id}
            className={`chat-sidebar-item ${c.id === activeId ? 'active' : ''}`}
            onClick={() => onSelect(c.id)}
          >
            <span className="chat-sidebar-title">{c.title}</span>
            <span className="chat-sidebar-date">
              {c.updated_at ? new Date(c.updated_at).toLocaleDateString() : ''}
            </span>
          </button>
        ))
      )}
    </div>
  </div>
);

// ─── Main Assistant Page ─────────────────────────────────────────────────────

const Assistant = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingConv, setLoadingConv] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // Load conversation list on mount
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const res = await assistantService.getConversations();
        if (res.data.success) {
          setConversations(res.data.data.conversations);
        }
      } catch {
        // non-fatal: sidebar just stays empty
      } finally {
        setLoadingHistory(false);
      }
    };
    fetchConversations();
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversation = async (convId) => {
    setLoadingConv(true);
    setError(null);
    try {
      const res = await assistantService.getConversation(convId);
      if (res.data.success) {
        const conv = res.data.data.conversation;
        setActiveConvId(conv.id);
        setMessages(conv.messages || []);
      }
    } catch {
      setError('Failed to load conversation.');
    } finally {
      setLoadingConv(false);
    }
  };

  const startNewConversation = () => {
    setActiveConvId(null);
    setMessages([]);
    setError(null);
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) return;

    setInput('');
    setSending(true);
    setError(null);

    // Optimistic UI: append user message immediately
    const optimisticMsg = { role: 'user', message: text };
    setMessages(prev => [...prev, optimisticMsg]);

    try {
      const res = await assistantService.chat(text, activeConvId);
      if (res.data.success) {
        const { conversation_id, message: assistantText } = res.data.data;

        // If new conversation, set the ID and refresh sidebar
        if (!activeConvId) {
          setActiveConvId(conversation_id);
          // Reload conversations list to show the new one
          try {
            const convRes = await assistantService.getConversations();
            if (convRes.data.success) {
              setConversations(convRes.data.data.conversations);
            }
          } catch { /* sidebar refresh is non-fatal */ }
        }

        setMessages(prev => [...prev, { role: 'assistant', message: assistantText }]);
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to send message. Please try again.');
      // Remove the optimistic user message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <motion.div
      className="assistant-page"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className="page-header" style={{ marginBottom: '1.5rem' }}>
        <div>
          <h2>AI Water Assistant</h2>
          <p className="subtitle">Ask anything about water conservation, your usage, or saving tips.</p>
        </div>
      </header>

      <div className="chat-layout">
        {/* Sidebar */}
        {!loadingHistory && (
          <ConversationSidebar
            conversations={conversations}
            activeId={activeConvId}
            onSelect={loadConversation}
            onNew={startNewConversation}
          />
        )}

        {/* Main Chat Area */}
        <div className="chat-main">
          {/* Messages */}
          <div className="chat-messages">
            {loadingConv ? (
              <div className="dashboard-loading" style={{ height: '100%' }}>
                <div className="spinner" />
                <p>Loading conversation...</p>
              </div>
            ) : isEmpty ? (
              <div className="chat-empty-state">
                <div className="chat-empty-icon">💧</div>
                <h3>Start a conversation</h3>
                <p>Ask me about your water usage, conservation tips, or how to improve your Water Saver Score.</p>
                <div className="chat-suggestions">
                  {['How can I reduce my shower usage?', 'What is a good Water Saver Score?', 'Tips for kitchen water saving'].map(s => (
                    <button key={s} className="chat-suggestion-btn" onClick={() => { setInput(s); }}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg, i) => <Message key={i} msg={msg} />)}
                {sending && (
                  <div className="chat-message assistant">
                    <div className="chat-avatar assistant-avatar">💧</div>
                    <div className="chat-bubble"><TypingDot /></div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Error Banner */}
          <AnimatePresence>
            {error && (
              <motion.div
                className="auth-error"
                style={{ margin: '0.5rem 1rem', borderRadius: '8px' }}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input Area */}
          <div className="chat-input-area">
            <textarea
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
              rows={2}
              disabled={sending || loadingConv}
            />
            <button
              className="btn-primary chat-send-btn"
              onClick={sendMessage}
              disabled={!input.trim() || sending || loadingConv}
            >
              {sending ? <span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> : '→'}
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default Assistant;
