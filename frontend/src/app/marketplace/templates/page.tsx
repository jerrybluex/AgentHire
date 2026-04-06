'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import TemplateCard from '@/components/TemplateCard';
import Button from '@/components/Button';
import Modal from '@/components/Modal';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  type: 'seeker' | 'employer';
  usage_count?: number;
  rating?: number;
  tags?: string[];
  content?: string;
}

export default function TemplatesPage() {
  const { t } = useLang();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState<string>('all');
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);
  const [total, setTotal] = useState(0);

  const categories = [
    { value: 'all', label: t('templates.all') },
    { value: 'seeker', label: t('templates.forJobSeekers') },
    { value: 'employer', label: t('templates.forEnterprises') },
    { value: 'resume', label: t('templates.resumeOptimization') },
    { value: 'interview', label: t('templates.interviewPrep') },
    { value: 'job_search', label: t('templates.jobSearch') },
    { value: 'salary_negotiation', label: t('templates.salaryNegotiation') },
  ];

  useEffect(() => {
    fetchTemplates();
  }, [category]);

  async function fetchTemplates() {
    try {
      setLoading(true);
      const params: { category?: string; page: number; page_size: number } = {
        page: 1,
        page_size: 50,
      };
      if (category !== 'all') {
        // Check if it's a type filter or category filter
        if (['seeker', 'employer'].includes(category)) {
          params.category = category;
        } else {
          params.category = category;
        }
      }
      const response = await api.templates.list(params);
      setTemplates(response.data || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('Failed to fetch templates:', err);
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <Header
        title={t('templates.title')}
        description={t('templates.subtitle')}
      />

      {/* Filters */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2 flex-wrap">
          {categories.map((cat) => (
            <Button
              key={cat.value}
              variant={category === cat.value ? 'primary' : 'secondary'}
              onClick={() => setCategory(cat.value)}
            >
              {cat.label}
            </Button>
          ))}
        </div>
        <p className="text-sm text-gray-500">
          {t('templates.totalPrefix')} {total} {t('templates.totalSuffix')}
        </p>
      </div>

      {/* Templates Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">{t('common.loading')}</div>
        </div>
      ) : templates.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 mb-4">{t('templates.noTemplates')}</p>
          <p className="text-sm text-gray-400">
            {t('templates.stayTuned')}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              onPreview={setPreviewTemplate}
            />
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {previewTemplate && (
        <Modal
          isOpen={!!previewTemplate}
          onClose={() => setPreviewTemplate(null)}
          title={previewTemplate.name}
        >
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-500 mb-1">{t('templates.description')}</h4>
              <p className="text-gray-900">{previewTemplate.description}</p>
            </div>
            {previewTemplate.content && (
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-1">{t('templates.templateContent')}</h4>
                <pre className="bg-gray-50 p-4 rounded-lg text-sm text-gray-700 overflow-auto max-h-64">
                  {previewTemplate.content}
                </pre>
              </div>
            )}
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setPreviewTemplate(null)}>
                {t('common.close')}
              </Button>
              <Button>{t('templates.useThisTemplate')}</Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Info Section */}
      <div className="mt-12 bg-purple-50 rounded-lg p-6">
        <h3 className="font-semibold text-gray-900 mb-2">{t('templates.about')}</h3>
        <p className="text-sm text-gray-600 mb-4">
          {t('templates.aboutDesc')}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg p-4">
            <div className="text-2xl mb-2">🚀</div>
            <h4 className="font-medium text-gray-900 mb-1">{t('templates.quickStart')}</h4>
            <p className="text-xs text-gray-500">{t('templates.quickStartDesc')}</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <div className="text-2xl mb-2">🛠️</div>
            <h4 className="font-medium text-gray-900 mb-1">{t('templates.customizable')}</h4>
            <p className="text-xs text-gray-500">{t('templates.customizableDesc')}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
