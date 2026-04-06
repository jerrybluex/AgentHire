'use client';

import { usePathname } from 'next/navigation';
import Sidebar from './Sidebar';

export default function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Public pages without sidebar (no authentication required)
  const publicPages = [
    '/',
    '/enterprise/login',
    '/enterprise/register',
  ];

  const isPublicPage = publicPages.some(page => pathname === page);

  if (isPublicPage) {
    return <>{children}</>;
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        {children}
      </main>
    </div>
  );
}