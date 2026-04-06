'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

interface PendingEnterprise {
  id: string;
  company_name: string;
  unified_social_credit_code: string;
  contact: any;
  status: string;
  created_at: string;
}

export default function DashboardPage() {
  const { t } = useLang();
  const [stats, setStats] = useState({
    totalProfiles: 0,
    totalJobs: 0,
    totalEnterprises: 0,
    totalMatches: 0,
    pendingEnterprises: 0,
  });
  const [pendingList, setPendingList] = useState<PendingEnterprise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    async function fetchStats() {
      try {
        // Check API health
        const health = await api.health();
        setApiStatus('connected');
      } catch (err) {
        setApiStatus('disconnected');
      }

      // Fetch data separately to avoid one failure breaking all
      try {
        const profilesRes = await api.profiles.list({ page_size: 1 });
        setStats(prev => ({ ...prev, totalProfiles: profilesRes.total || 0 }));
      } catch (err) {
        console.error('Failed to fetch profiles:', err);
      }

      try {
        const jobsRes = await api.jobs.list({ page_size: 1 });
        setStats(prev => ({ ...prev, totalJobs: jobsRes.total || 0 }));
      } catch (err) {
        console.error('Failed to fetch jobs:', err);
      }

      try {
        const enterprisesRes = await api.enterprises.list();
        const enterprises = enterprisesRes.data || [];
        const pendingCount = enterprises.filter((e: any) => e.status === 'pending').length;
        setStats(prev => ({
          ...prev,
          totalEnterprises: enterprises.length,
          pendingEnterprises: pendingCount,
        }));
        setPendingList(enterprises.filter((e: any) => e.status === 'pending').slice(0, 5));
      } catch (err) {
        console.error('Failed to fetch enterprises:', err);
      }

      setLoading(false);
    }
    fetchStats();
  }, []);

  const handleApprove = async (enterpriseId: string) => {
    try {
      // 调用审核通过 API
      const response = await fetch(`/api/v1/enterprise/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enterprise_id: enterpriseId,
          action: 'approve',
        }),
      });
      const result = await response.json();
      if (result.success) {
        alert(t('dashboard.reviewPassed'));
        // 刷新列表
        window.location.reload();
      } else {
        alert(t('dashboard.operationFailed') + result.message);
      }
    } catch (err) {
      alert(t('dashboard.operationFailedRetry'));
    }
  };

  const handleReject = async (enterpriseId: string) => {
    if (!confirm(t('dashboard.confirmReject'))) return;
    try {
      const response = await fetch(`/api/v1/enterprise/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enterprise_id: enterpriseId,
          action: 'reject',
        }),
      });
      const result = await response.json();
      if (result.success) {
        alert(t('dashboard.rejected'));
        window.location.reload();
      } else {
        alert(t('dashboard.operationFailed') + result.message);
      }
    } catch (err) {
      alert(t('dashboard.operationFailedRetry'));
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
        <div className="text-gray-500">{t('common.loading')}</div>
      </div>
    );
  }

  const statCards = [
    { title: t('dashboard.totalJobSeekers'), value: stats.totalProfiles, icon: '👤', color: 'bg-blue-500' },
    { title: t('dashboard.totalJobs'), value: stats.totalJobs, icon: '💼', color: 'bg-green-500' },
    { title: t('dashboard.totalEnterprises'), value: stats.totalEnterprises, icon: '🏢', color: 'bg-purple-500' },
    { title: t('dashboard.pendingEnterprises'), value: stats.pendingEnterprises, icon: '⏳', color: 'bg-orange-500' },
  ];

  return (
    <div>
      <Header title={t('dashboard.adminDashboard')} description={t('dashboard.welcomeAdmin')} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((card) => (
          <div key={card.title} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`${card.color} p-3 rounded-lg mr-4`}>
                <span className="text-2xl">{card.icon}</span>
              </div>
              <div>
                <p className="text-sm text-gray-500">{card.title}</p>
                <p className="text-2xl font-bold text-gray-900">{card.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 待审核企业 */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">{t('dashboard.pendingEnterprises')}</h2>
            <a href="/dashboard/enterprises" className="text-sm text-blue-600 hover:underline">
              {t('dashboard.viewAll')}
            </a>
          </div>

          {pendingList.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <span className="text-4xl mb-2 block">✅</span>
              <p>{t('dashboard.noPending')}</p>
            </div>
          ) : (
            <div className="space-y-4">
              {pendingList.map((enterprise) => (
                <div key={enterprise.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-medium text-gray-900">{enterprise.company_name}</h3>
                      <p className="text-sm text-gray-500">{enterprise.unified_social_credit_code}</p>
                    </div>
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded">
                      {t('dashboard.pendingReview')}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 mb-3">
                    <p>{t('dashboard.contact')}{enterprise.contact?.name}</p>
                    <p>{t('dashboard.phone')}{enterprise.contact?.phone}</p>
                    <p>{t('dashboard.email')}{enterprise.contact?.email}</p>
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => handleReject(enterprise.id)}
                      className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
                    >
                      {t('dashboard.reject')}
                    </button>
                    <button
                      onClick={() => handleApprove(enterprise.id)}
                      className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      {t('dashboard.approve')}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 快捷操作 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.quickActions')}</h2>
          <div className="space-y-3">
            <a href="/job-seekers" className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <span className="font-medium text-blue-600">{t('dashboard.manageJobSeekers')}</span>
              <p className="text-sm text-gray-500 mt-1">{t('dashboard.manageJobSeekersDesc')}</p>
            </a>
            <a href="/jobs" className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <span className="font-medium text-blue-600">{t('dashboard.manageJobs')}</span>
              <p className="text-sm text-gray-500 mt-1">{t('dashboard.manageJobsDesc')}</p>
            </a>
            <a href="/dashboard/enterprises" className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <span className="font-medium text-blue-600">{t('dashboard.manageEnterprises')}</span>
              <p className="text-sm text-gray-500 mt-1">{t('dashboard.manageEnterprisesDesc')}</p>
            </a>
          </div>
        </div>
      </div>

      {/* 系统信息 */}
      <div className="bg-white rounded-lg shadow p-6 mt-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('dashboard.systemInfo')}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-gray-600">{t('dashboard.systemVersion')}</span>
            <span className="text-gray-900 font-medium">1.0.0</span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-gray-600">{t('dashboard.apiStatus')}</span>
            <span className={`font-medium ${apiStatus === 'connected' ? 'text-green-600' : 'text-red-600'}`}>
              {apiStatus === 'connected' ? t('dashboard.connected') : t('dashboard.disconnected')}
            </span>
          </div>
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-gray-600">{t('dashboard.database')}</span>
            <span className={apiStatus === 'connected' ? 'text-green-600 font-medium' : 'text-gray-400 font-medium'}>
              {apiStatus === 'connected' ? t('dashboard.normal') : t('dashboard.disconnected')}
            </span>
          </div>
          <div className="flex justify-between items-center py-2">
            <span className="text-gray-600">{t('dashboard.lastUpdated')}</span>
            <span className="text-gray-900 font-medium">{new Date().toLocaleDateString('zh-CN')}</span>
          </div>
        </div>
      </div>
    </div>
  );
}