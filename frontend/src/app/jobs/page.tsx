'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import DataTable from '@/components/DataTable';
import Button from '@/components/Button';
import Modal from '@/components/Modal';
import StatusBadge from '@/components/StatusBadge';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

interface Job {
  id: string;
  title: string;
  department?: string;
  description?: string;
  requirements?: any;
  compensation?: any;
  location?: any;
  status: string;
  published_at?: string;
}

export default function JobsPage() {
  const { t } = useLang();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<Job | null>(null);
  const [formData, setFormData] = useState<any>({});

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      const response = await api.jobs.list({ page_size: 100 });
      setJobs(response.data || []);
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
        <div className="text-gray-500">{t('common.loading')}</div>
      </div>
    );
  }

  const getStatusType = (status: string) => {
    switch (status) {
      case 'active': return 'active';
      case 'paused': return 'pending';
      case 'filled': return 'filled';
      case 'expired': return 'rejected';
      default: return 'pending';
    }
  };

  const columns = [
    { key: 'id', label: 'ID', render: (item: Job) => <span className="text-xs font-mono">{item.id.slice(0, 16)}...</span> },
    { key: 'title', label: t('jobs.title') },
    { key: 'department', label: t('jobs.department') },
    { key: 'location', label: t('jobs.location'), render: (item: Job) => item.location?.city || '-' },
    { key: 'compensation', label: t('jobs.salary'), render: (item: Job) => {
      const comp = item.compensation;
      if (!comp) return '-';
      return `${comp.salary_min || '-'}-${comp.salary_max || '-'} ${comp.currency || 'CNY'}`;
    }},
    { key: 'status', label: t('jobs.status'), render: (item: Job) => <StatusBadge status={getStatusType(item.status)} type="job" /> },
    { key: 'published_at', label: t('jobs.publishedAt'), render: (item: Job) => item.published_at ? new Date(item.published_at).toLocaleDateString('zh-CN') : '-' },
  ];

  const handleEdit = (item: Job) => {
    setEditingItem(item);
    setFormData(item);
    setIsModalOpen(true);
  };

  const handleDelete = async (item: Job) => {
    if (confirm(`${t('jobs.confirmDelete')} "${item.title}" ${t('jobs.confirmDeleteSuffix')}`)) {
      try {
        await api.jobs.delete(item.id);
        fetchData();
      } catch (err) {
        alert(t('jobs.deleteFailed'));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingItem) {
        await api.jobs.update(editingItem.id, { job: formData });
      }
      setIsModalOpen(false);
      setEditingItem(null);
      setFormData({});
      fetchData();
    } catch (err) {
      alert(t('jobs.updateFailed'));
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev: any) => ({ ...prev, [name]: value }));
  };

  return (
    <div>
      <Header title={t('jobs.list')} description={t('jobs.manageAll')} />

      <div className="mb-4 flex justify-end">
        <Button onClick={() => fetchData()}>
          {t('common.refresh')}
        </Button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <DataTable
          columns={columns}
          data={jobs}
          keyField="id"
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEditingItem(null); }}
        title={t('jobs.details')}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('jobs.title')}</label>
            <input
              type="text"
              name="title"
              value={formData.title || ''}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('jobs.department')}</label>
            <input
              type="text"
              name="department"
              value={formData.department || ''}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('jobs.description')}</label>
            <textarea
              name="description"
              value={formData.description || ''}
              onChange={handleInputChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('jobs.status')}</label>
            <select
              name="status"
              value={formData.status || 'active'}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="active">{t('jobs.recruiting')}</option>
              <option value="paused">{t('jobs.paused')}</option>
              <option value="filled">{t('jobs.filled')}</option>
              <option value="expired">{t('jobs.expired')}</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
              {t('common.close')}
            </Button>
            <Button type="submit">
              {t('common.save')}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
