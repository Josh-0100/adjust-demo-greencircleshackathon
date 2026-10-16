import { afterEach, describe, expect, it, vi } from 'vitest';
import { request, friendlyDate, localDate } from '@/lib/api';

afterEach(() => vi.unstubAllGlobals());
describe('stateless API client', () => {
  it('uses only the isolated API namespace and disables caching', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'ok' }) });
    vi.stubGlobal('fetch', fetcher);
    await request('/health');
    expect(fetcher).toHaveBeenCalledWith('/api/adjust/health', expect.objectContaining({ method: 'GET', cache: 'no-store' }));
  });
  it('submits JSON without a persistence call', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal('fetch', fetcher);
    await request('/analyse', { description: 'workplace barriers' });
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher).toHaveBeenCalledWith('/api/adjust/analyse', expect.objectContaining({ method: 'POST', body: '{"description":"workplace barriers"}' }));
  });
  it('shows a useful error for a broken proxy without displaying HTML', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 502, json: async () => { throw new Error('HTML'); } }));
    await expect(request('/analyse', {})).rejects.toThrow('The service could not complete this request');
  });
  it('does not expose validation inputs', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: [{ input: 'secret employee name' }] }) }));
    await expect(request('/analyse', {})).rejects.toThrow('Check the required fields');
  });
  it('explains network and timeout failures', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    await expect(request('/health')).rejects.toThrow('cannot reach its local service');
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new DOMException('aborted', 'AbortError')));
    await expect(request('/health')).rejects.toThrow('took too long');
  });
  it('uses unambiguous British display dates and local calendar inputs', () => {
    expect(friendlyDate('2026-10-16')).toBe('16 Oct 2026');
    expect(localDate()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
