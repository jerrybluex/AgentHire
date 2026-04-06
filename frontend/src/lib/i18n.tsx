'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import zh from '@/i18n/zh';
import en from '@/i18n/en';

type Lang = 'zh' | 'en';

interface LangContextType {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string) => string;
}

const LangContext = createContext<LangContextType>({
  lang: 'zh',
  setLang: () => {},
  t: (key) => key,
});

const translations: Record<Lang, Record<string, string>> = { zh, en };

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
}

function setCookie(name: string, value: string) {
  const maxAge = 365 * 24 * 60 * 60; // 1 year
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAge}; SameSite=Lax`;
}

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>('zh');

  useEffect(() => {
    const saved = getCookie('agenthire_lang');
    if (saved === 'en' || saved === 'zh') {
      setLangState(saved);
    }
  }, []);

  const setLang = useCallback((newLang: Lang) => {
    setLangState(newLang);
    setCookie('agenthire_lang', newLang);
    document.documentElement.lang = newLang === 'zh' ? 'zh-CN' : 'en';
  }, []);

  const t = useCallback(
    (key: string): string => {
      return translations[lang][key] || translations['zh'][key] || key;
    },
    [lang]
  );

  return (
    <LangContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
