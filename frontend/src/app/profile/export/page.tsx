'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import Button from '@/components/Button';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

interface Profile {
  id: string;
  nickname?: string;
  status: string;
  job_intent?: any;
  created_at?: string;
  updated_at?: string;
  last_active_at?: string;
}

interface ExportHistory {
  exported_at: string;
  profile_id: string;
  profile_updated_at: string;
  resume_count: number;
  resumes: Array<{
    id: string;
    original_filename: string;
    version: number;
    is_current: boolean;
    parse_status: string;
    created_at: string;
  }>;
}

export default function ExportPage() {
  const { t } = useLang();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const [exportHistory, setExportHistory] = useState<ExportHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    fetchProfiles();
  }, []);

  async function fetchProfiles() {
    try {
      const response = await api.profiles.list({ page_size: 100 });
      setProfiles(response.data || []);
      if (response.data?.length > 0 && !selectedProfile) {
        setSelectedProfile(response.data[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch profiles:', err);
      setProfiles([]);
    } finally {
      setLoading(false);
    }
  }

  async function fetchHistory() {
    if (!selectedProfile) return;
    setHistoryLoading(true);
    try {
      const response = await api.export.profileHistory(selectedProfile, 10);
      setExportHistory(response.data);
    } catch (err) {
      console.error('Failed to fetch export history:', err);
      setExportHistory(null);
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    if (selectedProfile) {
      fetchHistory();
    }
  }, [selectedProfile]);

  function handleExport(format: 'json' | 'pdf') {
    if (!selectedProfile) return;
    setExporting(true);

    const url = format === 'json'
      ? api.export.profileJson(selectedProfile, true)
      : api.export.profilePdf(selectedProfile);

    // Open in new window for download
    window.open(url, '_blank');
    setExporting(false);
  }

  function handleResumeExport(resumeId: string, format: 'json' | 'pdf') {
    const url = format === 'json'
      ? api.export.resumeJson(resumeId)
      : api.export.resumePdf(resumeId);

    window.open(url, '_blank');
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div>
      <Header title={t('export.title')} description={t('export.subtitle')} />

      {/* Profile Selection */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">{t('export.selectProfile')}</h2>
        <select
          value={selectedProfile}
          onChange={(e) => setSelectedProfile(e.target.value)}
          className="w-full md:w-1/2 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">{t('export.selectPlaceholder')}</option>
          {profiles.map((profile) => (
            <option key={profile.id} value={profile.id}>
              {profile.nickname || profile.id} ({profile.status})
            </option>
          ))}
        </select>
      </div>

      {/* Export Options */}
      {selectedProfile && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">{t('export.options')}</h2>
          <div className="flex gap-4">
            <Button
              onClick={() => handleExport('json')}
              disabled={exporting}
            >
              {t('export.json')}
            </Button>
            <Button
              onClick={() => handleExport('pdf')}
              variant="secondary"
              disabled={exporting}
            >
              {t('export.pdf')}
            </Button>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            {t('export.fileContents')}
          </p>
        </div>
      )}

      {/* Export History */}
      {selectedProfile && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">{t('export.history')}</h2>
          {historyLoading ? (
            <div className="text-gray-500">{t('common.loading')}</div>
          ) : exportHistory ? (
            <div>
              <div className="mb-4 text-sm text-gray-600">
                <p>Profile ID: {exportHistory.profile_id}</p>
                <p>{t('export.lastUpdated')} {new Date(exportHistory.profile_updated_at).toLocaleString('zh-CN')}</p>
                <p>{t('export.resumeCount')} {exportHistory.resume_count}</p>
              </div>

              {exportHistory.resumes && exportHistory.resumes.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-md font-medium mb-2">{t('export.resumeFiles')}</h3>
                  <div className="space-y-2">
                    {exportHistory.resumes.map((resume) => (
                      <div key={resume.id} className="flex items-center justify-between border p-3 rounded">
                        <div>
                          <p className="font-medium">{resume.original_filename}</p>
                          <p className="text-sm text-gray-500">
                            {t('export.version')} {resume.version} | {resume.parse_status} | {resume.is_current ? t('export.currentVersion') : t('export.historicalVersion')}
                          </p>
                          <p className="text-xs text-gray-400">
                            {t('export.createdAt')} {new Date(resume.created_at).toLocaleString('zh-CN')}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="secondary"
                            onClick={() => handleResumeExport(resume.id, 'json')}
                          >
                            JSON
                          </Button>
                          <Button
                            variant="secondary"
                            onClick={() => handleResumeExport(resume.id, 'pdf')}
                          >
                            PDF
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-gray-500">{t('export.noHistory')}</div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!selectedProfile && profiles.length === 0 && (
        <div className="bg-white rounded-lg shadow p-6 text-center">
          <p className="text-gray-500">{t('export.noData')}</p>
        </div>
      )}
    </div>
  );
}
