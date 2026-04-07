import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi, matchesApi, screeningApi, MatchResult } from '../lib/api'
import { Play, Check, XCircle, Clock, Filter, Users, CheckSquare, Square, X } from 'lucide-react'

export default function Matches() {
  const queryClient = useQueryClient()
  const [selectedJob, setSelectedJob] = useState<number | null>(null)
  const [selectedMatch, setSelectedMatch] = useState<MatchResult | null>(null)
  
  // Screening state
  const [showScreening, setShowScreening] = useState(false)
  const [selectedMatches, setSelectedMatches] = useState<number[]>([])
  const [screeningCriteria, setScreeningCriteria] = useState({
    min_total_score: 0.5,
    min_skill_score: 0.4,
    min_experience_score: 0.3,
    min_education_score: 0.3,
  })

  const { data: jobs } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => jobsApi.list(),
  })

  const { data: matchResults, isLoading } = useQuery({
    queryKey: ['matches', selectedJob],
    queryFn: () => selectedJob ? matchesApi.getResults(selectedJob) : Promise.resolve({ data: [] }),
    enabled: !!selectedJob,
  })

  const { data: screeningStats } = useQuery({
    queryKey: ['screeningStats', selectedJob],
    queryFn: () => selectedJob ? screeningApi.getStats(selectedJob) : Promise.resolve({ data: {} }),
    enabled: !!selectedJob,
  })

  const runMatchMutation = useMutation({
    mutationFn: ({ jobId, topN = 20 }: { jobId: number; topN?: number }) => 
      matchesApi.runMatch(jobId, topN),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
    },
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => 
      matchesApi.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
      queryClient.invalidateQueries({ queryKey: ['screeningStats'] })
    },
  })

  const screenMutation = useMutation({
    mutationFn: ({ jobId, criteria }: { jobId: number; criteria?: any }) =>
      screeningApi.screen(jobId, criteria),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
      queryClient.invalidateQueries({ queryKey: ['screeningStats'] })
    },
  })

  const batchAcceptMutation = useMutation({
    mutationFn: ({ jobId, matchIds }: { jobId: number; matchIds: number[] }) =>
      screeningApi.batchAccept(jobId, matchIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
      queryClient.invalidateQueries({ queryKey: ['screeningStats'] })
      setSelectedMatches([])
    },
  })

  const batchRejectMutation = useMutation({
    mutationFn: ({ jobId, matchIds }: { jobId: number; matchIds: number[] }) =>
      screeningApi.batchReject(jobId, matchIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['matches'] })
      queryClient.invalidateQueries({ queryKey: ['screeningStats'] })
      setSelectedMatches([])
    },
  })

  const handleRunMatch = (jobId: number) => {
    runMatchMutation.mutate({ jobId })
    setSelectedJob(jobId)
  }

  const handleUpdateStatus = (id: number, status: string) => {
    updateStatusMutation.mutate({ id, status })
  }

  const handleRunScreening = () => {
    if (selectedJob) {
      screenMutation.mutate({ 
        jobId: selectedJob, 
        criteria: screeningCriteria 
      })
    }
  }

  const handleBatchAccept = () => {
    if (selectedJob && selectedMatches.length > 0) {
      batchAcceptMutation.mutate({ jobId: selectedJob, matchIds: selectedMatches })
    }
  }

  const handleBatchReject = () => {
    if (selectedJob && selectedMatches.length > 0) {
      batchRejectMutation.mutate({ jobId: selectedJob, matchIds: selectedMatches })
    }
  }

  const toggleSelectAll = () => {
    if (selectedMatches.length === matchResults?.data?.length) {
      setSelectedMatches([])
    } else {
      setSelectedMatches(matchResults?.data?.map((m: MatchResult) => m.id) || [])
    }
  }

  const toggleSelect = (id: number) => {
    if (selectedMatches.includes(id)) {
      setSelectedMatches(selectedMatches.filter(m => m !== id))
    } else {
      setSelectedMatches([...selectedMatches, id])
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50'
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <h1 className="text-xl font-bold text-gray-900">智能匹配</h1>
        {selectedJob && (
          <button
            onClick={() => setShowScreening(!showScreening)}
            className={`btn ${showScreening ? 'btn-primary' : 'btn-secondary'} flex items-center`}
          >
            <Filter className="w-4 h-4 mr-2" />
            批量初筛
          </button>
        )}
      </div>

      {/* Job selector */}
      <div className="card mb-6">
        <h2 className="font-medium mb-3">选择岗位</h2>
        <div className="flex flex-wrap gap-3">
          {jobs?.data?.map((job) => (
            <button
              key={job.id}
              onClick={() => { setSelectedJob(job.id); setSelectedMatches([]) }}
              className={`px-4 py-2 rounded-lg border transition-colors ${
                selectedJob === job.id
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              {job.title}
            </button>
          ))}
        </div>
        {jobs?.data?.length === 0 && (
          <p className="text-gray-500 text-sm mt-2">请先创建岗位</p>
        )}
      </div>

      {/* Screening panel */}
      {showScreening && selectedJob && (
        <div className="card mb-6 bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-medium text-blue-900">批量初筛设置</h2>
            <button onClick={() => setShowScreening(false)} className="text-gray-400 hover:text-gray-600">
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* Stats */}
          {screeningStats?.data && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
              <div className="bg-white rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-gray-900">{screeningStats.data.total || 0}</p>
                <p className="text-sm text-gray-500">总人数</p>
              </div>
              <div className="bg-white rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-green-600">{screeningStats.data.excellent || 0}</p>
                <p className="text-sm text-gray-500">优秀 (≥80%)</p>
              </div>
              <div className="bg-white rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-yellow-600">{screeningStats.data.good || 0}</p>
                <p className="text-sm text-gray-500">良好 (60-80%)</p>
              </div>
              <div className="bg-white rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-red-600">{screeningStats.data.rejected || 0}</p>
                <p className="text-sm text-gray-500">已拒绝</p>
              </div>
            </div>
          )}

          {/* Criteria */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">综合分数 ≥</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={screeningCriteria.min_total_score}
                onChange={e => setScreeningCriteria({...screeningCriteria, min_total_score: parseFloat(e.target.value) || 0})}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">技能分数 ≥</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={screeningCriteria.min_skill_score}
                onChange={e => setScreeningCriteria({...screeningCriteria, min_skill_score: parseFloat(e.target.value) || 0})}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">经验分数 ≥</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={screeningCriteria.min_experience_score}
                onChange={e => setScreeningCriteria({...screeningCriteria, min_experience_score: parseFloat(e.target.value) || 0})}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">学历分数 ≥</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={screeningCriteria.min_education_score}
                onChange={e => setScreeningCriteria({...screeningCriteria, min_education_score: parseFloat(e.target.value) || 0})}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleRunScreening}
              disabled={screenMutation.isPending}
              className="btn btn-primary flex items-center"
            >
              <Filter className="w-4 h-4 mr-2" />
              {screenMutation.isPending ? '筛选中...' : '执行初筛'}
            </button>
            
            {selectedMatches.length > 0 && (
              <>
                <button
                  onClick={handleBatchAccept}
                  disabled={batchAcceptMutation.isPending}
                  className="btn bg-green-600 text-white hover:bg-green-700 flex items-center"
                >
                  <Check className="w-4 h-4 mr-2" />
                  批量通过 ({selectedMatches.length})
                </button>
                <button
                  onClick={handleBatchReject}
                  disabled={batchRejectMutation.isPending}
                  className="btn bg-red-600 text-white hover:bg-red-700 flex items-center"
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  批量拒绝 ({selectedMatches.length})
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Run match button */}
      {selectedJob && !showScreening && (
        <div className="card mb-6">
          <button
            onClick={() => handleRunMatch(selectedJob)}
            disabled={runMatchMutation.isPending}
            className="btn btn-primary flex items-center"
          >
            <Play className="w-4 h-4 mr-2" />
            {runMatchMutation.isPending ? '匹配中...' : '运行匹配'}
          </button>
          <p className="text-sm text-gray-500 mt-2">
            点击后系统将根据岗位要求对人才库中的候选人进行智能评分匹配
          </p>
        </div>
      )}

      {/* Match results */}
      {selectedJob && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-medium">匹配结果</h2>
            {showScreening && matchResults?.data?.length > 0 && (
              <button
                onClick={toggleSelectAll}
                className="flex items-center text-sm text-gray-600 hover:text-gray-900"
              >
                {selectedMatches.length === matchResults.data.length ? (
                  <><CheckSquare className="w-4 h-4 mr-1" /> 取消全选</>
                ) : (
                  <><Square className="w-4 h-4 mr-1" /> 全选</>
                )}
              </button>
            )}
          </div>
          
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : (
            <div className="space-y-3">
              {matchResults?.data?.map((result) => (
                <div 
                  key={result.id} 
                  className={`flex flex-col sm:flex-row sm:items-center gap-4 p-4 border rounded-lg hover:bg-gray-50 ${
                    result.status === 'accepted' ? 'bg-green-50 border-green-200' :
                    result.status === 'rejected' ? 'bg-red-50 border-red-200' : ''
                  }`}
                >
                  {/* Selection checkbox */}
                  {showScreening && (
                    <div className="flex-shrink-0">
                      <button
                        onClick={() => toggleSelect(result.id)}
                        className={`p-1 rounded ${selectedMatches.includes(result.id) ? 'text-blue-600' : 'text-gray-400'}`}
                      >
                        {selectedMatches.includes(result.id) ? 
                          <CheckSquare className="w-5 h-5" /> : 
                          <Square className="w-5 h-5" />
                        }
                      </button>
                    </div>
                  )}

                  {/* Score */}
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold ${getScoreColor(result.total_score)}`}>
                      {Math.round(result.total_score * 100)}
                    </div>
                    <div>
                      <h3 className="font-medium">{result.candidate_name}</h3>
                      <p className="text-sm text-gray-500">{result.candidate_location || '未填写地点'}</p>
                    </div>
                  </div>

                  {/* Score breakdown */}
                  <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm">
                    <div>
                      <span className="text-gray-500">技能</span>
                      <p className="font-medium">{Math.round(result.skill_score * 100)}%</p>
                    </div>
                    <div>
                      <span className="text-gray-500">经验</span>
                      <p className="font-medium">{Math.round(result.experience_score * 100)}%</p>
                    </div>
                    <div>
                      <span className="text-gray-500">学历</span>
                      <p className="font-medium">{Math.round(result.education_score * 100)}%</p>
                    </div>
                    <div>
                      <span className="text-gray-500">语义</span>
                      <p className="font-medium">{Math.round(result.semantic_score * 100)}%</p>
                    </div>
                  </div>

                  {/* Status badge */}
                  <div className="flex items-center gap-2">
                    {result.status === 'pending' && <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">待处理</span>}
                    {result.status === 'accepted' && <span className="px-2 py-1 bg-green-100 text-green-600 text-xs rounded">已通过</span>}
                    {result.status === 'rejected' && <span className="px-2 py-1 bg-red-100 text-red-600 text-xs rounded">已拒绝</span>}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleUpdateStatus(result.id, 'accepted')}
                      disabled={result.status !== 'pending'}
                      className="p-2 text-green-600 hover:bg-green-50 rounded disabled:opacity-50"
                      title="通过"
                    >
                      <Check className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(result.id, 'rejected')}
                      disabled={result.status !== 'pending'}
                      className="p-2 text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
                      title="拒绝"
                    >
                      <XCircle className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => setSelectedMatch(result)}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                      title="详情"
                    >
                      查看
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {matchResults?.data?.length === 0 && (
            <p className="text-center py-8 text-gray-500">暂无匹配结果，请先运行匹配</p>
          )}
        </div>
      )}

      {/* Match detail modal */}
      {selectedMatch && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-white">
              <h2 className="font-semibold">匹配详情</h2>
              <button onClick={() => setSelectedMatch(null)} className="text-gray-400">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <h3 className="font-medium text-gray-900">{selectedMatch.candidate_name}</h3>
                <p className="text-sm text-gray-500">{selectedMatch.candidate_location}</p>
              </div>

              {/* Scores */}
              <div>
                <h4 className="font-medium mb-2">综合评分</h4>
                <div className={`text-3xl font-bold ${getScoreColor(selectedMatch.total_score)} p-4 rounded-lg`}>
                  {Math.round(selectedMatch.total_score * 100)}分
                </div>
              </div>

              {/* Score breakdown */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-sm text-gray-500">技能匹配</p>
                  <p className="text-xl font-bold">{Math.round(selectedMatch.skill_score * 100)}%</p>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-sm text-gray-500">经验匹配</p>
                  <p className="text-xl font-bold">{Math.round(selectedMatch.experience_score * 100)}%</p>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-sm text-gray-500">学历匹配</p>
                  <p className="text-xl font-bold">{Math.round(selectedMatch.education_score * 100)}%</p>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <p className="text-sm text-gray-500">语义匹配</p>
                  <p className="text-xl font-bold">{Math.round(selectedMatch.semantic_score * 100)}%</p>
                </div>
              </div>

              {/* Candidate details */}
              {selectedMatch.candidate && (
                <div>
                  <h4 className="font-medium mb-2">候选人详情</h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>邮箱: {selectedMatch.candidate.email || '-'}</p>
                    <p>电话: {selectedMatch.candidate.phone || '-'}</p>
                    <p>期望薪资: {selectedMatch.candidate.salary_expectation?.min}k - {selectedMatch.candidate.salary_expectation?.max}k</p>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-4 border-t">
                {selectedMatch.status === 'pending' && (
                  <>
                    <button
                      onClick={() => { handleUpdateStatus(selectedMatch.id, 'accepted'); setSelectedMatch(null) }}
                      className="flex-1 btn bg-green-600 text-white hover:bg-green-700"
                    >
                      通过
                    </button>
                    <button
                      onClick={() => { handleUpdateStatus(selectedMatch.id, 'rejected'); setSelectedMatch(null) }}
                      className="flex-1 btn bg-red-600 text-white hover:bg-red-700"
                    >
                      拒绝
                    </button>
                  </>
                )}
                {selectedMatch.status !== 'pending' && (
                  <button onClick={() => setSelectedMatch(null)} className="w-full btn btn-secondary">
                    关闭
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}