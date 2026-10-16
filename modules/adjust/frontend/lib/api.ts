import type { Health, Plan, Referral, Result, Scenario, Situation, Source } from './types';

export async function request<T>(path: string, body?: unknown): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(`/api/adjust${path}`, { method: body === undefined ? 'GET' : 'POST',
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body), cache: 'no-store', signal: controller.signal });
    if (!response.ok) {
      let detail = 'The service could not complete this request. Please try again.';
      try { const error = await response.json(); if (typeof error.detail === 'string') detail = error.detail;
        else if (response.status === 422) detail = 'Check the required fields and keep the description within the stated limits.';
      } catch { /* Proxy failures may not be JSON. */ }
      throw new Error(detail);
    }
    return await response.json() as T;
  } catch (error) {
    if (typeof error === 'object' && error !== null && 'name' in error && error.name === 'AbortError') throw new Error('The request took too long. Please try again.');
    if (error instanceof TypeError) throw new Error('ADJUST cannot reach its local service. Check that the ADJUST launcher is running, then retry.');
    throw error;
  } finally { clearTimeout(timer); }
}
export const api = {
  health: () => request<Health>('/health'),
  scenarios: () => request<{ scenarios: Scenario[] }>('/scenarios'),
  knowledge: () => request<{ entries: Source[] }>('/knowledge'),
  support: () => request<{ referrals: Referral[] }>('/support'),
  analyse: (situation: Situation) => request<Result>('/analyse', situation),
  plan: (body: { situation: Situation; selected_ids: string[]; next_steps: string; review_date: string; human_reviewed: boolean }) => request<Plan>('/plan', body),
};

export function localDate(offset = 0) {
  const date = new Date(); date.setDate(date.getDate() + offset);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}
export function friendlyDate(date: string) { return new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(`${date}T12:00:00`)); }
