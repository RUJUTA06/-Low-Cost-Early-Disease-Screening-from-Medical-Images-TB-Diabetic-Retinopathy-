const ACCESS_KEY = 'clarity.access.basic';

export function accessIsEnabled() {
  return import.meta.env.VITE_ACCESS_REQUIRED === 'true';
}

export function getAccessHeader() {
  const encoded = sessionStorage.getItem(ACCESS_KEY);
  return encoded ? `Basic ${encoded}` : undefined;
}

export function saveAccessCredentials(username: string, password: string) {
  const bytes = new TextEncoder().encode(`${username}:${password}`);
  sessionStorage.setItem(ACCESS_KEY, btoa(Array.from(bytes, byte => String.fromCharCode(byte)).join('')));
}

export function clearAccessCredentials() {
  sessionStorage.removeItem(ACCESS_KEY);
}

export function hasAccessCredentials() {
  return Boolean(sessionStorage.getItem(ACCESS_KEY));
}
