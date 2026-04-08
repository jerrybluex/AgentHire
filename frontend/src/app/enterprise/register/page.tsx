'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Button from '@/components/Button';
import { api } from '@/lib/api';
import { useLang } from '@/lib/i18n';

export default function EnterpriseRegisterPage() {
  const router = useRouter();
  const { t } = useLang();
  const [formData, setFormData] = useState({
    company_name: '',
    unified_social_credit_code: '',
    contact_name: '',
    contact_phone: '',
    contact_email: '',
    password: '',
    confirm_password: '',
  });
  const [files, setFiles] = useState<{
    business_license: File | null;
    legal_person_id: File | null;
  }>({
    business_license: null,
    legal_person_id: null,
  });
  const [uploadedUrls, setUploadedUrls] = useState<{
    business_license: string;
    legal_person_id: string;
  }>({
    business_license: '',
    legal_person_id: '',
  });
  const [uploading, setUploading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const businessLicenseRef = useRef<HTMLInputElement>(null);
  const legalPersonIdRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>, fileType: 'business_license' | 'legal_person_id') => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
      setErrors((prev) => ({ ...prev, [fileType]: t('register.formatError') }));
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrors((prev) => ({ ...prev, [fileType]: t('register.sizeError') }));
      return;
    }

    setErrors((prev) => ({ ...prev, [fileType]: '' }));

    setUploading(true);
    try {
      const fakeUrl = `https://storage.agenthire.com/uploads/${fileType}_${Date.now()}_${file.name}`;
      setUploadedUrls((prev) => ({ ...prev, [fileType]: fakeUrl }));
      setFiles((prev) => ({ ...prev, [fileType]: file }));
    } catch (err) {
      setErrors((prev) => ({ ...prev, [fileType]: t('register.uploadFailed') }));
    } finally {
      setUploading(false);
    }
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.company_name) newErrors.company_name = t('register.enterName');
    if (!formData.unified_social_credit_code) newErrors.unified_social_credit_code = t('register.enterCreditCode');
    if (formData.unified_social_credit_code.length !== 18) {
      newErrors.unified_social_credit_code = t('register.creditCodeLength');
    }
    if (!formData.contact_name) newErrors.contact_name = t('register.enterContactName');
    if (!formData.contact_phone) newErrors.contact_phone = t('register.enterContactPhone');
    if (!formData.contact_email) newErrors.contact_email = t('register.enterContactEmail');
    if (!formData.password) newErrors.password = t('register.enterPassword');
    if (formData.password.length < 6) newErrors.password = t('register.passwordLength');
    if (formData.password !== formData.confirm_password) {
      newErrors.confirm_password = t('register.passwordMismatch');
    }
    if (!files.business_license) newErrors.business_license = t('register.uploadLicense');
    if (!files.legal_person_id) newErrors.legal_person_id = t('register.uploadId');
    return newErrors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    setErrors({});
    try {
      // Upload files first
      let businessLicenseUrl = '';
      let legalPersonIdUrl = '';

      if (files.business_license) {
        const uploadRes = await api.enterprises.uploadFile(files.business_license);
        if (uploadRes.success) {
          businessLicenseUrl = uploadRes.data.url;
        }
      }

      if (files.legal_person_id) {
        const uploadRes = await api.enterprises.uploadFile(files.legal_person_id);
        if (uploadRes.success) {
          legalPersonIdUrl = uploadRes.data.url;
        }
      }

      const response = await fetch(`/api/v1/enterprise/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          company_name: formData.company_name,
          unified_social_credit_code: formData.unified_social_credit_code,
          contact: {
            name: formData.contact_name,
            phone: formData.contact_phone,
            email: formData.contact_email,
          },
          company_info: {},
          password: formData.password,
          certification: {
            business_license_url: businessLicenseUrl,
            legal_person_id_url: legalPersonIdUrl,
          },
        }),
      });

      const data = await response.json();
      if (data.success) {
        setSuccess(true);
      } else {
        setErrors({ submit: data.message || t('register.failed') });
      }
    } catch (err: unknown) {
      console.error('Registration error:', err);
      if (err instanceof TypeError && err.message.includes('fetch')) {
        setErrors({ submit: t('register.networkFailed') });
      } else if (err instanceof Error) {
        setErrors({ submit: `${t('register.networkError')}${err.message}` });
      } else {
        setErrors({ submit: t('register.failed') });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-[#FAF8F5] flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center animate-fade-in-up">
          <div className="w-20 h-20 bg-gradient-to-br from-[#00D084] to-[#00b86f] rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg shadow-[#00D084]/30">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-3">{t('register.submitted')}</h2>
          <p className="text-gray-600 mb-2">
            {t('register.submittedDesc')}
          </p>
          <p className="text-sm text-gray-500 mb-6">
            {t('register.reviewSentTo')}{formData.contact_email}
          </p>
          <div className="bg-green-50 rounded-xl p-4 mb-6 text-left">
            <p className="text-sm text-green-800">
              <strong>{t('register.friendlyReminder')}</strong>
              <ul className="list-disc list-inside mt-2 space-y-1 text-xs">
                <li>{t('register.reviewTime')}</li>
                <li>{t('register.afterApproval')}</li>
              </ul>
            </p>
          </div>
          <Button onClick={() => router.push('/enterprise/login')} size="lg" className="w-full">
            {t('register.goToLogin')}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF8F5] py-8 md:py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* 简洁标题 */}
        <div className="text-center mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">{t('register.title')}</h1>
          <p className="text-gray-600 text-sm md:text-base">{t('register.subtitle')}</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 md:p-10">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* 企业基本信息 */}
            <div className="border-b border-gray-100 pb-8">
              <h3 className="font-semibold text-gray-900 mb-6 flex items-center gap-3">
                <span className="w-8 h-8 bg-gradient-to-br from-[#00D084] to-[#00b86f] text-white rounded-lg flex items-center justify-center text-sm font-bold shadow-lg shadow-[#00D084]/30">1</span>
                {t('register.basicInfo')}
              </h3>
              <div className="grid sm:grid-cols-2 gap-5">
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('register.nameLabel')}</label>
                  <input
                    type="text"
                    name="company_name"
                    value={formData.company_name}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#00D084] focus:border-transparent transition-all ${errors.company_name ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'}`}
                    placeholder={t('register.namePlaceholder')}
                  />
                  {errors.company_name && <p className="text-red-500 text-xs mt-1">{errors.company_name}</p>}
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('register.creditCodeLabel')}</label>
                  <input
                    type="text"
                    name="unified_social_credit_code"
                    value={formData.unified_social_credit_code}
                    onChange={handleChange}
                    maxLength={18}
                    className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#00D084] focus:border-transparent transition-all ${errors.unified_social_credit_code ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'}`}
                    placeholder={t('register.creditCodePlaceholder')}
                  />
                  {errors.unified_social_credit_code && <p className="text-red-500 text-xs mt-1">{errors.unified_social_credit_code}</p>}
                </div>
              </div>
            </div>

            {/* 联系人信息 */}
            <div className="border-b border-gray-100 pb-8">
              <h3 className="font-semibold text-gray-900 mb-6 flex items-center gap-3">
                <span className="w-8 h-8 bg-gradient-to-br from-[#00D084] to-[#00b86f] text-white rounded-lg flex items-center justify-center text-sm font-bold shadow-lg shadow-[#00D084]/30">2</span>
                {t('register.contactSection')}
              </h3>
              <div className="grid sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('register.contactNameLabel')}</label>
                  <input
                    type="text"
                    name="contact_name"
                    value={formData.contact_name}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#00D084] focus:border-transparent transition-all ${errors.contact_name ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'}`}
                    placeholder={t('register.enterContactName')}
                  />
                  {errors.contact_name && <p className="text-red-500 text-xs mt-1">{errors.contact_name}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('register.contactPhoneLabel')}</label>
                  <input
                    type="tel"
                    name="contact_phone"
                    value={formData.contact_phone}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#00D084] focus:border-transparent transition-all ${errors.contact_phone ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'}`}
                    placeholder={t('register.enterContactPhone')}
                  />
                  {errors.contact_phone && <p className="text-red-500 text-xs mt-1">{errors.contact_phone}</p>}
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('register.contactEmailLabel')}</label>
                  <input
                    type="email"
                    name="contact_email"
                    value={formData.contact_email}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#00D084] focus:border-transparent transition-all ${errors.contact_email ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'}`}
                    placeholder={t('register.contactEmailPlaceholder')}
                  />
                  {errors.contact_email && <p className="text-red-500 text-xs mt-1">{errors.contact_email}</p>}
                </div>
              </div>
            </div>

            {/* 资质文件上传 */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-6 flex items-center gap-3">
                <span className="w-8 h-8 bg-gradient-to-br from-[#00D084] to-[#00b86f] text-white rounded-lg flex items-center justify-center text-sm font-bold shadow-lg shadow-[#00D084]/30">3</span>
                {t('register.fileUploadSection')}
              </h3>
              <p className="text-xs md:text-sm text-gray-500 mb-5">{t('register.fileUploadHint')}</p>

              <div className="grid sm:grid-cols-2 gap-5">
                {/* 营业执照 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">{t('register.licenseLabel')}</label>
                  <div
                    className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 ${
                      files.business_license
                        ? 'border-green-500 bg-green-50'
                        : 'border-gray-200 hover:border-[#00D084] hover:bg-green-50'
                    }`}
                    onClick={() => businessLicenseRef.current?.click()}
                  >
                    <input
                      ref={businessLicenseRef}
                      type="file"
                      accept=".jpg,.jpeg,.png,.pdf"
                      onChange={(e) => handleFileChange(e, 'business_license')}
                      className="hidden"
                    />
                    {files.business_license ? (
                      <div className="animate-fade-in">
                        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                          <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                        <p className="text-sm text-gray-700 font-medium truncate">{files.business_license.name}</p>
                        <p className="text-xs text-gray-400 mt-1">{t('register.clickReupload')}</p>
                      </div>
                    ) : (
                      <div>
                        <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                        </div>
                        <p className="text-sm text-gray-600">{t('register.clickUploadLicense')}</p>
                        <p className="text-xs text-gray-400 mt-1">{t('register.supportedFormats')}</p>
                      </div>
                    )}
                  </div>
                  {errors.business_license && <p className="text-red-500 text-xs mt-2">{errors.business_license}</p>}
                </div>

                {/* 法人身份证 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">{t('register.idLabel')}</label>
                  <div
                    className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 ${
                      files.legal_person_id
                        ? 'border-green-500 bg-green-50'
                        : 'border-gray-200 hover:border-[#00D084] hover:bg-green-50'
                    }`}
                    onClick={() => legalPersonIdRef.current?.click()}
                  >
                    <input
                      ref={legalPersonIdRef}
                      type="file"
                      accept=".jpg,.jpeg,.png,.pdf"
                      onChange={(e) => handleFileChange(e, 'legal_person_id')}
                      className="hidden"
                    />
                    {files.legal_person_id ? (
                      <div className="animate-fade-in">
                        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                          <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                        <p className="text-sm text-gray-700 font-medium truncate">{files.legal_person_id.name}</p>
                        <p className="text-xs text-gray-400 mt-1">{t('register.clickReupload')}</p>
                      </div>
                    ) : (
                      <div>
                        <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                        </div>
                        <p className="text-sm text-gray-600">{t('register.clickUploadId')}</p>
                        <p className="text-xs text-gray-400 mt-1">{t('register.supportedFormats')}</p>
                      </div>
                    )}
                  </div>
                  {errors.legal_person_id && <p className="text-red-500 text-xs mt-2">{errors.legal_person_id}</p>}
                </div>
              </div>
            </div>

            {/* 账户信息 */}
            <div className="border-t border-gray-100 pt-8">
              <h3 className="font-semibold text-gray-900 mb-6 flex items-center gap-3">
                <span className="w-8 h-8 bg-gradient-to-br from-[#00D084] to-[#00b86f] text-white rounded-lg flex items-center justify-center text-sm font-bold shadow-lg shadow-[#00D084]/30">4</span>
                {t('register.accountSection')}
              </h3>
              <div className="grid sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('register.passwordLabel')}</label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#00D084] focus:border-transparent transition-all ${errors.password ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'}`}
                    placeholder={t('register.passwordHint')}
                  />
                  {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password}</p>}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">{t('register.confirmPasswordLabel')}</label>
                  <input
                    type="password"
                    name="confirm_password"
                    value={formData.confirm_password}
                    onChange={handleChange}
                    className={`w-full px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#00D084] focus:border-transparent transition-all ${errors.confirm_password ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:border-gray-300'}`}
                    placeholder={t('register.confirmPasswordPlaceholder')}
                  />
                  {errors.confirm_password && <p className="text-red-500 text-xs mt-1">{errors.confirm_password}</p>}
                </div>
              </div>
            </div>

            {errors.submit && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-5 py-4 rounded-xl text-sm animate-fade-in">
                {errors.submit}
              </div>
            )}

            {/* 提示信息 */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <div className="w-5 h-5 bg-amber-400 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-white text-xs">!</span>
                </div>
                <div className="text-xs text-amber-800">
                  <p className="font-medium mb-1">{t('register.friendlyReminder')}</p>
                  <ul className="list-disc list-inside space-y-0.5">
                    <li>{t('register.reminderNameMatch')}</li>
                    <li>{t('register.reminderClearFiles')}</li>
                    <li>{t('register.reviewTime')}</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button
                type="button"
                variant="outline"
                size="lg"
                onClick={() => router.push('/enterprise/login')}
                className="sm:w-auto"
              >
                {t('register.hasAccount')}
              </Button>
              <Button
                type="submit"
                size="lg"
                disabled={isSubmitting || uploading}
                className="flex-1 shadow-lg shadow-[#00D084]/30"
              >
                {isSubmitting ? t('register.submitting') : t('register.submit')}
              </Button>
            </div>
          </form>

          <p className="text-center text-xs text-gray-400 mt-8">
            {t('register.agreementPrefix')} <span className="text-[#00D084]">{t('register.agreement')}</span> {t('register.agreementAnd')} <span className="text-[#00D084]">{t('register.privacyPolicy')}</span>
          </p>
        </div>
      </div>
    </div>
  );
}
