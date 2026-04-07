/** API Client */
import axios, { AxiosError, AxiosRequestConfig } from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API methods
export const apiClient = {
  get: <T>(url: string, config?: AxiosRequestConfig) =>
    api.get<T>(url, config),
  
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    api.post<T>(url, data, config),
  
  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    api.patch<T>(url, data, config),
  
  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    api.put<T>(url, data, config),
  
  delete: <T>(url: string, config?: AxiosRequestConfig) =>
    api.delete<T>(url, config),
}

// Auth API
export const authApi = {
  login: (username: string, password: string) =>
    apiClient.post<{ access_token: string }>('/auth/login', { username, password }),
  
  register: (data: { username: string; password: string; email?: string; full_name?: string }) =>
    apiClient.post('/auth/register', data),
  
  me: () => apiClient.get('/auth/me'),
}

// Jobs API
export const jobsApi = {
  list: (active_only = true) =>
    apiClient.get<Job[]>('/jobs/', { params: { active_only } }),
  
  get: (id: number) => apiClient.get<Job>(`/jobs/${id}`),
  
  create: (data: Partial<Job>) => apiClient.post<Job>('/jobs/', data),
  
  update: (id: number, data: Partial<Job>) => apiClient.patch<Job>(`/jobs/${id}`, data),
  
  delete: (id: number) => apiClient.delete(`/jobs/${id}`),
}

// Candidates API
export const candidatesApi = {
  list: (status?: string, limit = 100) =>
    apiClient.get<Candidate[]>('/candidates/', { params: { status, limit } }),
  
  get: (id: number) => apiClient.get<Candidate>(`/candidates/${id}`),
  
  create: (data: Partial<Candidate>) => apiClient.post<Candidate>('/candidates/', data),
  
  update: (id: number, data: Partial<Candidate>) => apiClient.patch<Candidate>(`/candidates/${id}`, data),
  
  delete: (id: number) => apiClient.delete(`/candidates/${id}`),
}

// Matches API
export const matchesApi = {
  runMatch: (jobId: number, topN = 20) =>
    apiClient.post(`/matches/${jobId}/match`, null, { params: { top_n: topN } }),

  getResults: (jobId: number, status?: string) =>
    apiClient.get<MatchResult[]>(`/matches/${jobId}/results`, { params: { status } }),

  getResult: (id: number) => apiClient.get<MatchResult>(`/matches/result/${id}`),

  updateStatus: (id: number, status: string) =>
    apiClient.patch(`/matches/${id}/status`, { status }),
}

// Screening API
export interface ScreeningCriteria {
  min_total_score: number
  min_skill_score: number
  min_experience_score: number
  min_education_score: number
  exclude_rejected: boolean
  use_llm_evaluation: boolean
}

export interface ScreeningResult {
  match_id: number
  candidate_id: number
  candidate_name: string
  total_score: number
  passed: boolean
  reasons: string[]
  llm_evaluation?: {
    technical_score: number
    experience_score: number
    education_score: number
    cultural_fit_score: number
    overall_recommendation: string
    strengths: string[]
    concerns: string[]
    interview_focus: string[]
    summary: string
  }
  interview_questions?: {
    type: string
    question: string
    purpose: string
    follow_up: string
  }[]
}

export interface ScreeningStats {
  total: number
  pending: number
  accepted: number
  rejected: number
  excellent: number
  good: number
  fair: number
  poor: number
  pass_rate: number
}

export interface ScreeningResponse {
  job_id: number
  total: number
  passed: number
  failed: number
  results: ScreeningResult[]
}

export const screeningApi = {
  screen: (jobId: number, criteria?: Partial<ScreeningCriteria>, candidateIds?: number[]) =>
    apiClient.post<ScreeningResponse>(`/screening/${jobId}/screen`, criteria, {
      params: candidateIds ? { candidate_ids: candidateIds } : undefined,
    }),

  getStats: (jobId: number) =>
    apiClient.get<ScreeningStats>(`/screening/${jobId}/stats`),

  batchAccept: (jobId: number, matchIds: number[], targetStatus = "screening") =>
    apiClient.post(`/screening/${jobId}/accept`, { match_ids: matchIds, target_status: targetStatus }),

  batchReject: (jobId: number, matchIds: number[]) =>
    apiClient.post(`/screening/${jobId}/reject`, { match_ids: matchIds }),

  filterExcellent: (jobId: number, threshold = 0.8) =>
    apiClient.post(`/screening/${jobId}/filter-excellent`, null, { params: { threshold } }),
}

// Settings API (LLM Configuration)
export interface LLMConfig {
  provider: string
  model: string
  base_url: string
  remote_model: string
  embedding_model: string
}

export interface LLMHealth {
  status: string
  provider?: string
  available_models?: string[]
  current_model?: string
  message?: string
}

export const settingsApi = {
  getLLMConfig: () => apiClient.get<LLMConfig>('/settings/llm'),

  updateLLMConfig: (config: {
    provider?: string
    model?: string
    base_url?: string
    api_key?: string
    api_base?: string
    remote_model?: string
    embedding_model?: string
  }) => apiClient.post('/settings/llm', config),

  checkLLMHealth: () => apiClient.get<LLMHealth>('/settings/llm/health'),

  listLLMModels: () => apiClient.get<{ models: string[] }>('/settings/llm/models'),

  listEmbeddingModels: () =>
    apiClient.get<{ models: string[]; recommended: string }>('/settings/embedding/models'),
}

// Files API (Resume parsing)
export interface ParsedResume {
  name: string
  email?: string
  phone?: string
  age?: number
  gender?: string
  location?: string
  education: { degree: string; university: string; major?: string }[]
  work_experience: { duration?: string; company?: string; title?: string }[]
  skills: { hard_skills: { name: string; level: string }[]; soft_skills: { name: string; level: string }[] }
  experience_years?: number
  resume_text: string
}

export const filesApi = {
  uploadResume: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post<{ filename: string; file_path: string; size: number }>(
      '/files/resume',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  },

  parseResumeFile: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post<{ success: boolean; data: ParsedResume }>(
      '/files/parse',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  },

  parseResumeText: (candidateId: number, resumeText: string) =>
    apiClient.post<{ success: boolean; parsed_fields: Record<string, unknown> }>(
      '/files/parse-resume',
      null,
      { params: { candidate_id: candidateId, resume_text: resumeText } }
    ),
}

// Types
export interface Job {
  id: number
  title: string
  department?: string
  description?: string
  qualifications?: Record<string, unknown>
  skills?: Record<string, unknown>
  competencies: string[]
  responsibilities: string[]
  environment?: Record<string, unknown>
  weights?: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Candidate {
  id: number
  name: string
  email?: string
  phone?: string
  location?: string
  education: Education[]
  work_experience: WorkExperience[]
  skills?: Record<string, unknown>
  salary_expectation?: { min: number; max: number }
  availability?: string
  status: string
  created_at: string
  updated_at: string
}

export interface Education {
  degree: string
  major: string
  school: string
  year?: number
}

export interface WorkExperience {
  company: string
  industry?: string
  role: string
  duration_months?: number
  responsibilities: string[]
  achievements: string[]
  skills_used: string[]
}

export interface MatchResult {
  id: number
  job_id: number
  candidate_id: number
  total_score: number
  skill_score: number
  experience_score: number
  semantic_score: number
  education_score: number
  salary_score: number
  soft_skill_score: number
  llm_analysis?: string
  status: string
  created_at: string
  candidate_name?: string
  candidate_location?: string
  candidate?: Candidate
}

export default apiClient