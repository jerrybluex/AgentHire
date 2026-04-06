'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLang } from '@/lib/i18n';

export default function Sidebar() {
  const pathname = usePathname();
  const { t, lang, setLang } = useLang();

  const menuItems = [
    { href: '/dashboard', label: t('nav.dashboard'), icon: '━' },
    { href: '/job-seekers', label: t('nav.agents'), icon: '◈' },
    { href: '/jobs', label: t('nav.jobs'), icon: '◇' },
    { href: '/enterprise', label: t('nav.enterprise'), icon: '▣' },
    { href: '/marketplace', label: t('nav.market'), icon: '⬡' },
    { href: '/marketplace/templates', label: t('nav.templates'), icon: '▤' },
  ];

  return (
    <aside className="w-56 bg-black border-r border-white/10 min-h-screen flex flex-col">
      <div className="p-5 border-b border-white/10">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-7 h-7 border border-white/30 flex items-center justify-center">
            <span className="text-white font-bold text-xs font-mono">AH</span>
          </div>
          <span className="text-xs font-mono tracking-[0.15em] text-white/70 uppercase">AgentHire</span>
        </Link>
        <p className="text-[10px] font-mono text-white/20 tracking-widest uppercase mt-2">{t('nav.adminConsole')}</p>
      </div>

      <div className="px-3 py-3 border-b border-white/5">
        <a
          href="/"
          target="_blank"
          className="flex items-center gap-2 px-3 py-2 text-[10px] font-mono tracking-widest uppercase text-white/30 hover:text-white/60 transition-colors"
        >
          <span>↗</span>
          <span>{t('nav.viewSite')}</span>
        </a>
      </div>

      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-0.5">
          {menuItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2.5 text-xs font-mono tracking-wider uppercase transition-all duration-150 ${
                    isActive
                      ? 'text-white bg-white/5 border-l-2 border-white'
                      : 'text-white/30 hover:text-white/60 border-l-2 border-transparent'
                  }`}
                >
                  <span className="text-[10px] opacity-50">{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-white/5">
        <button
          onClick={() => setLang(lang === 'zh' ? 'en' : 'zh')}
          className="w-full px-3 py-1.5 text-[10px] font-mono tracking-wider text-white/30 hover:text-white border border-white/10 hover:border-white/30 transition-colors mb-3"
        >
          {lang === 'zh' ? 'EN' : '中'}
        </button>
        <div className="text-[10px] font-mono text-white/15 tracking-widest uppercase">
          v0.1.0
        </div>
      </div>
    </aside>
  );
}
