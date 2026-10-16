import { describe, expect, it } from 'vitest';
import { decodeHandoff, encodeHandoff, type CaseHandoff, type Catalogue } from '@/lib/case-api';

const catalogue: Catalogue = {
  employee_needs: ['later-start', 'breaks', 'standing', 'lifting', 'quiet', 'written', 'workload', 'flexibility', 'appointments', 'discuss-needs'].map(id => ({ id, text: `Authored employee need: ${id}` })),
  employer_needs: ['cover', 'core-tasks', 'fixed-hours', 'limited-budget', 'small-space', 'tried-flexible', 'discuss-practicalities'].map(id => ({ id, text: `Authored employer need: ${id}` })),
};
const employee = { reviewed: true as const, need_ids: ['later-start', 'breaks'], support_kind: 'health' as const };
const employer = { reviewed: true as const, need_ids: ['cover', 'fixed-hours'], business_size: 'under_50' as const };
const raw = (value: unknown) => btoa(JSON.stringify(value));

describe('two-sided invitation and return links', () => {
  it.each(['employee', 'employer'] as const)('round-trips a reviewed %s-first invitation and its complete return link', starter => {
    const invitation: CaseHandoff = { v: 1, starter, ...(starter === 'employee' ? { employee } : { employer }) };
    expect(decodeHandoff(encodeHandoff(invitation, catalogue), catalogue)).toEqual(invitation);
    const complete: CaseHandoff = { ...invitation, employee, employer, review_date: '2026-10-30' };
    expect(decodeHandoff(encodeHandoff(complete, catalogue), catalogue)).toEqual(complete);
  });

  it('allows a person to remove every suggested need before sharing', () => {
    const value: CaseHandoff = { v: 1, starter: 'employee', employee: { ...employee, need_ids: [] } };
    expect(decodeHandoff(encodeHandoff(value, catalogue), catalogue).employee?.need_ids).toEqual([]);
  });

  it('copies only the complete handoff allowlist into a generated link', () => {
    const value = {
      v: 1, starter: 'employee', description: 'PRIVATE DESCRIPTION ALPHA', medical_details: 'Parkinson disease', costs: { adjustments: 1234 },
      employee: { ...employee, description: 'PRIVATE DESCRIPTION BETA', condition: 'Parkinson disease', text: 'PRIVATE NEED TEXT' },
      employer: { ...employer, practicalities: 'PRIVATE BUDGET FIGURES', medical_details: 'Parkinson disease', costs: { legal: 1234 } },
      review_date: '2026-10-30',
    } as unknown as CaseHandoff;
    const encoded = encodeHandoff(value, catalogue);
    const payload = atob(encoded);
    expect(JSON.parse(payload)).toEqual({ v: 1, starter: 'employee', employee, employer, review_date: '2026-10-30' });
    expect(payload).not.toMatch(/PRIVATE|Parkinson|1234|description|medical_details|condition|costs/);
    expect(decodeHandoff(encoded, catalogue)).toEqual(JSON.parse(payload));
  });

  it.each([
    { v: 1, starter: 'employee', employee: { ...employee, need_ids: ['Parkinson disease PRIVATE'] } },
    { v: 1, starter: 'employer', employer: { ...employer, need_ids: ['PRIVATE_FINANCIAL_WORDS'] } },
    { v: 1, starter: 'employee', employee: { ...employee, reviewed: false } },
    { v: 1, starter: 'employer', employer: { ...employer, reviewed: false } },
    { v: 1, starter: 'employee', employee: { ...employee, support_kind: 'PRIVATE_DIAGNOSIS' } },
    { v: 1, starter: 'employer', employer: { ...employer, business_size: 'PRIVATE_SALARY' } },
    { v: 1, starter: 'employee', employee, review_date: 'PRIVATE_WORDS' },
    { v: 1, starter: 'employee', employee: { ...employee, need_ids: ['breaks', 'breaks'] } },
  ])('refuses to generate a link from invalid runtime selections: %#', value => {
    expect(() => encodeHandoff(value as CaseHandoff, catalogue)).toThrow('This invitation is incomplete or invalid. Ask for a new link.');
  });

  it.each([
    { v: 2, starter: 'employee', employee },
    { v: 1, starter: 'manager', employee },
    { v: 1, starter: 'employee' },
    { v: 1, starter: 'employee', employer },
    { v: 1, starter: 'employer', employee },
    { v: 1, starter: 'employee', employee: { ...employee, reviewed: false } },
    { v: 1, starter: 'employer', employer: { ...employer, reviewed: false } },
    { v: 1, starter: 'employee', employee: { ...employee, need_ids: ['invented-need'] } },
    { v: 1, starter: 'employee', employee: { ...employee, need_ids: ['Parkinson disease PRIVATE'] } },
    { v: 1, starter: 'employee', employee: { ...employee, need_ids: ['cover'] } },
    { v: 1, starter: 'employer', employer: { ...employer, need_ids: ['later-start'] } },
    { v: 1, starter: 'employee', employee: { ...employee, need_ids: ['breaks', 'breaks'] } },
    { v: 1, starter: 'employee', employee: { ...employee, need_ids: Array(11).fill('breaks') } },
    { v: 1, starter: 'employee', employee: { ...employee, need_ids: 'breaks' } },
    { v: 1, starter: 'employee', employee: { ...employee, support_kind: 'PRIVATE_DIAGNOSIS' } },
    { v: 1, starter: 'employer', employer: { ...employer, business_size: 'PRIVATE_SALARY' } },
    { v: 1, starter: 'employee', employee, description: 'PRIVATE_WORDS' },
    { v: 1, starter: 'employee', employee: { ...employee, condition: 'PRIVATE_DIAGNOSIS' } },
    { v: 1, starter: 'employer', employer: { ...employer, practicalities: 'PRIVATE_FINANCIAL_WORDS' } },
    { v: 1, starter: 'employee', employee, employer, costs: { adjustments: 1234 } },
    { v: 1, starter: 'employee', employee, review_date: 'PRIVATE_WORDS' },
    { v: 1, starter: 'employee', employee, review_date: 1234 },
    null,
    [],
  ])('rejects invalid or extra-key handoff data without echoing it: %#', value => {
    expect(() => decodeHandoff(raw(value), catalogue)).toThrow('This invitation is incomplete or invalid. Ask for a new link.');
    try { decodeHandoff(raw(value), catalogue); } catch (error) {
      expect((error as Error).message).not.toMatch(/PRIVATE|Parkinson|1234/);
    }
  });

  it.each(['', 'not valid base64!', btoa('not valid JSON'), 'a'.repeat(4001)])('rejects malformed or oversized payloads', encoded => {
    expect(() => decodeHandoff(encoded, catalogue)).toThrow('This invitation is incomplete or invalid. Ask for a new link.');
  });
});
