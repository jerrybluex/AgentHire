'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import Button from '@/components/Button';
import { useLang } from '@/lib/i18n';

export default function ClaimPage() {
  const { t } = useLang();
  const [userId, setUserId] = useState<string>('');
  const [agentId, setAgentId] = useState<string>('');
  const [verificationCode, setVerificationCode] = useState<string>('');
  const [step, setStep] = useState<'initiate' | 'verify' | 'success'>('initiate');
  const [claimInfo, setClaimInfo] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(false);

  async function handleInitiateClaim() {
    if (!userId || !agentId) {
      setError(t('claim.enterIds'));
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`/api/v1/claim/agent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId,
        },
        body: JSON.stringify({ agent_id: agentId }),
      });

      const data = await response.json();

      if (data.success) {
        setClaimInfo(data.data);
        setStep('verify');
      } else {
        setError(data.detail || t('claim.initiateFailed'));
      }
    } catch (err) {
      setError(t('claim.networkError'));
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyClaim() {
    if (!verificationCode) {
      setError(t('claim.enterCode'));
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`/api/v1/claim/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId,
        },
        body: JSON.stringify({
          agent_id: agentId,
          verification_code: verificationCode,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setStep('success');
      } else {
        setError(data.detail || t('claim.verifyFailed'));
      }
    } catch (err) {
      setError(t('claim.networkError'));
    } finally {
      setLoading(false);
    }
  }

  async function handleCheckStatus() {
    if (!userId || !agentId) {
      setError(t('claim.enterIds'));
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`/api/v1/claim/status/${agentId}`, {
        headers: {
          'X-User-ID': userId,
        },
      });

      const data = await response.json();

      if (data.success) {
        setClaimInfo(data.data);
        if (data.data.status === 'verified') {
          setStep('success');
        } else if (data.data.status === 'pending') {
          setStep('verify');
        }
      } else {
        setError(data.detail || t('claim.noRecord'));
      }
    } catch (err) {
      setError(t('claim.networkError'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <Header title={t('claim.title')} description={t('claim.subtitle')} />

      {/* User ID Input */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">{t('claim.userInfo')}</h2>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">User ID</label>
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder={t('claim.userIdPlaceholder')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00D084]"
          />
        </div>
      </div>

      {/* Agent ID Input */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">{t('claim.agentInfo')}</h2>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Agent ID</label>
          <input
            type="text"
            value={agentId}
            onChange={(e) => setAgentId(e.target.value)}
            placeholder={t('claim.agentIdPlaceholder')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00D084]"
          />
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Initiate Step */}
      {step === 'initiate' && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">{t('claim.initiate')}</h2>
          <p className="text-gray-600 mb-4">
            {t('claim.initiateDesc')}
          </p>
          <div className="flex gap-4">
            <Button onClick={handleInitiateClaim} disabled={loading}>
              {loading ? t('claim.processing') : t('claim.initiate')}
            </Button>
            <Button variant="secondary" onClick={handleCheckStatus} disabled={loading}>
              {t('claim.viewStatus')}
            </Button>
          </div>
        </div>
      )}

      {/* Verify Step */}
      {step === 'verify' && claimInfo && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">{t('claim.verify')}</h2>
          <div className="mb-4 p-4 bg-blue-50 rounded">
            <p className="text-sm text-blue-800">
              <strong>{t('claim.claimId')}</strong> {claimInfo.claim_id}
            </p>
            <p className="text-sm text-blue-800">
              <strong>{t('claim.verificationCode')}</strong> {claimInfo.verification_code}
            </p>
            <p className="text-sm text-blue-800">
              <strong>{t('claim.expiresAt')}</strong> {new Date(claimInfo.expires_at).toLocaleString('zh-CN')}
            </p>
          </div>
          <p className="text-gray-600 mb-4">
            {t('claim.enterCodeDesc')}
          </p>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('claim.codeLabel')}</label>
            <input
              type="text"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value)}
              maxLength={6}
              placeholder={t('claim.codePlaceholder')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00D084]"
            />
          </div>
          <div className="flex gap-4">
            <Button onClick={handleVerifyClaim} disabled={loading}>
              {loading ? t('claim.verifying') : t('claim.verifyButton')}
            </Button>
            <Button variant="secondary" onClick={() => setStep('initiate')}>
              {t('common.back')}
            </Button>
          </div>
        </div>
      )}

      {/* Success Step */}
      {step === 'success' && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4 text-green-600">{t('claim.success')}</h2>
          <div className="p-4 bg-green-50 rounded mb-4">
            <p className="text-green-800">
              Agent <strong>{agentId}</strong> {t('claim.successDesc')}
            </p>
          </div>
          <Button onClick={() => {
            setStep('initiate');
            setClaimInfo(null);
            setVerificationCode('');
          }}>
            {t('claim.claimMore')}
          </Button>
        </div>
      )}

      {/* Info Box */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="font-medium text-gray-700 mb-2">{t('claim.processGuide')}</h3>
        <ol className="text-sm text-gray-600 list-decimal list-inside space-y-1">
          <li>{t('claim.step1')}</li>
          <li>{t('claim.step2')}</li>
          <li>{t('claim.step3')}</li>
          <li>{t('claim.step4')}</li>
          <li>{t('claim.step5')}</li>
        </ol>
      </div>
    </div>
  );
}
