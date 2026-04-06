'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useLang } from '@/lib/i18n';

interface MobileNavProps {
  items?: Array<{ href: string; label: string }>;
}

export default function MobileNav({ items }: MobileNavProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { t, lang, setLang } = useLang();

  const defaultItems = [
    { href: '#how-it-works', label: t('landing.protocol') },
    { href: '#job-seekers', label: t('landing.forSeekers') },
    { href: '#enterprises', label: t('landing.forEnterprises') },
    { href: '#features', label: t('landing.capabilities_title') },
    { href: '/skill', label: 'Docs' },
  ];

  const navItems = items || defaultItems;

  return (
    <>
      {/* Mobile Header */}
      <header className="lg:hidden bg-black/80 backdrop-blur-sm border-b border-white/10">
        <div className="px-4 py-3 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-7 h-7 border border-white/40 flex items-center justify-center">
              <span className="text-white font-bold text-xs font-mono">AH</span>
            </div>
            <span className="text-sm font-mono tracking-widest text-white/80 uppercase">AgentHire</span>
          </Link>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setLang(lang === 'zh' ? 'en' : 'zh')}
              className="px-2 py-1 text-[10px] font-mono tracking-wider text-white/40 hover:text-white border border-white/10 hover:border-white/30 transition-colors"
            >
              {lang === 'zh' ? 'EN' : '中'}
            </button>
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 text-white/60 hover:text-white transition-colors"
              aria-label="Menu"
            >
              {isOpen ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isOpen && (
          <nav className="px-4 pb-4 border-t border-white/5">
            <ul className="space-y-1 mt-2">
              {navItems.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setIsOpen(false)}
                    className="block px-3 py-2.5 text-white/50 hover:text-white text-xs font-mono tracking-widest uppercase transition-colors"
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        )}
      </header>

      {/* Desktop Header */}
      <header className="hidden lg:block fixed top-0 left-0 right-0 z-50 bg-black/60 backdrop-blur-md border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-8 h-8 border border-white/30 flex items-center justify-center">
              <span className="text-white font-bold text-xs font-mono">AH</span>
            </div>
            <span className="text-sm font-mono tracking-[0.2em] text-white/70 uppercase">AgentHire</span>
          </Link>
          <nav className="flex items-center gap-8">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="text-white/40 hover:text-white text-xs font-mono tracking-widest uppercase transition-colors duration-200"
              >
                {item.label}
              </a>
            ))}
            <button
              onClick={() => setLang(lang === 'zh' ? 'en' : 'zh')}
              className="px-2.5 py-1 text-[10px] font-mono tracking-wider text-white/40 hover:text-white border border-white/10 hover:border-white/30 transition-colors"
            >
              {lang === 'zh' ? 'EN' : '中'}
            </button>
          </nav>
        </div>
      </header>
    </>
  );
}
