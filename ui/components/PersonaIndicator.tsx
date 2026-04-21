'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';

interface PersonaIndicatorProps {
  persona: 'samara' | 'artery';
  active: boolean;
}

export default function PersonaIndicator({ persona, active }: PersonaIndicatorProps) {
  return (
    <motion.div
      animate={active ? { scale: [1, 1.05, 1] } : {}}
      transition={{ duration: 2, repeat: Infinity }}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${
        active ? 'border-white/30 bg-white/10' : 'border-white/10 bg-white/5'
      }`}
    >
      {persona === 'samara' ? (
        <div className="w-4 h-4 bg-samara-warm/80 animate-blob"></div>
      ) : (
        <div className="w-4 h-4 border border-artery-green bg-artery-green/20 animate-pulse rounded-sm"></div>
      )}
      <span className={`text-xs font-mono ${active ? 'text-white' : 'text-white/40'}`}>
        {persona === 'samara' ? 'Samara' : 'Artery'}
      </span>
    </motion.div>
  );
}
