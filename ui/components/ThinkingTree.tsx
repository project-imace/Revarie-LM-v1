'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Brain } from 'lucide-react';

interface ThinkingTreeProps {
  steps: string[];
}

export default function ThinkingTree({ steps }: ThinkingTreeProps) {
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        exit={{ opacity: 0, height: 0 }}
        className="mb-3 ml-12"
      >
        <div className="flex items-center gap-2 text-white/40 text-xs font-mono mb-2">
          <Brain className="w-3 h-3" />
          <span>Thinking...</span>
        </div>
        <div className="space-y-1">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.3 }}
              className="text-white/30 text-xs font-mono"
            >
              <span className="text-samara-warm mr-2">→</span>
              {step}
            </motion.div>
          ))}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
