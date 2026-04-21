'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import Image from 'next/image';
import { useState } from 'react';

export default function LMv1LandingPage() {
  const [videoLoaded, setVideoLoaded] = useState(false);

  return (
    <main className="min-h-screen bg-background text-white overflow-x-hidden">
      {/* Header */}
      <header className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur border-b border-white/10 h-14 flex items-center px-6">
        <Link href="/" className="flex items-center gap-3">
          <Image src="https://assets.imace.online/image/imace.svg" alt="IMACE" width={80} height={24} className="h-6 w-auto" />
        </Link>
        <nav className="ml-auto flex gap-6">
          <a href="https://github.com/project-imace" target="_blank" className="text-white/60 hover:text-white transition">GitHub</a>
          <a href="mailto:reach@imace.online" className="text-white/60 hover:text-white transition">Contact</a>
        </nav>
      </header>

      {/* Hero */}
      <section className="pt-24 px-6 max-w-4xl mx-auto text-center">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <h1 className="font-logo text-6xl md:text-7xl mb-4 tracking-tight">
            Revarie LM v1.0
          </h1>
          <p className="font-mono text-sm text-white/60 mb-8">
            Research on the Empirical Values of Anthropomorphic Reflections in Intelligence Emulation via Language Models version 1.0
          </p>
        </motion.div>

        {/* CTA Button */}
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }} className="mb-12">
          <Link href="https://research.imace.online/revarie1" className="inline-flex items-center gap-3 px-8 py-4 bg-white/5 backdrop-blur border border-white/20 rounded-2xl hover:bg-white/10 hover:border-white/30 transition-all">
            <span className="font-body text-lg">Explore the Model</span>
          </Link>
          <p className="text-xs text-white/40 mt-3 font-mono">Revarie LM v1 currently available only through Research study, public opening soon</p>
        </motion.div>
      </section>

      {/* Description */}
      <motion.section initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="px-6 py-8 max-w-3xl mx-auto">
        <div className="font-body text-white/70 space-y-4 leading-relaxed">
          <p>Revarie LM v1 is the first flagship experimental implementation of the Revarie framework. It is designed as a language‑model‑based cognitive emulation prototype. The model explores whether structured reasoning, belief handling, and memory can improve interpretive coherence.</p>
          <p>Its goal is not artificial general intelligence, but comparative research. The system contrasts baseline LLM behavior with more structured cognitive and psychological layering.</p>
        </div>
      </motion.section>

      {/* Dual Persona Comparison */}
      <motion.section initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="px-6 py-12 max-w-4xl mx-auto">
        <h3 className="font-mono text-xl text-white/80 mb-6 text-center">Dual Persona Comparison</h3>
        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-surface/50 backdrop-blur border border-white/10 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Image src="https://assets.imace.online/image/samaraicon.svg" alt="Samara" width={32} height={32} className="w-8 h-8" />
              <span className="font-logo text-2xl text-samara-warm">Samara</span>
            </div>
            <ul className="font-body text-white/60 space-y-2 text-sm">
              <li>• High Anthropomorphic Reflection</li>
              <li>• Integrated Synergistic Logic</li>
              <li>• Vector‑Episodic (Emotional & Contextual)</li>
              <li>• Warm, Empathetic, Relational</li>
            </ul>
          </div>
          <div className="bg-surface/50 backdrop-blur border border-white/10 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Image src="https://assets.imace.online/image/arteryicon.svg" alt="Artery" width={32} height={32} className="w-8 h-8" />
              <span className="font-logo text-2xl text-artery-green">Artery 1.0</span>
            </div>
            <ul className="font-body text-white/60 space-y-2 text-sm">
              <li>• Low Anthropomorphic Reflection</li>
              <li>• Restricted Functional Logic</li>
              <li>• Vector‑Episodic (Factual & Transactional)</li>
              <li>• Precise, Neutral, Efficient</li>
            </ul>
          </div>
        </div>
      </motion.section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8 px-6 mt-12">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="font-mono text-xs text-white/40">© 2026 Project IMACE</div>
          <div className="flex gap-6">
            <Image src="https://assets.imace.online/image/alternresearch.svg" alt="Altern Research" width={100} height={20} className="h-5 w-auto opacity-50" />
            <Image src="https://assets.imace.online/image/arcbmm.svg" alt="ARC BMM" width={80} height={20} className="h-5 w-auto opacity-50" />
            <Image src="https://assets.imace.online/image/arcami.svg" alt="Arcami" width={80} height={20} className="h-5 w-auto opacity-50" />
          </div>
        </div>
      </footer>
    </main>
  );
}
