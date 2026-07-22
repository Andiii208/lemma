import React, { useState, useEffect, useCallback } from 'react';
import { Download, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface UpdateStateData {
  state: string;
  info?: { version?: string; releaseNotes?: string };
  progress?: { percent: number };
  error?: string;
}

export function UpdateBanner(): React.ReactElement | null {
  const [updateState, setUpdateState] = useState<UpdateStateData | null>(null);

  useEffect(() => {
    const api = window.lemmaAPI;
    if (!api?.onUpdateStateChanged) return;
    const unsub = api.onUpdateStateChanged((data) => {
      setUpdateState(data as UpdateStateData);
    });
    return unsub;
  }, []);

  const handleDownload = useCallback(() => window.lemmaAPI?.downloadUpdate(), []);
  const handleInstall = useCallback(() => window.lemmaAPI?.installUpdate(), []);

  if (!updateState || updateState.state === 'idle' || updateState.state === 'checking') {
    if (updateState?.state === 'checking') {
      return (
        <div className="flex items-center gap-2 px-3 py-1.5 text-xs text-gray-500 bg-gray-50 rounded-md">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span>Checking for updates...</span>
        </div>
      );
    }
    return null;
  }

  if (updateState.state === 'error') {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 text-xs text-red-600 bg-red-50 rounded-md">
        <AlertCircle className="w-3 h-3" />
        <span>Update error: {updateState.error}</span>
      </div>
    );
  }

  if (updateState.state === 'available') {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 text-xs text-blue-600 bg-blue-50 rounded-md">
        <Download className="w-3 h-3" />
        <span>Update v{updateState.info?.version} available</span>
        <button
          onClick={handleDownload}
          className="ml-1 px-2 py-0.5 text-xs font-medium text-white bg-blue-500 rounded hover:bg-blue-600"
        >
          Download
        </button>
      </div>
    );
  }

  if (updateState.state === 'downloading') {
    const percent = updateState.progress?.percent ?? 0;
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 text-xs text-blue-600 bg-blue-50 rounded-md">
        <Loader2 className="w-3 h-3 animate-spin" />
        <span>Downloading... {Math.round(percent)}%</span>
        <div className="w-16 h-1.5 bg-blue-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>
    );
  }

  if (updateState.state === 'downloaded') {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 text-xs text-green-600 bg-green-50 rounded-md">
        <CheckCircle className="w-3 h-3" />
        <span>Update v{updateState.info?.version} ready</span>
        <button
          onClick={handleInstall}
          className="ml-1 px-2 py-0.5 text-xs font-medium text-white bg-green-500 rounded hover:bg-green-600"
        >
          Restart
        </button>
      </div>
    );
  }

  return null;
}
