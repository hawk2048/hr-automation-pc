import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { candidatesApi, Candidate, filesApi } from '../lib/api'
import { Plus, Search, Mail, Phone, MapPin, X, Upload, Loader2 } from 'lucide-react'

export default function Candidates() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [showForm, setShowForm] = useState(false)
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [parsing, setParsing] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    location: '',
  })

  const { data: candidates, isLoading } = useQuery({
    queryKey: ['candidates'],
    queryFn: () => candidatesApi.list(),
  })

  const createMutation = useMutation({
    mutationFn: candidatesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] })
      setShowForm(false)
      setFormData({ name: '', email: '', phone: '', location: '' })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  // Handle file upload and parse
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setParsing(true)
    try {
      const result = await filesApi.parseResumeFile(file)
      if (result.data?.success) {
        const parsed = result.data.data
        // Auto-fill form with parsed data
        setFormData({
          name: parsed.name || '',
          email: parsed.email || '',
          phone: parsed.phone || '',
          location: parsed.location || '',
        })
        // Show success message and open form
        setShowForm(true)
      }
    } catch (err) {
      console.error('Parse failed:', err)
    } finally {
      setParsing(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  // Filter candidates
  const filteredCandidates = candidates?.data?.filter(c => 
    searchQuery ? c.name.includes(searchQuery) || c.email?.includes(searchQuery) : true
  ) || []

  if (isLoading) {
    return <div className="flex justify-center py-8"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div></div>
  }

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <h1 className="text-xl font-bold text-gray-900">人才库</h1>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="搜索人才..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10 w-48"
            />
          </div>
          
          {/* Resume Upload */}
          <div className="relative">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={parsing}
              className="btn btn-secondary flex items-center"
            >
              {parsing ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Upload className="w-4 h-4 mr-2" />
              )}
              解析简历
            </button>
          </div>
          
          <button onClick={() => setShowForm(true)} className="btn btn-primary flex items-center">
            <Plus className="w-4 h-4 mr-2" />添加人才
          </button>
        </div>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-lg">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="font-semibold">添加人才</h2>
              <button onClick={() => setShowForm(false)} className="text-gray-400">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">姓名 *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">电话</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">地点</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="input"
                />
              </div>
              <div className="flex gap-3">
                <button type="button" onClick={() => setShowForm(false)} className="flex-1 btn btn-secondary">
                  取消
                </button>
                <button type="submit" className="flex-1 btn btn-primary">
                  添加
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedCandidate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-white">
              <h2 className="font-semibold">{selectedCandidate.name}</h2>
              <button onClick={() => setSelectedCandidate(null)} className="text-gray-400">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              {/* Contact */}
              <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                {selectedCandidate.email && (
                  <div className="flex items-center">
                    <Mail className="w-4 h-4 mr-2" />
                    {selectedCandidate.email}
                  </div>
                )}
                {selectedCandidate.phone && (
                  <div className="flex items-center">
                    <Phone className="w-4 h-4 mr-2" />
                    {selectedCandidate.phone}
                  </div>
                )}
                {selectedCandidate.location && (
                  <div className="flex items-center">
                    <MapPin className="w-4 h-4 mr-2" />
                    {selectedCandidate.location}
                  </div>
                )}
              </div>

              {/* Education */}
              {selectedCandidate.education?.length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">教育背景</h3>
                  <div className="space-y-2">
                    {selectedCandidate.education.map((edu, i) => (
                      <div key={i} className="text-sm">
                        <p className="font-medium">{edu.degree} - {edu.major}</p>
                        <p className="text-gray-500">{edu.school} {edu.year && `(${edu.year})`}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Work Experience */}
              {selectedCandidate.work_experience?.length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">工作经历</h3>
                  <div className="space-y-3">
                    {selectedCandidate.work_experience.map((exp, i) => (
                      <div key={i} className="text-sm">
                        <p className="font-medium">{exp.role}</p>
                        <p className="text-gray-500">{exp.company} {exp.industry && `(${exp.industry})`}</p>
                        {exp.duration_months && (
                          <p className="text-gray-400">{Math.round(exp.duration_months / 12)} 年</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Skills */}
              {selectedCandidate.skills && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">技能</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedCandidate.skills.hard_skills?.map((s: any, i: number) => (
                      <span key={i} className="px-2 py-1 bg-primary-50 text-primary-700 rounded text-sm">
                        {s.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Status */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">状态:</span>
                <span className="px-2 py-1 bg-gray-100 rounded text-sm">
                  {selectedCandidate.status === 'new' ? '新简历' : 
                   selectedCandidate.status === 'interview' ? '面试中' :
                   selectedCandidate.status === 'offer' ? '待入职' :
                   selectedCandidate.status === 'hired' ? '已入职' : '已淘汰'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Candidate List */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredCandidates.map((candidate) => (
          <div 
            key={candidate.id} 
            className="card cursor-pointer hover:border-primary-300"
            onClick={() => setSelectedCandidate(candidate)}
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-gray-900">{candidate.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{candidate.location || '未填写地点'}</p>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-2 text-sm text-gray-500">
              {candidate.email && (
                <span className="flex items-center">
                  <Mail className="w-3 h-3 mr-1" />
                </span>
              )}
              {candidate.education?.[0] && (
                <span className="px-2 py-0.5 bg-gray-100 rounded">
                  {candidate.education[0].degree}
                </span>
              )}
            </div>
            <div className="mt-3 flex items-center justify-between">
              <span className={`text-xs px-2 py-1 rounded ${
                candidate.status === 'new' ? 'bg-blue-100 text-blue-700' :
                candidate.status === 'interview' ? 'bg-yellow-100 text-yellow-700' :
                candidate.status === 'offer' ? 'bg-green-100 text-green-700' :
                candidate.status === 'rejected' ? 'bg-red-100 text-red-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {candidate.status === 'new' ? '新简历' : 
                 candidate.status === 'interview' ? '面试中' :
                 candidate.status === 'offer' ? '待入职' :
                 candidate.status === 'hired' ? '已入职' : 
                 candidate.status === 'rejected' ? '已淘汰' : candidate.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Empty state */}
      {filteredCandidates.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>暂无人才数据</p>
          <button onClick={() => setShowForm(true)} className="mt-4 btn btn-primary">
            添加第一批人才
          </button>
        </div>
      )}
    </div>
  )
}