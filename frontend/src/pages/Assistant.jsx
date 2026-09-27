import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { assistantService } from '../services/api';
import Icon from '../components/Icon';

const suggestions = [
  'Where could I save water at home?',
  'How can I make my showers more efficient?',
  'What does my latest water assessment mean?',
];

function formatDate(value) {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '' : new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(date);
}

function ConversationHistory({ conversations, activeId, onSelect, onNew, loading, error, onRetry, onClose }) {
  return (
    <>
      <div className="chat-sidebar-header">
        <div><span className="chat-section-label">YOUR SPACE</span><h2>Conversations</h2></div>
        <div className="chat-history-actions">
          <button type="button" className="chat-new-button" onClick={onNew}><span aria-hidden="true">+</span> New chat</button>
          <button type="button" className="chat-close-history" onClick={onClose} aria-label="Close conversation history"><Icon name="close" /></button>
        </div>
      </div>
      <div className="chat-sidebar-list" aria-label="Conversation history">
        {loading ? <div className="chat-history-state" role="status"><span className="spinner" />Loading conversations…</div> : null}
        {!loading && error ? <div className="chat-history-state"><p>{error}</p><button type="button" className="chat-text-button" onClick={onRetry}>Try again</button></div> : null}
        {!loading && !error && conversations.length === 0 ? <p className="chat-sidebar-empty">Your conversations will appear here.</p> : null}
        {!loading && !error && conversations.map((conversation) => (
          <button
            type="button"
            key={conversation.id}
            className={`chat-sidebar-item ${conversation.id === activeId ? 'active' : ''}`}
            onClick={() => onSelect(conversation.id)}
            aria-current={conversation.id === activeId ? 'page' : undefined}
          >
            <span className="chat-sidebar-item-icon"><Icon name="assistant" size={17} /></span>
            <span className="chat-sidebar-item-copy"><span className="chat-sidebar-title">{conversation.title || 'Water Conservation Chat'}</span><span className="chat-sidebar-meta">{formatDate(conversation.updated_at)}{conversation.message_count ? ` · ${conversation.message_count} messages` : ''}</span></span>
          </button>
        ))}
      </div>
      <div className="chat-history-footer"><Icon name="water" size={17} /><span>Small changes add up to lasting impact.</span></div>
    </>
  );
}

function Message({ message }) {
  const isUser = message.role === 'user';
  return (
    <motion.article className={`chat-message ${isUser ? 'user' : 'assistant'}`} initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
      {!isUser && <span className="chat-avatar assistant-avatar" aria-hidden="true"><Icon name="water" size={18} /></span>}
      <div className="chat-message-content">
        <div className="chat-message-label">{isUser ? 'You' : 'AquaWise assistant'}{message.created_at && <time dateTime={message.created_at}>{formatDate(message.created_at)}</time>}</div>
        <div className="chat-bubble"><p>{message.message || message.text}</p>{!isUser && message.disclaimer && <small className="chat-message-disclaimer">{message.disclaimer}</small>}</div>
      </div>
      {isUser && <span className="chat-avatar user-avatar" aria-hidden="true">Y</span>}
    </motion.article>
  );
}

