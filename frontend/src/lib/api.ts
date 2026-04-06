const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

interface RequestOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  timeout?: number;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {}, timeout = 10000 } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    signal: controller.signal,
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, config);
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('请求超时，请检查网络连接');
    }
    throw error;
  }
}

export const api = {
  // 健康检查
  health: () => request<{ status: string }>('/api/v1/health'),

  // Agent 注册和认证
  agents: {
    register: (data: { name: string; type: 'seeker' | 'employer'; platform?: string; contact?: any }) =>
      request<{ success: boolean; data: { agent_id: string; agent_secret: string } }>('/api/v1/agents/register', { method: 'POST', body: data }),
    authenticate: (data: { agent_id: string; timestamp: number; signature: string }) =>
      request<{ success: boolean; data: any }>('/api/v1/agents/authenticate', { method: 'POST', body: data }),
    me: (headers: Record<string, string>) =>
      request<{ success: boolean; data: any }>('/api/v1/agents/me', { headers }),
    list: (params?: { type?: 'seeker' | 'employer'; status?: string; rating?: string; page?: number; page_size?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.type) searchParams.set('type', params.type);
      if (params?.status) searchParams.set('status', params.status);
      if (params?.rating) searchParams.set('rating', params.rating);
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
      const query = searchParams.toString();
      return request<{ success: boolean; data: any[]; total: number }>(`/api/v1/agents${query ? `?${query}` : ''}`);
    },
  },

  // Skill 模板
  templates: {
    list: (params?: { category?: string; page?: number; page_size?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.category) searchParams.set('category', params.category);
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
      const query = searchParams.toString();
      return request<{ success: boolean; data: any[]; total: number }>(`/api/v1/templates${query ? `?${query}` : ''}`);
    },
    get: (id: string) => request<{ success: boolean; data: any }>(`/api/v1/templates/${id}`),
  },

  // 求职者相关 (Profile API)
  profiles: {
    list: (params?: { page?: number; page_size?: number; status?: string; agent_id?: string }) => {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
      if (params?.status) searchParams.set('status', params.status);
      if (params?.agent_id) searchParams.set('agent_id', params.agent_id);
      const query = searchParams.toString();
      return request<{ success: boolean; data: any[]; total: number }>(`/api/v1/profiles${query ? `?${query}` : ''}`);
    },
    get: (id: string) => request<{ success: boolean; data: any }>(`/api/v1/profiles/${id}`),
    create: (data: { profile: any; agent_metadata?: any }) =>
      request<{ success: boolean; data: { profile_id: string } }>('/api/v1/profiles', { method: 'POST', body: data }),
    update: (id: string, data: { profile: any }) =>
      request<{ success: boolean; data: any }>(`/api/v1/profiles/${id}`, { method: 'PUT', body: data }),
    delete: (id: string) => request<{ success: boolean }>(`/api/v1/profiles/${id}`, { method: 'DELETE' }),
  },

  // 职位相关
  jobs: {
    list: (params?: { page?: number; page_size?: number; status?: string; city?: string; enterprise_id?: string; skills?: string; min_salary?: number; max_salary?: number; experience_years?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
      if (params?.status) searchParams.set('status', params.status);
      if (params?.city) searchParams.set('city', params.city);
      if (params?.enterprise_id) searchParams.set('enterprise_id', params.enterprise_id);
      if (params?.skills) searchParams.set('skills', params.skills);
      if (params?.min_salary) searchParams.set('min_salary', params.min_salary.toString());
      if (params?.max_salary) searchParams.set('max_salary', params.max_salary.toString());
      if (params?.experience_years) searchParams.set('experience_years', params.experience_years.toString());
      const query = searchParams.toString();
      return request<{ success: boolean; data: any[]; total: number }>(`/api/v1/jobs${query ? `?${query}` : ''}`);
    },
    get: (id: string) => request<{ success: boolean; data: any }>(`/api/v1/jobs/${id}`),
    create: (data: { job: any; publish_options?: any }) =>
      request<{ success: boolean; data: { job_id: string } }>('/api/v1/jobs', { method: 'POST', body: data }),
    update: (id: string, data: { job: any }) =>
      request<{ success: boolean; data: any }>(`/api/v1/jobs/${id}`, { method: 'PUT', body: data }),
    delete: (id: string) => request<{ success: boolean }>(`/api/v1/jobs/${id}`, { method: 'DELETE' }),
  },

  // 企业相关
  enterprises: {
    apply: (data: { company_name: string; unified_social_credit_code: string; contact: any; company_info?: any; password: string; certification?: any }) =>
      request<{ success: boolean; data: { enterprise_id: string; status: string } }>('/api/v1/enterprise/apply', { method: 'POST', body: data }),
    login: (data: { email: string; password: string }) =>
      request<{ success: boolean; data: any; message?: string }>('/api/v1/enterprise/login', { method: 'POST', body: data }),
    uploadFile: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return fetch(`${API_BASE}/api/v1/enterprise/upload`, {
        method: 'POST',
        body: formData,
      }).then(res => res.json());
    },
    list: (params?: { status?: string; page?: number; page_size?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.set('status', params.status);
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
      const query = searchParams.toString();
      return request<{ success: boolean; data: any[]; total: number }>(`/api/v1/enterprise${query ? `?${query}` : ''}`);
    },
    get: (id: string) => request<{ success: boolean; data: any }>(`/api/v1/enterprise/${id}`),
    getMe: (enterpriseId: string) =>
      request<{ success: boolean; data: any }>('/api/v1/enterprise/me', { headers: { 'X-Enterprise-ID': enterpriseId } }),
    verify: (data: { enterprise_id: string; action: 'approve' | 'reject'; reason?: string }) =>
      request<{ success: boolean; data: any }>('/api/v1/enterprise/verify', { method: 'POST', body: data }),
    createApiKey: (data: { name: string; plan?: string }, enterpriseId: string) =>
      request<{ success: boolean; data: any }>('/api/v1/enterprise/api-keys', {
        method: 'POST',
        body: data,
        headers: { 'X-Enterprise-ID': enterpriseId },
      }),
  },

  // 计费相关
  billing: {
    getRecords: (enterpriseId: string, params?: { start_date?: string; end_date?: string; usage_type?: string; limit?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.start_date) searchParams.set('start_date', params.start_date);
      if (params?.end_date) searchParams.set('end_date', params.end_date);
      if (params?.usage_type) searchParams.set('usage_type', params.usage_type);
      if (params?.limit) searchParams.set('limit', params.limit.toString());
      const query = searchParams.toString();
      return request<{ success: boolean; data: any[]; total: number; current_period_usage: any }>(
        `/api/v1/billing${query ? `?${query}` : ''}`,
        { headers: { 'X-Enterprise-ID': enterpriseId } }
      );
    },
    getStats: (enterpriseId: string) =>
      request<{ success: boolean; data: any }>('/api/v1/billing/stats', { headers: { 'X-Enterprise-ID': enterpriseId } }),
    getPricing: () =>
      request<{ success: boolean; data: any }>('/api/v1/billing/pricing'),
  },

  // 简历解析
  skill: {
    parseResume: (file: File) => {
      const formData = new FormData();
      formData.append('resume_file', file);
      return fetch(`${API_BASE}/api/v1/skill/parse-resume`, {
        method: 'POST',
        body: formData,
      }).then(res => res.json());
    },
    parseIntent: (text: string, type: 'seeker' | 'employer', sessionId: string) =>
      request<{ success: boolean; data: any }>('/api/v1/skill/parse-intent', {
        method: 'POST',
        body: { text, type, session_id: sessionId },
      }),
  },

  // 自主发现 (Agent 自主判断，不依赖平台匹配算法)
  discover: {
    jobs: (params?: { skills?: string; city?: string; min_salary?: number; max_salary?: number; experience_years?: number; limit?: number; offset?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.skills) searchParams.set('skills', params.skills);
      if (params?.city) searchParams.set('city', params.city);
      if (params?.min_salary) searchParams.set('min_salary', params.min_salary.toString());
      if (params?.max_salary) searchParams.set('max_salary', params.max_salary.toString());
      if (params?.experience_years) searchParams.set('experience_years', params.experience_years.toString());
      if (params?.limit) searchParams.set('limit', params.limit.toString());
      if (params?.offset) searchParams.set('offset', params.offset.toString());
      const query = searchParams.toString();
      return request<{ success: boolean; data: any[]; total: number }>(`/api/v1/discover/jobs${query ? `?${query}` : ''}`);
    },
    profiles: (params?: { skills?: string; city?: string; min_experience?: number; max_salary_expectation?: number; limit?: number; offset?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.skills) searchParams.set('skills', params.skills);
      if (params?.city) searchParams.set('city', params.city);
      if (params?.min_experience) searchParams.set('min_experience', params.min_experience.toString());
      if (params?.max_salary_expectation) searchParams.set('max_salary_expectation', params.max_salary_expectation.toString());
      if (params?.limit) searchParams.set('limit', params.limit.toString());
      if (params?.offset) searchParams.set('offset', params.offset.toString());
      const query = searchParams.toString();
      return request<{ success: boolean; data: any[]; total: number }>(`/api/v1/discover/profiles${query ? `?${query}` : ''}`);
    },
  },

  // 数据导出
  export: {
    profileJson: (profileId: string, includeResume: boolean = true) =>
      `${API_BASE}/api/v1/export/profiles/${profileId}?include_resume=${includeResume}`,
    profilePdf: (profileId: string) =>
      `${API_BASE}/api/v1/export/profiles/${profileId}/pdf`,
    resumeJson: (resumeId: string) =>
      `${API_BASE}/api/v1/export/resumes/${resumeId}`,
    resumePdf: (resumeId: string) =>
      `${API_BASE}/api/v1/export/resumes/${resumeId}/pdf`,
    profileHistory: (profileId: string, limit: number = 10) =>
      request<{ success: boolean; data: any }>(`/api/v1/export/history/profiles/${profileId}?limit=${limit}`),
  },
};
