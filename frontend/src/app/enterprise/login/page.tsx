'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Button from '@/components/Button';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

export default function EnterpriseLoginPage() {
  const router = useRouter();
  const { t } = useLang();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = t('login.enterEmail');
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = t('login.invalidEmail');
    }
    if (!formData.password) {
      newErrors.password = t('login.enterPassword');
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      const response = await api.enterprises.login({
        email: formData.email,
        password: formData.password,
      });

      if (response.success && response.data) {
        const enterpriseData = {
          enterprise_id: response.data?.enterprise_id,
          company_name: response.data?.company_name || '',
          status: response.data?.status || '',
          email: formData.email,
          api_keys: response.data?.api_keys || [],
        };

        if (!enterpriseData.enterprise_id) {
          setErrors({ submit: t('login.responseError') });
          return;
        }

        localStorage.setItem('enterprise', JSON.stringify(enterpriseData));
        router.push('/enterprise/dashboard');
      } else {
        setErrors({ submit: response.message || t('login.failed') });
      }
    } catch (err: unknown) {
      if (err instanceof TypeError && err.message.includes('fetch')) {
        setErrors({ submit: t('login.networkFailed') });
      } else if (err instanceof Error) {
        setErrors({ submit: err.message || t('login.failed') });
      } else {
        setErrors({ submit: t('login.failed') });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-xl shadow-blue-500/30 mb-4">
            <span className="text-white font-bold text-2xl">A</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{t('login.title')}</h1>
          <p className="text-gray-500 mt-1">{t('login.subtitle')}</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 md:p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('login.email')}
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${errors.email ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'}`}
                placeholder={t('login.emailPlaceholder')}
              />
              {errors.email && (
                <p className="text-red-500 text-xs mt-1">{errors.email}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('login.password')}
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all ${errors.password ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'}`}
                placeholder={t('login.passwordPlaceholder')}
              />
              {errors.password && (
                <p className="text-red-500 text-xs mt-1">{errors.password}</p>
              )}
            </div>

            {errors.submit && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm animate-fade-in">
                {errors.submit}
              </div>
            )}

            <Button type="submit" size="lg" className="w-full shadow-lg shadow-blue-500/30" disabled={isSubmitting}>
              {isSubmitting ? t('login.loggingIn') : t('login.submit')}
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-100 text-center">
            <span className="text-sm text-gray-500">
              {t('login.notRegistered')}{' '}
            </span>
            <a
              href="/enterprise/register"
              className="text-sm text-blue-600 hover:underline"
            >
              {t('login.registerNow')}
            </a>
          </div>
        </div>

        <div className="text-center text-sm text-gray-400 mt-6">
          <a
            href="/"
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            {t('login.backToHome')}
          </a>
        </div>
      </div>
    </div>
  );
}
