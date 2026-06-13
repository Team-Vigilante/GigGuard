import { useState, useRef, useEffect } from 'react';
import './App.css';

const INITIAL_MESSAGE = {
  role: 'assistant',
  content: 'Namaste! I am GigGuard, your free legal advocate.\nTell me what happened — which platform did you work for, and what went wrong?'
};

const SYSTEM_PROMPT = {
  role: "system",
  content: `You are GigGuard, an AI legal advocate for gig workers in India. When a worker describes their grievance:
1. Ask clarifying questions to understand: platform name, event type, date, amount affected, notice given or not
2. Once you have enough info, provide:
   - Summary of what happened
   - Indian labour laws that were violated
   - Formal grievance letter draft in English
   - Key demands the worker should make
3. Be empathetic, use simple language
4. End every response with:
   "Reply DONE when you want to generate your grievance PDF"
5. When user replies DONE, respond with exactly the word:
   GENERATE_PDF
and absolutely nothing else.`
};

function App() {
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [pdfError, setPdfError] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, isGeneratingPdf, pdfUrl, errorMsg, pdfError]);

  const handleInput = (e) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 100)}px`;
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const resetChat = () => {
    setMessages([INITIAL_MESSAGE]);
    setPdfUrl(null);
    setIsGeneratingPdf(false);
    setPdfError(null);
    setErrorMsg(null);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const generatePdfFromBackend = async (chatHistory) => {
    setIsGeneratingPdf(true);
    setPdfError(null);
    try {
      const response = await fetch("http://localhost:8000/api/extract-and-generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: chatHistory
        })
      });

      if (!response.ok) {
        const errText = await response.text();
        console.error("Backend PDF Generation Error:", errText);
        throw new Error(`Backend error: ${response.status}`);
      }

      const data = await response.json();
      setPdfUrl(`http://localhost:8000${data.pdf_url}`);
    } catch (err) {
      console.error(err);
      setPdfError("PDF generation failed. Please try again.");
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input.trim() };
    const newMessages = [...messages, userMessage];
    
    setMessages(newMessages);
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    setIsLoading(true);
    setErrorMsg(null);
    setPdfError(null);

    try {
      const apiMessages = [SYSTEM_PROMPT, ...newMessages].map(m => ({
        role: m.role,
        content: m.content
      }));
      
      const requestBody = {
        model: "llama-3.3-70b-versatile",
        messages: apiMessages,
        max_tokens: 1000,
        temperature: 0.7
      };
      
      const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${import.meta.env.VITE_GROQ_API_KEY}`
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.log("Groq error response:", errorText);
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      const botReply = data.choices[0].message.content.trim();

      const updatedMessages = [...newMessages, { role: 'assistant', content: botReply }];
      setMessages(updatedMessages);

      if (botReply === 'GENERATE_PDF') {
        // Exclude system prompt when sending history to our backend
        const userAndBotMessages = updatedMessages.map(m => ({
          role: m.role,
          content: m.content
        }));
        await generatePdfFromBackend(userAndBotMessages);
      }

    } catch (err) {
      console.error(err);
      setErrorMsg("Sorry, something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-app">
      <header className="header">
        <div className="header-left">
          <h1>⚖ GigGuard</h1>
          <span className="subtitle">Legal Advocate</span>
        </div>
        <a href="http://localhost:8000/dashboard/index.html" target="_blank" rel="noreferrer" className="dashboard-link">
          View Dashboard →
        </a>
      </header>

      <main className="chat-container">
        <div className="message-list">
          {messages.map((msg, idx) => {
            if (msg.content === 'GENERATE_PDF') return null;
            
            return (
              <div key={idx} className={`message-wrapper ${msg.role}`}>
                {msg.role === 'assistant' && (
                  <div className="avatar">GG</div>
                )}
                <div className={`message-bubble ${msg.role}`}>
                  {msg.content.split('\n').map((line, i) => (
                    <span key={i}>
                      {line}
                      <br />
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
          
          {isLoading && (
            <div className="message-wrapper assistant">
              <div className="avatar">GG</div>
              <div className="message-bubble assistant typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          
          {errorMsg && (
            <div className="error-message">{errorMsg}</div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </main>

      <div className="input-area">
        {isGeneratingPdf && (
          <div className="pdf-banner loading">
            <div className="spinner"></div>
            <p>Generating your grievance letter...</p>
          </div>
        )}
        
        {pdfError && (
          <div className="pdf-banner error">
            <p style={{ color: '#d32f2f' }}>{pdfError}</p>
          </div>
        )}

        {pdfUrl && !isGeneratingPdf && (
          <div className="pdf-banner">
            <p>Your grievance letter is ready!</p>
            <a href={pdfUrl} target="_blank" rel="noreferrer" className="btn-download">
              Download Grievance Letter (PDF)
            </a>
          </div>
        )}

        <div className="input-controls">
          <button className="btn-new-case" onClick={resetChat}>New Case</button>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            rows={1}
          />
          <button className="btn-send" onClick={handleSend} disabled={isLoading || isGeneratingPdf || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
