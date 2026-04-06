'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Header from '@/components/Header';
import Button from '@/components/Button';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

export default function BillingPage() {
  const { t } = useLang();
  const [enterprise, setEnterprise] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [billingRecords, setBillingRecords] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [pricing, setPricing] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const savedEnterprise = localStorage.getItem('enterprise');
    if (savedEnterprise) {
      const ent = JSON.parse(savedEnterprise);
      setEnterprise(ent);
      loadBillingData(ent.enterprise_id);
    } else {
      setLoading(false);
    }
  }, []);

  const loadBillingData = async (enterpriseId: string) => {
    try {
      const [recordsRes, statsRes, pricingRes] = await Promise.all([
        api.billing.getRecords(enterpriseId),
        api.billing.getStats(enterpriseId),
        api.billing.getPricing(),
      ]);

      if (recordsRes.success) {
        setBillingRecords(recordsRes.data);
      }
      if (statsRes.success) {
        setStats(statsRes.data);
      }
      if (pricingRes.success) {
        setPricing(pricingRes.data);
      }
    } catch (err: any) {
      console.error('Failed to load billing data:', err);
      setError(t('billing.loadFailed'));
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  const formatAmount = (amount: number | null) => {
    if (amount === null || amount === undefined) return '¥0.00';
    return `¥${amount.toFixed(2)}`;
  };

  const usageTypeLabels: Record<string, string> = {
    job_post: t('billing.postJobs'),
    profile_view: t('billing.viewTalent'),
    match_query: t('billing.matchQuery'),
    match_success: t('billing.successMatch'),
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header title={t('billing.title')} description={t('billing.subtitle')} />
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-500">{t('common.loading')}</div>
          </div>
        </div>
      </div>
    );
  }

  if (!enterprise) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow p-8 text-center max-w-md">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">💰</span>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">{t('billing.loginFirst')}</h2>
          <p className="text-gray-600 mb-6">{t('billing.loginFirstDesc')}</p>
          <Link href="/enterprise/login">
            <Button variant="primary">{t('billing.loginButton')}</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title={t('billing.title')} description={t('billing.subtitle')} />

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* 返回链接 */}
        <Link href="/enterprise/dashboard" className="text-blue-600 hover:underline mb-4 inline-block">
          ← {t('billing.backToDashboard')}
        </Link>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* 价格表 */}
        {pricing && (
          <div className="bg-white rounded-xl shadow p-6 mb-8">
            <h2 className="text-lg font-bold text-gray-900 mb-4">{t('billing.pricingStandard')}</h2>
            <div className="grid md:grid-cols-4 gap-4">
              {Object.entries(pricing.pricing).map(([key, info]: [string, any]) => (
                <div key={key} className="border rounded-lg p-4">
                  <div className="text-sm text-gray-500 mb-1">{info.description}</div>
                  <div className="text-xl font-bold text-gray-900">{formatAmount(info.unit_price)}</div>
                  <div className="text-xs text-gray-400">{t('billing.perUse')}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 统计概览 */}
        {stats && (
          <div className="grid md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow p-6">
              <div className="text-sm text-gray-500 mb-1">{t('billing.totalSpending')}</div>
              <div className="text-2xl font-bold text-gray-900">{formatAmount(stats.total_spend)}</div>
            </div>
            <div className="bg-white rounded-xl shadow p-6">
              <div className="text-sm text-gray-500 mb-1">{t('billing.postedJobs')}</div>
              <div className="text-2xl font-bold text-gray-900">{stats.total_jobs_posted}</div>
            </div>
            <div className="bg-white rounded-xl shadow p-6">
              <div className="text-sm text-gray-500 mb-1">{t('billing.talentViewCount')}</div>
              <div className="text-2xl font-bold text-gray-900">{stats.total_profile_views}</div>
            </div>
            <div className="bg-white rounded-xl shadow p-6">
              <div className="text-sm text-gray-500 mb-1">{t('billing.successfulMatches')}</div>
              <div className="text-2xl font-bold text-gray-900">{stats.total_match_successes}</div>
            </div>
          </div>
        )}

        {/* 消费趋势 */}
        {stats?.by_period && Object.keys(stats.by_period).length > 0 && (
          <div className="bg-white rounded-xl shadow p-6 mb-8">
            <h2 className="text-lg font-bold text-gray-900 mb-4">{t('billing.monthlyStats')}</h2>
            <div className="space-y-4">
              {Object.entries(stats.by_period).map(([period, data]: [string, any]) => (
                <div key={period} className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900">{period}</div>
                    <div className="text-sm text-gray-500">{t('billing.total')} {data.count} {t('billing.calls')}</div>
                  </div>
                  <div className="text-xl font-bold text-gray-900">{formatAmount(data.amount)}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 账单记录 */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">{t('billing.details')}</h2>

          {billingRecords.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              {t('billing.noRecords')}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">{t('billing.time')}</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">{t('billing.type')}</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">{t('billing.quantity')}</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">{t('billing.unitPrice')}</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">{t('billing.amount')}</th>
                  </tr>
                </thead>
                <tbody>
                  {billingRecords.map((record) => (
                    <tr key={record.id} className="border-b last:border-b-0">
                      <td className="py-3 px-4 text-sm text-gray-900">
                        {formatDate(record.created_at)}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-900">
                        {usageTypeLabels[record.usage_type] || record.usage_type}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-900 text-right">
                        {record.quantity}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-900 text-right">
                        {formatAmount(record.unit_price)}
                      </td>
                      <td className="py-3 px-4 text-sm font-medium text-gray-900 text-right">
                        {formatAmount(record.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
