'use client';

import { useLang } from '@/lib/i18n';

interface TemplateCardProps {
  template: {
    id: string;
    name: string;
    description: string;
    category: string;
    type: 'seeker' | 'employer';
    usage_count?: number;
    rating?: number;
    tags?: string[];
  };
  onPreview?: (template: any) => void;
}

const categoryIcons: Record<string, string> = {
  resume: '📄',
  interview: '🎯',
  job_search: '🔍',
  salary_negotiation: '💰',
  employer: '🏢',
  screening: '✅',
  default: '📋',
};

export default function TemplateCard({ template, onPreview }: TemplateCardProps) {
  const { t } = useLang();

  const categoryLabels: Record<string, string> = {
    resume: t('template.resumeOptimization'),
    interview: t('template.interviewPrep'),
    job_search: t('template.jobSearch'),
    salary_negotiation: t('template.salaryNegotiation'),
    employer: t('template.enterpriseRecruiting'),
    screening: t('template.resumeScreening'),
    default: t('template.general'),
  };

  const icon = categoryIcons[template.category] || categoryIcons.default;
  const categoryLabel = categoryLabels[template.category] || template.category;

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow border border-gray-100 overflow-hidden">
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start gap-3 mb-4">
          <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
            template.type === 'seeker' ? 'bg-blue-100' : 'bg-purple-100'
          }`}>
            <span className="text-2xl">{icon}</span>
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900">{template.name}</h3>
            <div className="flex items-center gap-2 mt-1">
              <span className={`px-2 py-0.5 text-xs rounded ${
                template.type === 'seeker' ? 'bg-blue-50 text-blue-600' : 'bg-purple-50 text-purple-600'
              }`}>
                {template.type === 'seeker' ? t('template.forJobSeekers') : t('template.forEnterprises')}
              </span>
              <span className="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-600">
                {categoryLabel}
              </span>
            </div>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {template.description}
        </p>

        {/* Tags */}
        {template.tags && template.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {template.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
              >
                {tag}
              </span>
            ))}
            {template.tags.length > 3 && (
              <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-500 rounded">
                +{template.tags.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
          {template.usage_count !== undefined && (
            <div className="flex items-center gap-1">
              <span>📥</span>
              <span>{template.usage_count} {t('template.timesUsed')}</span>
            </div>
          )}
          {template.rating !== undefined && (
            <div className="flex items-center gap-1">
              <span>⭐</span>
              <span>{template.rating.toFixed(1)}</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-3 border-t border-gray-100">
          {onPreview && (
            <button
              onClick={() => onPreview(template)}
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              {t('template.preview')}
            </button>
          )}
          <button className="flex-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            {t('template.useTemplate')}
          </button>
        </div>
      </div>
    </div>
  );
}
