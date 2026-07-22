interface ExportOptions {
  format: 'markdown' | 'text';
  includeTimestamps: boolean;
  includeMetadata: boolean;
}

export function exportMessages(
  messages: ClaudeMessage[],
  options: ExportOptions
): string {
  const lines: string[] = [];

  lines.push(`# Lemma 对话导出`);
  lines.push(`导出时间: ${new Date().toLocaleString()}`);
  lines.push(`消息数量: ${messages.length}`);
  lines.push('');
  lines.push('---');
  lines.push('');

  for (const message of messages) {
    const isUser = message.metadata?.role === 'user';
    const roleLabel = isUser ? '**用户**' : '**Claude**';

    if (options.format === 'markdown') {
      lines.push(`### ${roleLabel}`);
      if (options.includeTimestamps) {
        lines.push(`*${new Date().toLocaleTimeString()}*`);
      }
      lines.push('');
      lines.push(message.content);
      lines.push('');
    } else {
      lines.push(`[${roleLabel}]`);
      lines.push(message.content);
      lines.push('');
    }
  }

  return lines.join('\n');
}

export function exportMessagesJson(messages: ClaudeMessage[]): string {
  const exportData = {
    version: '1.0',
    exportedAt: new Date().toISOString(),
    messageCount: messages.length,
    messages: messages.map((message, index) => ({
      index,
      type: message.type,
      role: message.metadata?.role || 'assistant',
      content: message.content,
    })),
  };
  return JSON.stringify(exportData, null, 2);
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

export function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
