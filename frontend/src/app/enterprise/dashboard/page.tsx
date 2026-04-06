'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import Header from '@/components/Header';
import Button from '@/components/Button';
import { useLang } from '@/lib/i18n';

export default function EnterpriseDashboardPage() {
  const { t } = useLang();
  const [enterprise, setEnterprise] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showGuide, setShowGuide] = useState(false);

  useEffect(() => {
    const savedEnterprise = localStorage.getItem('enterprise');
    if (savedEnterprise) {
      const ent = JSON.parse(savedEnterprise);
      setEnterprise(ent);
      if (ent.status === 'approved' && ent.api_key) {
        setShowGuide(true);
      }
    }
    setLoading(false);
  }, []);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert(t('edash.copied'));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">{t('common.loading')}</div>
      </div>
    );
  }

  if (!enterprise) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow p-8 text-center max-w-md">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">🏢</span>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">{t('edash.loginFirst')}</h2>
          <p className="text-gray-600 mb-6">{t('edash.loginFirstDesc')}</p>
          <Link href="/enterprise/login">
            <Button variant="primary">{t('edash.loginButton')}</Button>
          </Link>
        </div>
      </div>
    );
  }

  if (enterprise.status === 'pending') {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header title={t('edash.title')} description={t('edash.welcome')} />
        <div className="max-w-4xl mx-auto px-4 py-12">
          <div className="bg-white rounded-xl shadow p-8 text-center">
            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">⏳</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('edash.awaitingReview')}</h2>
            <p className="text-gray-600 mb-6">
              {t('edash.reviewPending')}
              {t('edash.reviewResultEmail')}
            </p>
            <p className="text-sm text-gray-500">
              {t('edash.enterpriseName')}{enterprise.company_name}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (showGuide || enterprise.status === 'approved') {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header title={t('edash.title')} description={t('edash.welcome')} />

        <div className="max-w-6xl mx-auto px-4 py-8">
          {/* Welcome card */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 mb-8 text-white">
            <h2 className="text-2xl font-bold mb-2">{t('edash.welcomeBack')}{enterprise.company_name}！</h2>
            <p className="opacity-90">{t('edash.verifiedDesc')}</p>
          </div>

          {/* Quick start guide */}
          <div className="bg-white rounded-xl shadow p-6 mb-8">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-900">{t('edash.quickStart')}</h3>
              <button
                onClick={() => setShowGuide(!showGuide)}
                className="text-sm text-blue-600 hover:underline"
              >
                {showGuide ? t('edash.collapse') : t('edash.expand')}
              </button>
            </div>

            {showGuide && (
              <div className="space-y-6">
                <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
                  <p className="font-semibold text-blue-800 mb-2">{t('edash.step1')}</p>
                  <p className="text-blue-700 text-sm mb-3">
                    {t('edash.step1Desc')}
                  </p>
                  <div className="bg-gray-900 rounded-lg p-4 relative">
                    <pre className="text-sm text-gray-300 overflow-x-auto">{`${t('edash.agentPrompt')}

1. ${t('edash.agentPromptLine1')}
2. ${t('edash.agentPromptLine2')}
   - ${t('edash.enterpriseId')} ${enterprise.id || 'ent_xxx'}
   - ${t('edash.apiKey')} ${enterprise.api_key || 'ah_live_xxx...'}
3. ${t('edash.agentPromptLine3')}
4. ${t('edash.agentPromptLine4')}
5. ${t('edash.agentPromptLine5')}`}</pre>
                    <button
                      onClick={() => copyToClipboard(`${t('edash.agentPrompt')}

1. ${t('edash.agentPromptLine1')}
2. ${t('edash.agentPromptLine2')}
   - ${t('edash.enterpriseId')} ${enterprise.id || 'ent_xxx'}
   - ${t('edash.apiKey')} ${enterprise.api_key || 'ah_live_xxx...'}
3. ${t('edash.agentPromptLine3')}
4. ${t('edash.agentPromptLine4')}
5. ${t('edash.agentPromptLine5')}`)}
                      className="absolute top-2 right-2 bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700"
                    >
                      {t('edash.copyInstructions')}
                    </button>
                  </div>
                </div>

                <div className="grid md:grid-cols-3 gap-4">
                  <div className="border rounded-lg p-4">
                    <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mb-3">
                      <span className="text-xl">📋</span>
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-1">{t('edash.postJobs')}</h4>
                    <p className="text-sm text-gray-600">{t('edash.postJobsDesc')}</p>
                  </div>
                  <div className="border rounded-lg p-4">
                    <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mb-3">
                      <span className="text-xl">🤖</span>
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-1">{t('edash.agentWorking')}</h4>
                    <p className="text-sm text-gray-600">{t('edash.agentWorkingDesc')}</p>
                  </div>
                  <div className="border rounded-lg p-4">
                    <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center mb-3">
                      <span className="text-xl">💼</span>
                    </div>
                    <h4 className="font-semibold text-gray-900 mb-1">{t('edash.handleMatches')}</h4>
                    <p className="text-sm text-gray-600">{t('edash.handleMatchesDesc')}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Quick actions */}
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow p-6">
              <h3 className="font-bold text-gray-900 mb-4">{t('edash.myRecruitment')}</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{t('edash.seniorGoEngineer')}</p>
                    <p className="text-sm text-gray-500">{t('edash.receivedMatches1')}</p>
                  </div>
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">{t('edash.recruiting')}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{t('edash.frontendEngineer')}</p>
                    <p className="text-sm text-gray-500">{t('edash.receivedMatches2')}</p>
                  </div>
                  <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">{t('edash.recruiting')}</span>
                </div>
              </div>
              <Button variant="secondary" className="w-full mt-4">
                {t('edash.viewAllJobs')}
              </Button>
            </div>

            <div className="bg-white rounded-xl shadow p-6">
              <h3 className="font-bold text-gray-900 mb-4">{t('edash.recentMatches')}</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{t('edash.zhangsan')}</p>
                    <p className="text-sm text-gray-500">{t('edash.matchGo')}</p>
                  </div>
                  <Button variant="secondary">{t('common.view')}</Button>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{t('edash.lisi')}</p>
                    <p className="text-sm text-gray-500">{t('edash.matchFrontend')}</p>
                  </div>
                  <Button variant="secondary">{t('common.view')}</Button>
                </div>
              </div>
              <Button variant="secondary" className="w-full mt-4">
                {t('edash.viewAllMatches')}
              </Button>
            </div>

            <div className="bg-white rounded-xl shadow p-6">
              <h3 className="font-bold text-gray-900 mb-4">{t('edash.billingCenter')}</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{t('edash.monthlySpending')}</p>
                    <p className="text-sm text-gray-500">{t('edash.viewBillingDetail')}</p>
                  </div>
                  <span className="text-lg font-bold text-gray-900">¥0.00</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{t('edash.apiCalls')}</p>
                    <p className="text-sm text-gray-500">{t('edash.zeroQueries')}</p>
                  </div>
                </div>
              </div>
              <Link href="/enterprise/dashboard/billing">
                <Button variant="secondary" className="w-full mt-4">
                  {t('edash.viewBilling')}
                </Button>
              </Link>
            </div>
          </div>

          {/* API info */}
          <div className="bg-white rounded-xl shadow p-6">
            <h3 className="font-bold text-gray-900 mb-4">{t('edash.apiCredentials')}</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">{t('edash.enterpriseIdLabel')}</span>
                <code className="bg-gray-100 px-3 py-1 rounded text-sm">{enterprise.id || 'ent_xxx'}</code>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">{t('edash.apiKeyLabel')}</span>
                <div className="flex items-center gap-2">
                  <code className="bg-gray-100 px-3 py-1 rounded text-sm">
                    {enterprise.api_key ? enterprise.api_key.slice(0, 12) + '...' : 'ah_live_xxx...'}
                  </code>
                  <button
                    onClick={() => enterprise.api_key && copyToClipboard(enterprise.api_key)}
                    className="text-blue-600 hover:underline text-sm"
                  >
                    {t('common.copy')}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title={t('edash.title')} description={t('edash.welcome')} />
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-white rounded-xl shadow p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">❌</span>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">{t('edash.reviewNotPassed')}</h2>
          <p className="text-gray-600 mb-6">{t('edash.reviewNotPassedDesc')}</p>
          <Link href="/">
            <Button variant="secondary">{t('edash.backToHome')}</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
