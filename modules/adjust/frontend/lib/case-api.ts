import { request } from './api';

export type CaseRole = 'employee' | 'employer';
export type BusinessSize = 'under_50' | '50_249' | '250_plus';
export type SupportKind = 'health' | 'carer' | 'both';
export interface WorkNeed { id: string; text: string }
export interface Catalogue { employee_needs: WorkNeed[]; employer_needs: WorkNeed[] }
export interface EmployeeSide { reviewed: true; need_ids: string[]; support_kind: SupportKind }
export interface EmployerSide { reviewed: true; need_ids: string[]; business_size: BusinessSize }
export interface CaseHandoff { v: 1; starter: CaseRole; employee?: EmployeeSide; employer?: EmployerSide; review_date?: string }
export interface SafetyResult { level: string; title: string; message: string; actions: string[]; official_url: string | null }
export interface PreparedSide { status: 'review' | 'urgent' | 'emergency'; needs: WorkNeed[]; safety: SafetyResult }
export interface PlanItem { id: string; title: string; detail: string; url: string }
export interface CombinedPlan {
  title: string; created_on: string; review_date: string;
  start_now: PlanItem[]; options: PlanItem[];
  conversation: { opening: string; questions: string[]; agree: string[] };
  help: PlanItem[]; legal_note: string; disclaimer: string;
}
export const caseApi = {
  catalogue: () => request<Catalogue>('/case/catalogue'),
  prepare: (body: {role: CaseRole; description: string; support_kind: SupportKind; business_size: BusinessSize | null; role_context: string; practicalities: string; tried: string}) => request<PreparedSide>('/case/prepare', body),
  plan: (body: {employee: EmployeeSide; employer: EmployerSide; review_date: string}) => request<CombinedPlan>('/case/plan', body),
};

// This is the complete handoff allowlist. Free text cannot enter a link.
export function encodeHandoff(value: CaseHandoff, catalogue: Catalogue): string {
  const clean: CaseHandoff = { v: 1, starter: value.starter };
  if (value.employee) clean.employee = { reviewed: value.employee.reviewed, need_ids: [...value.employee.need_ids], support_kind: value.employee.support_kind };
  if (value.employer) clean.employer = { reviewed: value.employer.reviewed, need_ids: [...value.employer.need_ids], business_size: value.employer.business_size };
  if (value.review_date) clean.review_date = value.review_date;
  const encoded = btoa(JSON.stringify(clean));
  decodeHandoff(encoded, catalogue);
  return encoded;
}
export function decodeHandoff(encoded: string, catalogue: Catalogue): CaseHandoff {
  if (!encoded || encoded.length > 4000) throw new Error('This invitation is incomplete or invalid. Ask for a new link.');
  let value: CaseHandoff;
  try { value = JSON.parse(atob(encoded)); } catch { throw new Error('This invitation is incomplete or invalid. Ask for a new link.'); }
  const only = (item: object, keys: string[]) => Object.keys(item).every(key => keys.includes(key));
  const idsValid = (ids: unknown, options: WorkNeed[]) => Array.isArray(ids) && ids.length <= 10 && new Set(ids).size === ids.length && ids.every(id => options.some(option => option.id === id));
  const invalid = !value || typeof value !== 'object' || !only(value, ['v','starter','employee','employer','review_date']) || value.v !== 1 || !['employee','employer'].includes(value.starter)
    || (!value.employee && !value.employer)
    || (value.employee && (typeof value.employee !== 'object' || !only(value.employee, ['reviewed','need_ids','support_kind']) || value.employee.reviewed !== true || !idsValid(value.employee.need_ids, catalogue.employee_needs) || !['health','carer','both'].includes(value.employee.support_kind)))
    || (value.employer && (typeof value.employer !== 'object' || !only(value.employer, ['reviewed','need_ids','business_size']) || value.employer.reviewed !== true || !idsValid(value.employer.need_ids, catalogue.employer_needs) || !['under_50','50_249','250_plus'].includes(value.employer.business_size)))
    || (!value.employee && value.starter !== 'employer') || (!value.employer && value.starter !== 'employee')
    || (value.review_date !== undefined && (typeof value.review_date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value.review_date)));
  if (invalid) throw new Error('This invitation is incomplete or invalid. Ask for a new link.');
  return value;
}
