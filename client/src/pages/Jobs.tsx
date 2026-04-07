import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi, Job } from '../lib/api'
import { Plus, Search, Edit2, Trash2, X } from 'lucide-react'

export default function Jobs() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingJob, setEditingJob] = useState<Job | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    department: '',
    description: '',
  })

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => jobsApi.list(),
  })

  const createMutation = useMutation({
    mutationFn: jobsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      setShowForm(false)
      setFormData({ title: '', department: '', description: '' })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Job> }) => jobsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      setEditingJob(null)
      setFormData({ title: '', department: '', description: '' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: jobsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingJob) {
      updateMutation.mutate({ id: editingJob.id, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleEdit = (job: Job) => {
    setEditingJob(job)
    setFormData({
      title: job.title,
      department: job.department || '',
      description: job.description || '',
    })
    setShowForm(true)
  }

  const handleDelete = (id: number) => {
    if (confirm('确定要删除该岗位吗？')) {
      deleteMutation.mutate(id)
    }
  }

  if (isLoading) {
    return <div className="flex justify-center py-8"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div></div>
  }

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <h1 className="text-xl font-bold text-gray-900">岗位管理</h1>
        <button onClick={() => setShowForm(true)} className="btn btn-primary flex items-center justify-center">
          <Plus className="w-4 h-4 mr-2" />新建岗位
        </button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="font-semibold">{editingJob ? '编辑岗位' : '新建岗位'}</h2>
              <button onClick={() => { setShowForm(false); setEditingJob(null) }} className="text-gray-400">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">岗位名称 *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">部门</label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">岗位描述</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input min-h-[100px]"
                  rows={4}
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => { setShowForm(false); setEditingJob(null) }}
                  className="flex-1 btn btn-secondary"
                >
                  取消
                </button>
                <button type="submit" className="flex-1 btn btn-primary">
                  {editingJob ? '保存' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Job List */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {jobs?.data?.map((job) => (
          <div key={job.id} className="card">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{job.title}</h3>
                {job.department && (
                  <p className="text-sm text-gray-500 mt-1">{job.department}</p>
                )}
              </div>
              <div className="flex gap-2">
                <button onClick={() => handleEdit(job)} className="text-gray-400 hover:text-primary-600">
                  <Edit2 className="w-4 h-4" />
                </button>
                <button onClick={() => handleDelete(job.id)} className="text-gray-400 hover:text-red-600">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
            {job.description && (
              <p className="text-sm text-gray-600 mt-2 line-clamp-2">{job.description}</p>
            )}
            <div className="mt-3 flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${job.is_active ? 'bg-green-500' : 'bg-gray-300'}`}></span>
              <span className="text-xs text-gray-500">{job.is_active ? '启用中' : '已禁用'}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Empty state */}
      {jobs?.data?.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>暂无岗位数据</p>
          <button onClick={() => setShowForm(true)} className="mt-4 btn btn-primary">
            创建第一个岗位
          </button>
        </div>
      )}
    </div>
  )
}