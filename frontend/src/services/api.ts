const BASE = "/api/v1";
const SKIP_REFRESH = new Set(["/auth/login", "/auth/register", "/auth/refresh"]);

export type User = {
  id: number;
  nickname: string;
  email: string;
  age: number | null;
};

async function send(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  return fetch(BASE + path, { ...options, headers, credentials: "include" });
}

async function parse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? "Request failed");
  }
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let res = await send(path, options);
  if (res.status === 401 && !SKIP_REFRESH.has(path)) {
    const refreshed = await send("/auth/refresh", { method: "POST" });
    if (refreshed.ok) res = await send(path, options);
  }
  return parse<T>(res);
}

function withBody<T>(method: string, path: string, body?: unknown) {
  return request<T>(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export const Api = {
  get<T>(path: string) {
    return request<T>(path);
  },
  post<T = void>(path: string, body?: unknown) {
    return withBody<T>("POST", path, body);
  },
  put<T = void>(path: string, body?: unknown) {
    return withBody<T>("PUT", path, body);
  },
  patch<T = void>(path: string, body?: unknown) {
    return withBody<T>("PATCH", path, body);
  },
  delete(path: string) {
    return request(path, { method: "DELETE" });
  },
};

export const getMe = () => Api.get<User>("/auth/me");

export const login = (email: string, password: string) =>
  Api.post("/auth/login", { email, password });

export const register = (nickname: string, email: string, password: string, age: number | null) =>
  Api.post("/auth/register", { nickname, email, password, age });

export const logout = () => Api.post("/auth/logout");

export type FileOut = {
  id: number;
  name: string;
  created_at: string;
};

export type Note = {
  id: number;
  title: string;
  content: string;
  tags: string[];
  created_at: string;
  files: FileOut[];
};

export type FeedItem = (Note & { kind: "note" }) | (FileOut & { kind: "file" });

export type Page<T> = {
  items: T[];
  has_more: boolean;
};

export type FeedCursor = {
  before_id: number;
  before_kind: "note" | "file";
  before_created_at: string;
};

export const PAGE_SIZE = 20;

function qs(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value));
  }
  const value = search.toString();
  return value ? `?${value}` : "";
}

export const listNotes = (before_id?: number, limit = PAGE_SIZE) =>
  Api.get<Page<Note>>(`/notes${qs({ limit, before_id })}`);

export const createNote = (title: string, tags: string[], content: string) =>
  Api.post<Note>("/notes", { title, tags, content });

export const updateNote = (id: number, title: string, tags: string[], content: string) =>
  Api.put<Note>(`/notes/${id}`, { title, tags, content });

export const deleteNote = (id: number) => Api.delete(`/notes/${id}`);

export const noteFileUrl = (noteId: number, fileId: number) => `${BASE}/notes/${noteId}/files/${fileId}`;

export const fileUrl = (fileId: number) => `${BASE}/files/${fileId}`;

function uploadForm(path: string, file: File, onProgress?: (pct: number) => void) {
  const body = new FormData();
  body.append("file", file);

  function sendXhr() {
    return new Promise<Response>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", BASE + path);
      xhr.withCredentials = true;
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) onProgress?.(Math.round((event.loaded / event.total) * 100));
      };
      xhr.onload = () => resolve(new Response(xhr.responseText, { status: xhr.status }));
      xhr.onerror = () => reject(new Error("Request failed"));
      xhr.send(body);
    });
  }

  return (async () => {
    let res = await sendXhr();
    if (res.status === 401) {
      const refreshed = await send("/auth/refresh", { method: "POST" });
      if (refreshed.ok) res = await sendXhr();
    }
    return parse<FileOut>(res);
  })();
}

export const uploadNoteFile = (noteId: number, file: File, onProgress?: (pct: number) => void) =>
  uploadForm(`/notes/${noteId}/files`, file, onProgress);

export const deleteNoteFile = (noteId: number, fileId: number) => Api.delete(`/notes/${noteId}/files/${fileId}`);

export const listFiles = (before_id?: number, limit = PAGE_SIZE) =>
  Api.get<Page<FileOut>>(`/files${qs({ limit, before_id })}`);

export const listFeed = (cursor?: FeedCursor, limit = PAGE_SIZE, q?: string) =>
  Api.get<Page<FeedItem>>(`/feed${qs({ limit, q: q || undefined, ...cursor })}`);

export const uploadFile = (file: File, onProgress?: (pct: number) => void) => uploadForm("/files", file, onProgress);

export const deleteFile = (fileId: number) => Api.delete(`/files/${fileId}`);

export const askLibrary = (q: string) => Api.post<{ answer: string }>("/ask", { q });
