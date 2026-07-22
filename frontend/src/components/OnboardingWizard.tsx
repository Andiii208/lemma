import { useState } from 'react';
import { ArrowRight, ArrowLeft, Key, FolderOpen, CheckCircle2 } from 'lucide-react';
import PresetSelector from './PresetSelector';

interface OnboardingWizardProps {
  onComplete: (settings: { workDir: string | null; preset: string | null }) => void;
}

type Step = 'welcome' | 'api-key' | 'work-dir' | 'preset' | 'done';

const STEPS: Step[] = ['welcome', 'api-key', 'work-dir', 'preset', 'done'];

export default function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState<Step>('welcome');
  const [apiKey, setApiKey] = useState('');
  const [workDir, setWorkDir] = useState<string | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [apiKeyStatus, setApiKeyStatus] = useState<string | null>(null);

  const stepIndex = STEPS.indexOf(currentStep);

  const goNext = () => {
    const nextIndex = stepIndex + 1;
    if (nextIndex < STEPS.length) {
      setCurrentStep(STEPS[nextIndex]);
    } else {
      onComplete({ workDir, preset: selectedPreset });
    }
  };

  const goBack = () => {
    const prevIndex = stepIndex - 1;
    if (prevIndex >= 0) setCurrentStep(STEPS[prevIndex]);
  };

  const handleSaveApiKey = async () => {
    if (!apiKey.trim()) return;
    try {
      const result = await window.lemmaAPI?.storeApiKey(apiKey.trim()) ?? { success: false, reason: 'API not available' };
      if (result.success) {
        setApiKeyStatus('success');
        setApiKey('');
        goNext();
      } else {
        setApiKeyStatus(`存储失败: ${result.reason}`);
      }
    } catch {
      setApiKeyStatus('IPC 不可用，请确认在 Electron 环境中运行');
    }
  };

  const handleSelectDir = async () => {
    const dir = await window.lemmaAPI?.selectDirectory();
    if (dir) setWorkDir(dir);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-bg-secondary p-8">
      <div className="w-full max-w-lg space-y-8">
        {/* 进度条 */}
        <div className="flex gap-1">
          {STEPS.map((step, index) => (
            <div
              key={step}
              className={`h-1 flex-1 rounded-full transition-colors ${
                index <= stepIndex ? 'bg-accent' : 'bg-bg-tertiary'
              }`}
            />
          ))}
        </div>

        {/* 欢迎 */}
        {currentStep === 'welcome' && (
          <div className="text-center space-y-4">
            <h1 className="text-3xl font-serif text-accent">欢迎使用 Lemma</h1>
            <p className="text-text-muted">
              Every Theorem Begins with a Lemma
            </p>
            <p className="text-sm text-text-muted">
              基于 Claude 的学术写作桌面软件。无需安装 Claude Code，开箱即用。
            </p>
            <button onClick={goNext} className="px-6 py-3 rounded-lg bg-accent text-white hover:bg-accent-hover text-sm">
              开始设置 <ArrowRight size={16} className="inline ml-1" />
            </button>
          </div>
        )}

        {/* API Key */}
        {currentStep === 'api-key' && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Key size={20} className="text-accent" />
              <h2 className="text-xl font-serif">Anthropic API Key</h2>
            </div>
            <p className="text-sm text-text-muted">
              输入你的 Anthropic API Key。密钥将通过 Electron safeStorage 加密存储。
            </p>
            <input
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="sk-ant-..."
              className="w-full px-4 py-3 rounded-lg border border-border-strong bg-bg-secondary focus:outline-none focus:ring-2 focus:ring-accent"
            />
            {apiKeyStatus && (
              <p className={`text-sm ${apiKeyStatus === 'success' ? 'text-green-600' : 'text-red-500'}`}>
                {apiKeyStatus}
              </p>
            )}
            <div className="flex justify-between">
              <button onClick={goBack} className="px-4 py-2 text-sm text-text-secondary hover:text-text">
                <ArrowLeft size={16} className="inline mr-1" /> 上一步
              </button>
              <button onClick={handleSaveApiKey} disabled={!apiKey.trim()} className="px-6 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover disabled:opacity-50 text-sm">
                保存并继续 <ArrowRight size={16} className="inline ml-1" />
              </button>
            </div>
          </div>
        )}

        {/* 工作目录 */}
        {currentStep === 'work-dir' && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <FolderOpen size={20} className="text-accent" />
              <h2 className="text-xl font-serif">选择工作目录</h2>
            </div>
            <p className="text-sm text-text-muted">
              选择一个目录作为工作空间。Claude 将在此目录中读写文件。
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={workDir || ''}
                readOnly
                placeholder="未选择"
                className="flex-1 px-4 py-3 rounded-lg border border-border-strong bg-bg-elevated text-sm"
              />
              <button onClick={handleSelectDir} className="px-4 py-3 rounded-lg border border-border-strong hover:bg-bg-tertiary text-sm">
                浏览
              </button>
            </div>
            <div className="flex justify-between">
              <button onClick={goBack} className="px-4 py-2 text-sm text-text-secondary hover:text-text">
                <ArrowLeft size={16} className="inline mr-1" /> 上一步
              </button>
              <button onClick={goNext} className="px-6 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover text-sm">
                {workDir ? '继续' : '跳过'} <ArrowRight size={16} className="inline ml-1" />
              </button>
            </div>
          </div>
        )}

        {/* 预设选择 */}
        {currentStep === 'preset' && (
          <div className="space-y-4">
            <h2 className="text-xl font-serif">选择预设模板</h2>
            <p className="text-sm text-text-muted">
              选择一个预设来定制 Claude 的行为。你可以稍后更改。
            </p>
            <PresetSelector selectedPreset={selectedPreset} onSelect={setSelectedPreset} />
            <div className="flex justify-between">
              <button onClick={goBack} className="px-4 py-2 text-sm text-text-secondary hover:text-text">
                <ArrowLeft size={16} className="inline mr-1" /> 上一步
              </button>
              <button onClick={goNext} className="px-6 py-2 rounded-lg bg-accent text-white hover:bg-accent-hover text-sm">
                完成设置 <ArrowRight size={16} className="inline ml-1" />
              </button>
            </div>
          </div>
        )}

        {/* 完成 */}
        {currentStep === 'done' && (
          <div className="text-center space-y-4">
            <CheckCircle2 size={48} className="text-green-500 mx-auto" />
            <h2 className="text-xl font-serif">设置完成！</h2>
            <p className="text-sm text-text-muted">
              Lemma 已准备就绪。开始你的学术写作之旅吧。
            </p>
            <button onClick={() => onComplete({ workDir, preset: selectedPreset })} className="px-6 py-3 rounded-lg bg-accent text-white hover:bg-accent-hover text-sm">
              进入 Lemma
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
