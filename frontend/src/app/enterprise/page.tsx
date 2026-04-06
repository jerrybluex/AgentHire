'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Header from '@/components/Header';
import Button from '@/components/Button';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

interface Enterprise {
  id: string;
  name: string;
  unified_social_credit_code?: string;
  contact?: any;
  status: string;
  industry?: string;
  company_size?: string;
  website?: string;
  description?: string;
  created_at?: string;
  certification?: any;
}

export default function EnterprisePage() {
  const { t } = useLang();
  const [enterprises, setEnterprises] = useState<Enterprise[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEnterprise, setSelectedEnterprise] = useState<Enterprise | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      const response = await api.enterprises.list();
      setEnterprises(response.data || []);
    } catch (err) {
      console.error('Failed to fetch enterprises:', err);
      setEnterprises([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleViewDetail(enterprise: Enterprise) {
    setDetailLoading(true);
    setSelectedEnterprise(enterprise);
    setDetailLoading(false);
  }

  function closeDetail() {
    setSelectedEnterprise(null);
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">{t('enterprise.verified')}</span>;
      case 'pending':
        return <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded">{t('enterprise.pendingReview')}</span>;
      case 'rejected':
        return <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">{t('enterprise.rejected')}</span>;
      case 'suspended':
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">{t('enterprise.deactivated')}</span>;
      default:
        return <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">{status}</span>;
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

  return (
    <div>
      <Header title={t('enterprise.management')} description={t('enterprise.manageAllAccounts')} />

      <div className="mb-6">
        <p className="text-gray-600 mb-4">
          {t('enterprise.listDescription')}{' '}
          <Link href="/dashboard" className="text-blue-600 hover:underline">
            {t('enterprise.adminDashboard')}
          </Link>
          。
        </p>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('enterprise.name')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('enterprise.industry')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('enterprise.scale')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('enterprise.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('enterprise.registrationTime')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('enterprise.actions')}</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {enterprises.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                  {t('enterprise.noData')}
                </td>
              </tr>
            ) : (
              enterprises.map((enterprise) => (
                <tr key={enterprise.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{enterprise.name}</div>
                    <div className="text-xs text-gray-500 font-mono">{enterprise.id}</div>
                  </td>
                  <td className="px-6 py-4 text-gray-600">{enterprise.industry || '-'}</td>
                  <td className="px-6 py-4 text-gray-600">{enterprise.company_size || '-'}</td>
                  <td className="px-6 py-4">{getStatusBadge(enterprise.status)}</td>
                  <td className="px-6 py-4 text-gray-600">
                    {enterprise.created_at ? new Date(enterprise.created_at).toLocaleDateString('zh-CN') : '-'}
                  </td>
                  <td className="px-6 py-4">
                    <Button variant="secondary" onClick={() => handleViewDetail(enterprise)}>
                      {t('enterprise.viewDetails')}
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 企业详情弹窗 */}
      {selectedEnterprise && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-900">{t('enterprise.details')}</h2>
              <button
                onClick={closeDetail}
                className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                &times;
              </button>
            </div>

            <div className="p-6">
              {detailLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* 基本信息 */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('enterprise.basicInfo')}</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm text-gray-500">{t('enterprise.name')}</div>
                        <div className="font-medium text-gray-900">{selectedEnterprise.name}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">{t('enterprise.id')}</div>
                        <div className="font-mono text-sm text-gray-700">{selectedEnterprise.id}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">{t('enterprise.creditCode')}</div>
                        <div className="font-mono text-sm text-gray-700">{selectedEnterprise.unified_social_credit_code || '-'}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">{t('enterprise.status')}</div>
                        <div className="mt-1">{getStatusBadge(selectedEnterprise.status)}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">{t('enterprise.industry')}</div>
                        <div className="text-gray-700">{selectedEnterprise.industry || '-'}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">{t('enterprise.scale')}</div>
                        <div className="text-gray-700">{selectedEnterprise.company_size || '-'}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">{t('enterprise.website')}</div>
                        <div className="text-gray-700">{selectedEnterprise.website || '-'}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">{t('enterprise.registrationTime')}</div>
                        <div className="text-gray-700">
                          {selectedEnterprise.created_at ? new Date(selectedEnterprise.created_at).toLocaleDateString('zh-CN') : '-'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 联系方式 */}
                  {selectedEnterprise.contact && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('enterprise.contactInfo')}</h3>
                      <div className="grid grid-cols-2 gap-4">
                        {selectedEnterprise.contact.email && (
                          <div>
                            <div className="text-sm text-gray-500">{t('enterprise.email')}</div>
                            <div className="text-gray-700">{selectedEnterprise.contact.email}</div>
                          </div>
                        )}
                        {selectedEnterprise.contact.phone && (
                          <div>
                            <div className="text-sm text-gray-500">{t('enterprise.phone')}</div>
                            <div className="text-gray-700">{selectedEnterprise.contact.phone}</div>
                          </div>
                        )}
                        {selectedEnterprise.contact.name && (
                          <div>
                            <div className="text-sm text-gray-500">{t('enterprise.contactPerson')}</div>
                            <div className="text-gray-700">{selectedEnterprise.contact.name}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* 认证信息 */}
                  {selectedEnterprise.certification && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('enterprise.certInfo')}</h3>
                      <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                        {selectedEnterprise.certification.verified_at && (
                          <div className="text-sm text-gray-500">
                            {t('enterprise.certTime')}{new Date(selectedEnterprise.certification.verified_at).toLocaleString('zh-CN')}
                          </div>
                        )}
                        {selectedEnterprise.certification.verified_by && (
                          <div className="text-sm text-gray-500">
                            {t('enterprise.certBy')}{selectedEnterprise.certification.verified_by}
                          </div>
                        )}
                        {selectedEnterprise.certification.business_license_url && (
                          <div className="mt-3">
                            <div className="text-sm text-gray-500 mb-2">{t('enterprise.businessLicense')}</div>
                            <a
                              href={selectedEnterprise.certification.business_license_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block border rounded-lg overflow-hidden hover:shadow-lg transition-shadow max-w-md"
                            >
                              {selectedEnterprise.certification.business_license_url.match(/\.(jpg|jpeg|png|gif)$/i) ? (
                                <img
                                  src={selectedEnterprise.certification.business_license_url}
                                  alt={t('enterprise.businessLicense')}
                                  className="w-full h-auto max-h-64 object-contain"
                                />
                              ) : (
                                <div className="flex items-center gap-2 p-4 bg-blue-50 text-blue-600">
                                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                  </svg>
                                  <span>{t('enterprise.viewLicense')}</span>
                                </div>
                              )}
                            </a>
                          </div>
                        )}
                        {selectedEnterprise.certification.legal_person_id_url && (
                          <div className="mt-3">
                            <div className="text-sm text-gray-500 mb-2">{t('enterprise.legalPersonId')}</div>
                            <a
                              href={selectedEnterprise.certification.legal_person_id_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block border rounded-lg overflow-hidden hover:shadow-lg transition-shadow max-w-md"
                            >
                              {selectedEnterprise.certification.legal_person_id_url.match(/\.(jpg|jpeg|png|gif)$/i) ? (
                                <img
                                  src={selectedEnterprise.certification.legal_person_id_url}
                                  alt={t('enterprise.legalPersonId')}
                                  className="w-full h-auto max-h-64 object-contain"
                                />
                              ) : (
                                <div className="flex items-center gap-2 p-4 bg-blue-50 text-blue-600">
                                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3 3 0 00-3 3h6a3 3 0 00-3-3z" />
                                  </svg>
                                  <span>{t('enterprise.viewLegalId')}</span>
                                </div>
                              )}
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* 企业简介 */}
                  {selectedEnterprise.description && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">{t('enterprise.description')}</h3>
                      <div className="text-gray-700">{selectedEnterprise.description}</div>
                    </div>
                  )}

                  {/* 操作按钮 */}
                  <div className="flex justify-end gap-3 pt-4 border-t">
                    <Button variant="secondary" onClick={closeDetail}>
                      {t('common.close')}
                    </Button>
                    {selectedEnterprise.status === 'pending' && (
                      <Link href="/dashboard">
                        <Button variant="primary">{t('enterprise.goReview')}</Button>
                      </Link>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
