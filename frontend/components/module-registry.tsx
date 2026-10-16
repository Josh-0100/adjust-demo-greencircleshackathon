'use client';
import { type ComponentType, useState } from 'react';
import { BookOpen, BriefcaseBusiness, Building2, HeartHandshake, Leaf, Route, type LucideIcon } from 'lucide-react';
import { api } from '@/lib/api';
import type { Case, EnquiryInput, ModuleId } from '@/lib/types';
import { Badge, Card, Field, Input, Textarea } from './ui';
export type CustomAssessmentInput = { home_type: 'flat' | 'house' | 'other'; risk_flags: ('cold' | 'damp' | 'bills')[]; household_vulnerability: boolean; goal: string };
export type ModuleInputProps = { value: CustomAssessmentInput; onChange: (value: CustomAssessmentInput) => void };
function HomeSupportFields({ value, onChange }: ModuleInputProps) {
  return <div className="custom-fields"><div className="custom-intro"><Leaf size={17} /><span>Home resilience assessment · custom workflow</span></div><div className="form-row"><Field label="Home type" htmlFor="home-type"><select id="home-type" className="input" value={value.home_type} onChange={e => onChange({ ...value, home_type: e.target.value as CustomAssessmentInput['home_type'] })}><option value="flat">Flat</option><option value="house">House</option><option value="other">Other</option></select></Field><Field label="Who needs support?" htmlFor="household"><select id="household" className="input" value={value.household_vulnerability ? 'yes' : 'no'} onChange={e => onChange({ ...value, household_vulnerability: e.target.value === 'yes' })}><option value="no">General household</option><option value="yes">A vulnerable household member</option></select></Field></div><fieldset className="checkbox-field"><legend>What is affecting the home?</legend>{(['cold', 'damp', 'bills'] as const).map(flag => <label key={flag}><input type="checkbox" checked={value.risk_flags.includes(flag)} onChange={e => onChange({ ...value, risk_flags: e.target.checked ? [...value.risk_flags, flag] : value.risk_flags.filter(item => item !== flag) })} />{flag === 'bills' ? 'Energy bills' : flag === 'cold' ? 'Cold rooms' : 'Damp or mould'}</label>)}</fieldset></div>;
}
function HomeSupportResult({ item }: { item: Case }) { return <Card className="custom-result"><div><Leaf size={21} /><h3>Home resilience assessment</h3></div><p>Suggested risk level: <strong>{item.priority}</strong>. This custom workflow combines home conditions with the resident’s stated goal and routes the assessment for human verification.</p><Badge tone="amber">Staff verification required</Badge></Card>; }
export type FrontendModulePlugin = { icon: LucideIcon; shortName: string; InputComponent?: ComponentType<ModuleInputProps>; ResultComponent?: ComponentType<{ item: Case }>; submit?: (input: EnquiryInput, custom: CustomAssessmentInput) => Promise<Case> };
// Add one keyed plugin for a new module; shared results remain grounded in the Case contract.
export const frontendModuleRegistry: Record<ModuleId, FrontendModulePlugin> = {
  'service-navigator': { icon: Building2, shortName: 'Council services' },
  employment: { icon: BriefcaseBusiness, shortName: 'Work & skills' },
  community: { icon: HeartHandshake, shortName: 'Community' },
  triage: { icon: Route, shortName: 'Report an issue' },
  learning: { icon: BookOpen, shortName: 'Learning' },
  custom: { icon: Leaf, shortName: 'Home resilience', InputComponent: HomeSupportFields, ResultComponent: HomeSupportResult,
    submit: async (input, custom) => (await api<{ case: Case }>('/custom/assess', { method: 'POST', body: JSON.stringify({ ...custom, goal: input.message, borough: input.borough, resident_name: input.resident_name }) })).case },
};
export const defaultCustomInput: CustomAssessmentInput = { home_type: 'flat', risk_flags: ['cold', 'bills'], household_vulnerability: false, goal: '' };
