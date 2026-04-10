import { useState, useEffect } from 'react'
import { settingsApi, LLMConfig, LLMHealth } from '../lib/api'

interface SettingsPageProps {
  onError?: (msg: string) => void
}

export function SettingsPage({ onError }: SettingsPageProps) {
  const [config, setConfig] = useState<LLMConfig | null>(null)
  const [health, setHealth] = useState<LLMHealth | null>(null)
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [embeddingModels, setEmbeddingModels] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<'llm' | 'embedding'>('llm')

  // Form state
  const [provider, setProvider] = useState('ollama')
  const [llmModel, setLlmModel] = useState('')
  const [llmBaseUrl, setLlmBaseUrl] = useState('http://localhost:11434')
  const [remoteModel, setRemoteModel] = useState('gpt-4o-mini')
  const [remoteApiKey, setRemoteApiKey] = useState('')
  const [remoteApiBase, setRemoteApiBase] = useState('https://api.openai.com/v1')
  const [embeddingModel, setEmbeddingModel] = useState('bge-large-zh-v1.5')

  useEffect(() => {
    loadConfig()
  }, [])

  async function loadConfig() {
    try {
      setLoading(true)
      const [configData, healthData, modelsData, embedData] = await Promise.all([
        settingsApi.getLLMConfig(),
        settingsApi.checkLLMHealth(),
        settingsApi.listLLMModels(),
        settingsApi.listEmbeddingModels(),
      ])

      setConfig(configData)
      setHealth(healthData)
      setAvailableModels(modelsData.models)
      setEmbeddingModels(embedData.models)

      // Set form values
      setProvider(configData.provider)
      setLlmBaseUrl(configData.base_url)
      setLlmModel(configData.model)
      setRemoteModel(configData.remote_model)
      setEmbeddingModel(configData.embedding_model)
    } catch (err: any) {
      onError?.(err.response?.data?.detail || 'Failed to load settings')
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    try {
      setSaving(true)
      await settingsApi.updateLLMConfig({
        provider,
        model: provider === 'ollama' ? llmModel : undefined,
        base_url: provider === 'ollama' ? llmBaseUrl : undefined,
        remote_model: provider === 'remote' ? remoteModel : undefined,
        api_key: provider === 'remote' ? remoteApiKey : undefined,
        api_base: provider === 'remote' ? remoteApiBase : undefined,
        embedding_model: embeddingModel,
      })
      await loadConfig()
      onError?.('Settings saved successfully!')
    } catch (err: any) {
      onError?.(err.response?.data?.detail || 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  async function handleTestConnection() {
    try {
      const healthData = await settingsApi.checkLLMHealth()
      setHealth(healthData)
      if (healthData.status === 'ok') {
        onError?.('Connection successful!')
      } else {
        onError?.(healthData.message || 'Connection failed')
      }
    } catch (err: any) {
      onError?.('Connection test failed')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">System Settings</h1>

      {/* Health Status */}
      {health && (
        <div
          className={`p-4 rounded-lg mb-6 ${
            health.status === 'ok' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}
        >
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                health.status === 'ok' ? 'bg-green-500' : 'bg-red-500'
              }`}
            ></span>
            <span className="font-medium">
              LLM Status: {health.status === 'ok' ? 'Connected' : 'Disconnected'}
            </span>
            {health.current_model && (
              <span className="text-sm text-gray-600 ml-2">
                Current: {health.current_model}
              </span>
            )}
          </div>
          {health.available_models && health.available_models.length > 0 && (
            <p className="text-sm text-gray-600 mt-1">
              Available: {health.available_models.slice(0, 5).join(', ')}
              {health.available_models.length > 5 && '...'}
            </p>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          onClick={() => setActiveTab('llm')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeTab === 'llm'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          LLM Model
        </button>
        <button
          onClick={() => setActiveTab('embedding')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeTab === 'embedding'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Embedding Model
        </button>
      </div>

      {/* LLM Tab */}
      {activeTab === 'llm' && (
        <div className="space-y-6">
          {/* Provider Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              LLM Provider
            </label>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="provider"
                  value="ollama"
                  checked={provider === 'ollama'}
                  onChange={(e) => setProvider(e.target.value)}
                  className="mr-2"
                />
                <span className="text-sm">Local (Ollama)</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="provider"
                  value="remote"
                  checked={provider === 'remote'}
                  onChange={(e) => setProvider(e.target.value)}
                  className="mr-2"
                />
                <span className="text-sm">Remote API (OpenAI-compatible)</span>
              </label>
            </div>
          </div>

          {/* Ollama Settings */}
          {provider === 'ollama' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ollama URL
                </label>
                <input
                  type="text"
                  value={llmBaseUrl}
                  onChange={(e) => setLlmBaseUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="http://localhost:11434"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Model
                </label>
                <select
                  value={llmModel}
                  onChange={(e) => setLlmModel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select model</option>
                  {availableModels.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
                {availableModels.length === 0 && (
                  <p className="text-sm text-gray-500 mt-1">
                    No models found. Make sure Ollama is running.
                  </p>
                )}
              </div>
            </>
          )}

          {/* Remote API Settings */}
          {provider === 'remote' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Base URL
                </label>
                <input
                  type="text"
                  value={remoteApiBase}
                  onChange={(e) => setRemoteApiBase(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://api.openai.com/v1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key
                </label>
                <input
                  type="password"
                  value={remoteApiKey}
                  onChange={(e) => setRemoteApiKey(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="sk-..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Model
                </label>
                <select
                  value={remoteModel}
                  onChange={(e) => setRemoteModel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-4o-mini">GPT-4o Mini</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                  <option value="claude-3-haiku">Claude 3 Haiku</option>
                </select>
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
            <button
              onClick={handleTestConnection}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Test Connection
            </button>
          </div>
        </div>
      )}

      {/* Embedding Tab */}
      {activeTab === 'embedding' && (
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Embedding Model
            </label>
            <select
              value={embeddingModel}
              onChange={(e) => setEmbeddingModel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {embeddingModels.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-500 mt-1">
              Recommended: bge-large-zh-v1.5 (best for Chinese text)
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-medium text-blue-900 mb-2">Mobile Local Model Guide</h3>
            <div className="text-sm text-blue-800 space-y-2">
              <p><strong>iOS:</strong> Use Ollama's official app or WebDAV server to access your Mac's Ollama</p>
              <p><strong>Android:</strong> Use "Ollama for Android" app with remote server URL</p>
              <p><strong>Setup steps:</strong></p>
              <ol className="list-decimal list-inside ml-2 space-y-1">
                <li>Run Ollama on your Mac/PC with <code>OLLAMA_HOST=0.0.0.0:11434</code></li>
                <li>Find your computer's local IP address</li>
                <li>On mobile, set Ollama URL to <code>http://YOUR_IP:11434</code></li>
                <li>Make sure both devices are on the same WiFi</li>
              </ol>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// Default export for routing compatibility
export default SettingsPage