function Assistant() {
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [activeTitle, setActiveTitle] = useState('New conversation');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingConv, setLoadingConv] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [historyError, setHistoryError] = useState('');
  const [error, setError] = useState('');
  const [mobileHistoryOpen, setMobileHistoryOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const activeRequest = useRef(0);

  const fetchConversations = useCallback(async () => {
    setLoadingHistory(true);
    setHistoryError('');
    try {
      const response = await assistantService.getConversations();
      if (!response.data.success) throw new Error('Could not load conversations.');
      setConversations(response.data.data.conversations || []);
    } catch {
      setHistoryError('Conversation history could not be loaded.');
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  // Initial load synchronizes the conversation list with the API.
  // eslint-disable-next-line react/set-state-in-effect
  useEffect(() => { fetchConversations(); }, [fetchConversations]);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages, sending, loadingConv]);
  useEffect(() => {
    if (!mobileHistoryOpen) return undefined;
    const closeOnEscape = (event) => { if (event.key === 'Escape') setMobileHistoryOpen(false); };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [mobileHistoryOpen]);

  const loadConversation = async (conversationId) => {
    const requestId = ++activeRequest.current;
    setLoadingConv(true);
    setError('');
    try {
      const response = await assistantService.getConversation(conversationId);
      if (!response.data.success) throw new Error('Could not load this conversation.');
      if (requestId !== activeRequest.current) return;
      const conversation = response.data.data.conversation;
      setActiveConvId(conversation.id);
      setActiveTitle(conversation.title || 'Water Conservation Chat');
      setMessages(conversation.messages || []);
      setMobileHistoryOpen(false);
    } catch {
      if (requestId === activeRequest.current) setError('This conversation could not be loaded. Please try again.');
    } finally {
      if (requestId === activeRequest.current) setLoadingConv(false);
    }
  };

  const startNewConversation = () => {
    activeRequest.current += 1;
    setActiveConvId(null);
    setActiveTitle('New conversation');
    setMessages([]);
    setError('');
    setMobileHistoryOpen(false);
    requestAnimationFrame(() => inputRef.current?.focus());
  };

  const sendMessage = async (event) => {
    event?.preventDefault();
    const text = input.trim();
    if (!text || sending || loadingConv) return;
    setSending(true);
    setError('');
    setInput('');
    setMessages((previous) => [...previous, { role: 'user', message: text }]);
    try {
      const response = await assistantService.chat(text, activeConvId);
      if (!response.data.success) throw new Error('Message could not be sent.');
      const data = response.data.data;
      if (!activeConvId) {
        setActiveConvId(data.conversation_id);
        setActiveTitle(text.length > 40 ? `${text.slice(0, 37)}...` : text);
      }
      setMessages((previous) => [...previous, { role: 'assistant', message: data.message, disclaimer: data.disclaimer, source: data.source }]);
      void fetchConversations();
    } catch (sendError) {
      const message = sendError.response?.data?.error?.message;
      setError(message || 'Your message could not be sent. It is still here so you can retry.');
      setMessages((previous) => previous.slice(0, -1));
      setInput(text);
      requestAnimationFrame(() => inputRef.current?.focus());
    } finally {
      setSending(false);
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <motion.main className="assistant-page" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <header className="page-header assistant-page-header">
        <div><span className="chat-eyebrow">AQUAWISE · CONSERVATION COMPANION</span><h1>Water, made clearer.</h1><p className="subtitle">Explore practical ways to understand and reduce your water use.</p></div>
        <div className="chat-page-links"><Link to="/dashboard">Dashboard <Icon name="arrowRight" size={16} /></Link><Link to="/recommendations">Recommendations <Icon name="arrowRight" size={16} /></Link></div>
      </header>

      <section className="chat-workspace" aria-label="AquaWise assistant">
        <AnimatePresence>
          {mobileHistoryOpen && <motion.button type="button" className="chat-history-backdrop" aria-label="Close conversation history" onClick={() => setMobileHistoryOpen(false)} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />}
        </AnimatePresence>
        <aside className={`chat-sidebar ${mobileHistoryOpen ? 'mobile-open' : ''}`} aria-label="Conversation history">
          <ConversationHistory conversations={conversations} activeId={activeConvId} onSelect={loadConversation} onNew={startNewConversation} loading={loadingHistory} error={historyError} onRetry={fetchConversations} onClose={() => setMobileHistoryOpen(false)} />
        </aside>

        <div className="chat-main">
          <div className="chat-conversation-header">
            <button type="button" className="chat-history-toggle" onClick={() => setMobileHistoryOpen(true)} aria-label="Open conversation history"><Icon name="menu" size={19} /><span>History</span></button>
            <div className="chat-current-title"><span className="chat-status-mark" /><div><span className="chat-current-label">CURRENT CONVERSATION</span><h2>{activeTitle}</h2></div></div>
            <span className="chat-assistant-tag"><Icon name="water" size={15} /> AquaWise</span>
          </div>

          <div className="chat-messages" aria-live="polite" aria-relevant="additions text" aria-busy={loadingConv || sending}>
            {loadingConv ? <div className="chat-loading-state" role="status"><span className="spinner" /><p>Opening conversation…</p></div> : isEmpty ? (
              <div className="chat-empty-state">
                <span className="chat-empty-icon"><Icon name="water" size={27} /></span>
                <span className="chat-section-label">AQUAWISE ASSISTANT</span>
                <h3>What would you like to understand?</h3>
                <p>Ask about everyday conservation. For your measured usage and tailored actions, visit your assessment and recommendations.</p>
                <div className="chat-suggestions">{suggestions.map((suggestion) => <button type="button" key={suggestion} className="chat-suggestion-btn" onClick={() => { setInput(suggestion); inputRef.current?.focus(); }}>{suggestion}<Icon name="arrowRight" size={16} /></button>)}</div>
                <Link className="chat-assessment-link" to="/assessment">View your water assessment <Icon name="arrowRight" size={16} /></Link>
              </div>
            ) : <>{messages.map((message, index) => <Message key={message.id || `${message.role}-${index}`} message={message} />)}{sending && <div className="chat-message assistant"><span className="chat-avatar assistant-avatar"><Icon name="water" size={18} /></span><div className="chat-message-content"><div className="chat-message-label">AquaWise assistant</div><div className="chat-bubble chat-typing"><span>Preparing a response</span><span className="typing-indicator" aria-hidden="true"><i /><i /><i /></span></div></div></div>}</>}
            <div ref={messagesEndRef} />
          </div>

          <AnimatePresence>{error && <motion.div className="chat-error" role="alert" initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 5 }}><Icon name="warning" size={18} /><span>{error}</span>{input.trim() && <button type="button" onClick={sendMessage} disabled={sending}>Retry</button>}</motion.div>}</AnimatePresence>

          <form className="chat-input-area" onSubmit={sendMessage}>
            <label className="chat-composer-label" htmlFor="assistant-message">YOUR MESSAGE</label>
            <div className="chat-composer-row">
              <textarea id="assistant-message" ref={inputRef} className="chat-input" value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendMessage(); } }} placeholder="Ask a question about water conservation…" rows={2} disabled={sending || loadingConv} />
              <button type="submit" className="chat-send-btn" disabled={!input.trim() || sending || loadingConv} aria-label={sending ? 'Sending message' : 'Send message'}>{sending ? <span className="spinner" /> : <Icon name="arrowRight" size={20} />}</button>
            </div>
            <div className="chat-composer-footer"><span>Enter to send <span aria-hidden="true">·</span> Shift + Enter for a new line</span><span>Responses are conversational; see your AquaWise assessment for recorded usage data.</span></div>
          </form>
        </div>
      </section>
    </motion.main>
  );
}

export default Assistant;
