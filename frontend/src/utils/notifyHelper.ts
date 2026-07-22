export function createNotifyHelper(
  isEnabled: () => boolean,
  notify?: (title: string, body: string) => Promise<void> | void,
): (title: string, body: string) => void {
  return (title: string, body: string) => {
    if (!isEnabled()) return;
    void notify?.(title, body);
  };
}
