'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import AgentCard from '@/components/AgentCard';
import Button from '@/components/Button';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

interface Agent {
  id: string;
  name: string;
  type: 'seeker' | 'employer';
  platform?: string;
  status: string;
  rating?: number;
  success_rate?: number;
  total_jobs_completed?: number;
  created_at?: string;
}

export default function MarketplacePage() {
  const { t } = useLang();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'seeker' | 'employer'>('all');
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchAgents();
  }, [filter]);

  async function fetchAgents() {
    try {
      setLoading(true);
      const params: { type?: 'seeker' | 'employer'; status?: string; page: number; page_size: number } = {
        status: 'active',
        page: 1,
        page_size: 20,
      };
      if (filter !== 'all') {
        params.type = filter;
      }
      const response = await api.agents.list(params);
      setAgents(response.data || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('Failed to fetch agents:', err);
      setAgents([]);
    } finally {
      setLoading(false);
    }
  }

  const getFilterLabel = () => {
    switch (filter) {
      case 'seeker':
        return t('market.jobSeekerAgent');
      case 'employer':
        return t('market.recruiterAgent');
      default:
        return t('market.allAgents');
    }
  };

  return (
    <div>
      <Header
        title={t('market.title')}
        description={t('market.subtitle')}
      />

      {/* Filters */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Button
            variant={filter === 'all' ? 'primary' : 'secondary'}
            onClick={() => setFilter('all')}
          >
            {t('market.all')}
          </Button>
          <Button
            variant={filter === 'seeker' ? 'primary' : 'secondary'}
            onClick={() => setFilter('seeker')}
          >
            {t('market.jobSeekerAgent')}
          </Button>
          <Button
            variant={filter === 'employer' ? 'primary' : 'secondary'}
            onClick={() => setFilter('employer')}
          >
            {t('market.recruiterAgent')}
          </Button>
        </div>
        <p className="text-sm text-gray-500">
          {t('market.totalPrefix')} {total} {t('market.totalSuffix')}
        </p>
      </div>

      {/* Agent Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">{t('common.loading')}</div>
        </div>
      ) : agents.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 mb-4">{t('market.noAgents')}</p>
          <p className="text-sm text-gray-400">
            {t('market.stayTuned')}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}

      {/* Info Section */}
      <div className="mt-12 bg-blue-50 rounded-lg p-6">
        <h3 className="font-semibold text-gray-900 mb-2">{t('market.about')}</h3>
        <p className="text-sm text-gray-600 mb-4">
          {t('market.aboutDesc')}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4">
            <div className="text-2xl mb-2">✅</div>
            <h4 className="font-medium text-gray-900 mb-1">{t('market.certified')}</h4>
            <p className="text-xs text-gray-500">{t('market.certifiedDesc')}</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <div className="text-2xl mb-2">📊</div>
            <h4 className="font-medium text-gray-900 mb-1">{t('market.ratingSystem')}</h4>
            <p className="text-xs text-gray-500">{t('market.ratingDesc')}</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <div className="text-2xl mb-2">🔗</div>
            <h4 className="font-medium text-gray-900 mb-1">{t('market.plugAndPlay')}</h4>
            <p className="text-xs text-gray-500">{t('market.plugAndPlayDesc')}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
