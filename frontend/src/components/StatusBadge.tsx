import { useLang } from '@/lib/i18n';

interface StatusBadgeProps {
  status: string;
  type: 'jobSeeker' | 'job' | 'enterprise';
}

export default function StatusBadge({ status, type }: StatusBadgeProps) {
  const { t } = useLang();

  const statusConfig = {
    jobSeeker: {
      active: { label: t('status.active'), className: 'bg-green-100 text-green-800' },
      paused: { label: t('status.paused'), className: 'bg-yellow-100 text-yellow-800' },
      deleted: { label: t('status.deleted'), className: 'bg-red-100 text-red-800' },
      inactive: { label: t('status.inactive'), className: 'bg-gray-100 text-gray-800' },
      hired: { label: t('status.hired'), className: 'bg-blue-100 text-blue-800' },
    },
    job: {
      active: { label: t('status.recruiting'), className: 'bg-green-100 text-green-800' },
      paused: { label: t('status.suspended'), className: 'bg-yellow-100 text-yellow-800' },
      filled: { label: t('status.filled'), className: 'bg-blue-100 text-blue-800' },
      expired: { label: t('status.expired'), className: 'bg-red-100 text-red-800' },
      open: { label: t('status.recruiting'), className: 'bg-green-100 text-green-800' },
      closed: { label: t('status.closed'), className: 'bg-gray-100 text-gray-800' },
    },
    enterprise: {
      approved: { label: t('status.certified'), className: 'bg-green-100 text-green-800' },
      verified: { label: t('status.certified'), className: 'bg-green-100 text-green-800' },
      pending: { label: t('status.pendingReview'), className: 'bg-yellow-100 text-yellow-800' },
      rejected: { label: t('status.rejected'), className: 'bg-red-100 text-red-800' },
      suspended: { label: t('status.suspended'), className: 'bg-red-100 text-red-800' },
    },
  };

  const config = statusConfig[type] as Record<string, { label: string; className: string }>;
  const statusInfo = config[status] || { label: status, className: 'bg-gray-100 text-gray-800' };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.className}`}>
      {statusInfo.label}
    </span>
  );
}
