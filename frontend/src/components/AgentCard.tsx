'use client';

import Link from 'next/link';
import AgentRating from './AgentRating';
import { useLang } from '@/lib/i18n';

interface AgentCardProps {
  agent: {
    id: string;
    name: string;
    type: 'seeker' | 'employer';
    platform?: string;
    status: string;
    rating?: number;
    success_rate?: number;
    total_jobs_completed?: number;
    created_at?: string;
  };
}

export default function AgentCard({ agent }: AgentCardProps) {
  const { t } = useLang();
  const isSeeker = agent.type === 'seeker';

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow border border-gray-100 overflow-hidden">
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              isSeeker ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'
            }`}>
              <span className="text-xl">{isSeeker ? '👤' : '🏢'}</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{agent.name}</h3>
              <p className="text-sm text-gray-500">
                {isSeeker ? t('agent.jobSeeker') : t('agent.recruiter')}
                {agent.platform && ` · ${agent.platform}`}
              </p>
            </div>
          </div>
          <span className={`px-2 py-1 text-xs rounded ${
            agent.status === 'active' ? 'bg-green-100 text-green-700' :
            agent.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {agent.status === 'active' ? t('status.certified') : agent.status === 'pending' ? t('status.pendingReview') : agent.status}
          </span>
        </div>

        {/* Stats */}
        {agent.rating !== undefined && (
          <div className="mb-3">
            <AgentRating rating={agent.rating} size="sm" />
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">{t('agent.successRate')}</p>
            <p className="text-lg font-semibold text-gray-900">
              {agent.success_rate !== undefined ? `${agent.success_rate}%` : '-'}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">{t('agent.completedTasks')}</p>
            <p className="text-lg font-semibold text-gray-900">
              {agent.total_jobs_completed ?? 0}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            ID: {agent.id.slice(0, 8)}...
          </p>
          <Link
            href={`/agents/${agent.id}`}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {t('agent.viewDetails')} →
          </Link>
        </div>
      </div>
    </div>
  );
}
