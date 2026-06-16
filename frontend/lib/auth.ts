// Token storage that's importable by api.ts without circular deps.
// The store calls setAuthToken on login/logout; api.ts calls getAuthToken per request.

const STORAGE_KEY = "echo-auth-token";

let _token: string | null = null;

export function setAuthToken(token: string | null): void {
  _token = token;
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem(STORAGE_KEY, token);
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
}

export function getAuthToken(): string | null {
  if (_token) return _token;
  if (typeof window === "undefined") return null;
  return localStorage.getItem(STORAGE_KEY);
}
