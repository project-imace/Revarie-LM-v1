'use client';

import { motion } from 'framer-motion';

interface ChatBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  persona?: 'samara' | 'artery';
}

export default function ChatBubble({ role, content, persona = 'samara' }: ChatBubbleProps) {
  const isUser = role === 'user';
  const isArtery = persona === 'artery';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div
        className={
          isUser
            ? 'bg-white/10 text-white rounded-2xl px-5 py-3 max-w-[80%] font-body'
            : isArtery
            ? 'bg-black border border-artery-green/30 text-artery-green rounded-none px-5 py-3 max-w-[80%] font-artery terminal-prompt'
            : 'chat-bubble-samara font-samara'
        }
      >
        {content}
      </div>
    </motion.div>
  );
}
