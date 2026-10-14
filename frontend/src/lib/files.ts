export const FILE_ACCEPT = ".pdf,.txt,.md,application/pdf,text/plain,text/markdown";
export const FILE_OK = /\.(pdf|txt|md)$/i;

export function pickFiles(list: FileList | null) {
  return Array.from(list ?? []).filter((file) => FILE_OK.test(file.name));
}

export function tagsFrom(value: string) {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export function errMsg(err: unknown, fallback: string) {
  return err instanceof Error ? err.message : fallback;
}

export async function keepBusy(started: number) {
  const wait = 600 - (Date.now() - started);
  if (wait > 0) await new Promise((resolve) => setTimeout(resolve, wait));
}
