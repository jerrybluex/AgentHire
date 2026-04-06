'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import DataTable from '@/components/DataTable';
import Button from '@/components/Button';
import Modal from '@/components/Modal';
import StatusBadge from '@/components/StatusBadge';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

interface Profile {
  id: string;
  nickname?: string;
  status: string;
  job_intent?: any;
  created_at?: string;
}

export default function JobSeekersPage() {
  const { t } = useLang();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<Profile | null>(null);
  const [formData, setFormData] = useState<any>({});

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      const response = await api.profiles.list({ page_size: 100 });
      setProfiles(response.data || []);
    } catch (err) {
      console.error('Failed to fetch profiles:', err);
      setProfiles([]);
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
      case 'pending': return 'pending';
      case 'deleted': return 'rejected';
      default: return 'pending';
    }
  };

  const columns = [
    { key: 'id', label: 'ID', render: (item: Profile) => <span className="text-xs font-mono">{item.id.slice(0, 16)}...</span> },
    { key: 'nickname', label: t('seekers.nickname') },
    { key: 'status', label: t('seekers.status'), render: (item: Profile) => <StatusBadge status={getStatusType(item.status)} type="jobSeeker" /> },
    { key: 'job_intent', label: t('seekers.jobIntent'), render: (item: Profile) => item.job_intent?.target_roles?.join(', ') || '-' },
    { key: 'created_at', label: t('seekers.createdAt'), render: (item: Profile) => item.created_at ? new Date(item.created_at).toLocaleDateString('zh-CN') : '-' },
  ];

  const handleEdit = (item: Profile) => {
    setEditingItem(item);
    setFormData(item);
    setIsModalOpen(true);
  };

  const handleDelete = async (item: Profile) => {
    if (confirm(`${t('seekers.confirmDelete')} "${item.nickname || item.id}" ${t('seekers.confirmDeleteSuffix')}`)) {
      try {
        await api.profiles.delete(item.id);
        fetchData();
      } catch (err) {
        alert(t('seekers.deleteFailed'));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingItem) {
        await api.profiles.update(editingItem.id, { profile: formData });
      }
      setIsModalOpen(false);
      setEditingItem(null);
      setFormData({});
      fetchData();
    } catch (err) {
      alert(editingItem ? t('seekers.updateFailed') : t('seekers.createFailed'));
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev: any) => ({ ...prev, [name]: value }));
  };

  return (
    <div>
      <Header title={t('seekers.list')} description={t('seekers.manageAll')} />

      <div className="mb-4 flex justify-end">
        <Button onClick={() => { setEditingItem(null); setFormData({}); setIsModalOpen(true); }}>
          {t('common.refresh')}
        </Button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <DataTable
          columns={columns}
          data={profiles}
          keyField="id"
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEditingItem(null); }}
        title={t('seekers.details')}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('seekers.nickname')}</label>
            <input
              type="text"
              name="nickname"
              value={formData.nickname || ''}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('seekers.status')}</label>
            <select
              name="status"
              value={formData.status || 'active'}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="active">{t('seekers.active')}</option>
              <option value="paused">{t('seekers.paused')}</option>
              <option value="deleted">{t('seekers.deleted')}</option>
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
