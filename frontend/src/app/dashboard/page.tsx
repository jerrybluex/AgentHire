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

// 带超时的fetch函数
const fetchWithTimeout = async <T,>(
  promise: Promise<T>,
  timeout = 5000,
  name = 'API'
): Promise<T> => {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error(`${name} 请求超时`)), timeout)
    ),
  ]);
};

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
  const [loadingStatus, setLoadingStatus] = useState<string>('正在连接服务器...');
  const [error, setError] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected'>('disconnected');
  const [apiErrors, setApiErrors] = useState<string[]>([]);

  useEffect(() => {
    async function fetchStats() {
      const errors: string[] = [];

      try {
        // Step 1: 检查API健康（3秒超时）
        setLoadingStatus('正在检查API服务...');
        try {
          await fetchWithTimeout(api.health(), 3000, 'Health Check');
          setApiStatus('connected');
        } catch (err) {
          console.warn('Health check failed:', err);
          setApiStatus('disconnected');
          errors.push('API服务连接失败');
        }

        // Step 2: 并行发起所有数据请求（5秒超时）
        setLoadingStatus('正在加载统计数据...');

        const [profilesResult, jobsResult, enterprisesResult] = await Promise.allSettled([
          fetchWithTimeout(
            api.profiles.list({ page_size: 1 }),
            5000,
            'Profiles'
          ).catch(err => {
            console.error('Profiles API error:', err);
            errors.push('求职者数据加载失败');
            return { total: 0 };
          }),

          fetchWithTimeout(
            api.jobs.list({ page_size: 1 }),
            5000,
            'Jobs'
          ).catch(err => {
            console.error('Jobs API error:', err);
            errors.push('职位数据加载失败');
            return { total: 0 };
          }),

          fetchWithTimeout(
            api.enterprises.list(),
            5000,
            'Enterprises'
          ).catch(err => {
            console.error('Enterprises API error:', err);
            errors.push('企业数据加载失败');
            return { data: [], total: 0 };
          }),
        ]);

        // 处理结果
        if (profilesResult.status === 'fulfilled') {
          setStats(prev => ({ ...prev, totalProfiles: profilesResult.value.total || 0 }));
        }

        if (jobsResult.status === 'fulfilled') {
          setStats(prev => ({ ...prev, totalJobs: jobsResult.value.total || 0 }));
        }

        if (enterprisesResult.status === 'fulfilled') {
          const enterprises = enterprisesResult.value.data || [];
          const pendingCount = enterprises.filter((e: any) => e.status === 'pending').length;
          setStats(prev => ({
            ...prev,
            totalEnterprises: enterprises.length,
            pendingEnterprises: pendingCount,
          }));
          setPendingList(enterprises.filter((e: any) => e.status === 'pending').slice(0, 5));
        }

        // 记录所有错误
        if (errors.length > 0) {
          setApiErrors(errors);
          setError(`部分数据加载失败: ${errors.join(', ')}`);
        }

      } catch (err) {
        console.error('Dashboard fetch error:', err);
        setError('数据加载失败，请检查网络连接或刷新页面重试');
      } finally {
        setLoading(false);
        setLoadingStatus('');
      }
    }

    fetchStats();
  }, []);

  const handleApprove = async (enterpriseId: string) => {
    try {
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

  // 重新加载数据
  const handleRetry = () => {
    window.location.reload();
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-4"></div>
        <div className="text-gray-600 font-medium">{t('common.loading')}</div>
        <div className="text-gray-400 text-sm mt-2">{loadingStatus}</div>
        <div className="text-gray-400 text-xs mt-4">如果长时间无响应，请检查网络连接</div>
      </div>
    );
  }

  // 如果有错误，显示错误提示但不阻止内容显示
  const statCards = [
    { title: t('dashboard.totalJobSeekers'), value: stats.totalProfiles, icon: '👤', color: 'bg-blue-500' },
    { title: t('dashboard.totalJobs'), value: stats.totalJobs, icon: '💼', color: 'bg-green-500' },
    { title: t('dashboard.totalEnterprises'), value: stats.totalEnterprises, icon: '🏢', color: 'bg-purple-500' },
    { title: t('dashboard.pendingEnterprises'), value: stats.pendingEnterprises, icon: '⏳', color: 'bg-orange-500' },
  ];

  return (
    <div>
      <Header title={t('dashboard.adminDashboard')} description={t('dashboard.welcomeAdmin')} />

      {/* 错误提示 */}
      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <div className="text-yellow-600 mr-3">⚠️</div>
            <div className="flex-1">
              <div className="text-yellow-800 font-medium">{error}</div>
              <div className="text-yellow-600 text-sm mt-1">
                您可以继续查看已加载的数据，或点击刷新重试
              </div>
              <button
                onClick={handleRetry}
                className="mt-2 px-3 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 text-sm"
              >
                刷新页面
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API状态指示器 */}
      <div className="flex items-center gap-4 mb-6 text-sm">
        <div className="flex items-center">
          <div className={`w-2 h-2 rounded-full mr-2 ${apiStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-gray-600">
            API: {apiStatus === 'connected' ? '已连接' : '未连接'}
          </span>
        </div>
      </div>

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
            <a href="/enterprise" className="text-sm text-blue-600 hover:underline">
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
            <a href="/enterprise" className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
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
