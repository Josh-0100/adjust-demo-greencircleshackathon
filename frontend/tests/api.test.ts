import { describe, expect, it, vi } from 'vitest';
import { api, ApiError, safeSourceUrl } from '@/lib/api';
describe('API transport and safe citations', () => {
  it('sends explicit demo role without frontend secrets', async () => { const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true }))); vi.stubGlobal('fetch', fetcher); await api('/cases', { role: 'staff' }); expect(fetcher).toHaveBeenCalledWith('/api/cases', expect.objectContaining({ headers: { 'Content-Type': 'application/json', 'X-Demo-Role': 'staff' } })); });
  it('preserves server validation messages', async () => { vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'This module is disabled.' }), { status: 422 }))); await expect(api('/enquiries')).rejects.toThrow('This module is disabled.'); });
  it('gives a recoverable message for an offline backend', async () => { vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Network error'))); await expect(api('/health')).rejects.toThrow('Cannot reach the service'); });
  it('rejects executable and malformed source URLs', () => { expect(safeSourceUrl('javascript:alert(1)')).toBeUndefined(); expect(safeSourceUrl('data:text/html,bad')).toBeUndefined(); expect(safeSourceUrl('not a url')).toBeUndefined(); expect(safeSourceUrl('https://example.org/evidence')).toBe('https://example.org/evidence'); });
});
