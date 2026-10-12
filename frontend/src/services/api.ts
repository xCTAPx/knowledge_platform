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
  if (options.body) headers.set("Content-Type", "application/json");
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

export type Note = {
  id: number;
  title: string;
  content: string;
  tags: string[];
};

export const listNotes = () => Api.get<Note[]>("/notes");

export const createNote = (title: string, tags: string[], content: string) =>
  Api.post<Note>("/notes", { title, tags, content });

export const updateNote = (id: number, title: string, tags: string[], content: string) =>
  Api.put<Note>(`/notes/${id}`, { title, tags, content });

export const deleteNote = (id: number) => Api.delete(`/notes/${id}`);
