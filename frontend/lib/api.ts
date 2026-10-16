export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); this.name = 'ApiError'; }
}
export async function api<T>(path: string, options: RequestInit & { role?: 'resident' | 'staff' | 'admin' } = {}): Promise<T> {
  const { role, ...init } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 60000);
  try {
    const response = await fetch(`/api${path}`, {
      ...init, signal: init.signal || controller.signal,
      headers: { 'Content-Type': 'application/json', ...(role ? { 'X-Demo-Role': role } : {}), ...init.headers },
    });
    const text = await response.text();
    let data: unknown;
    try { data = text ? JSON.parse(text) : {}; } catch { throw new ApiError('The service returned an unexpected response. Check that the backend is running, then retry.', response.status); }
    if (!response.ok) {
      const detail = (data as { detail?: unknown }).detail;
      throw new ApiError(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(item => item.msg || 'Invalid input').join('. ') : `Request failed (${response.status}). Please try again.`, response.status);
    }
    return data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error && error.name === 'AbortError') throw new ApiError('This request took too long. Please retry when the service is ready.', 408);
    throw new ApiError('Cannot reach the service. Start the backend and try again.', 0);
  } finally { clearTimeout(timer); }
}
export function errorMessage(error: unknown) { return error instanceof Error ? error.message : 'Something went wrong. Please retry.'; }
export function safeSourceUrl(url: string | null) { if (!url) return undefined; try { const parsed = new URL(url); return ['https:', 'http:'].includes(parsed.protocol) ? url : undefined; } catch { return undefined; } }
