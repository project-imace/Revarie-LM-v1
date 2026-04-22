'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';
import { Terminal as TerminalIcon, Send } from 'lucide-react';
import ChatBubble from '@/components/ChatBubble';
import Terminal from '@/components/Terminal';

export default function ArteryPage() {
  const [messages, setMessages] = useState<Array<{role: string; content: string}>>([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { 
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); 
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsProcessing(true);

    setTimeout(() => {
      const assistantMessage = { role: 'assistant', content: `> Query processed. Response: Input acknowledged.` };
      setMessages(prev => [...prev, assistantMessage]);
      setIsProcessing(false);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-screen bg-black bg-artery-grid relative overflow-hidden">
      <div className="scan-line pointer-events-none z-50"></div>
      
      {/* Terminal Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-artery-green/30 bg-black">
        <div className="flex items-center gap-3">
          <TerminalIcon className="w-5 h-5 text-artery-green" />
          <div className="font-artery font-bold text-xl tracking-widest">[ARTERY_CORE]</div>
          <span className="font-artery text-artery-green/60 text-sm ml-2">v1.0</span>
        </div>
        <div className="font-artery text-artery-green/40 text-xs">SESSION: {new Date().toISOString().slice(0, 10)}</div>
      </header>

      {/* Terminal Output Area */}
      <div className="flex-1 overflow-y-auto p-4 font-artery text-sm custom-scrollbar bg-black">
        <Terminal />
        <AnimatePresence>
          {messages.map((msg, idx) => (
            <motion.div key={idx} initial={{ opacity: 0, x: -5 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }}>
              <ChatBubble role={msg.role as 'user' | 'assistant'} content={msg.content} persona="artery" />
            </motion.div>
          ))}
        </AnimatePresence>
        
        {isProcessing && (
          <div className="font-artery text-artery-green/60 animate-pulse">
            <span className="terminal-prompt">PROCESSING</span>
            <span className="inline-block w-2 h-4 bg-artery-green ml-1 animate-terminal-blink" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Line */}
      <div className="p-4 border-t border-artery-green/30 bg-black">
        <div className="flex gap-2 max-w-4xl mx-auto items-center">
          <span className="font-artery text-artery-green">{'>'}</span>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="ENTER COMMAND..."
            className="flex-1 bg-transparent border-none text-artery-green font-artery placeholder:text-artery-green/30 focus:outline-none"
          />
          <button 
            onClick={handleSend} 
            disabled={!input.trim()} 
            aria-label="Send" 
            className="text-artery-green/60 hover:text-artery-green disabled:opacity-50 transition-opacity"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
