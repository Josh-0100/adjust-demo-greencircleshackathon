export type ModuleId = 'service-navigator' | 'employment' | 'community' | 'triage' | 'learning' | 'custom';
export type Challenge = {
  borough: string; title: string; description: string; problem_statement: string;
  target_users: string[]; desired_outcomes: string[]; selected_modules: ModuleId[];
  success_metrics: string[]; constraints: string[]; data_sources: string[];
  demo_scenario: string; human_review_required: boolean;
};
export type Config = { challenge: Challenge; demo_mode: boolean; boroughs: string[]; escalation_threshold: number };
export type Module = { id: ModuleId; name: string; description: string; icon: string; enabled: boolean; input_hint: string; example_prompt: string; capabilities: string[]; workflow_steps: string[] };
export type Resource = { id: number; title: string; category: string; module_id: ModuleId; borough: string; description: string; content: string; source_label: string; source_url: string | null; synthetic: boolean; skills: string[]; next_steps: string[] };
export type Analysis = {
  summary: string; intent: string; confidence: number; needs_human_review: boolean; escalation_reason: string | null;
  recommendations: { title: string; description: string; next_steps: string[]; match_score: number | null; skills_gap: string[] }[];
  sources: { resource_id: number; title: string; excerpt: string; source_label: string; source_url: string | null; synthetic: boolean }[];
  safety_notes: string[]; workflow_steps: { name: string; status: 'complete' | 'review' | 'warning'; detail: string }[];
  provider: string; simulated: boolean; processing_ms: number; duplicate_of: number | null;
};
export type Case = { id: number; reference: string; resident_name: string; message: string; module_id: ModuleId; borough: string; category: string; priority: 'low' | 'normal' | 'high' | 'urgent'; status: 'new' | 'in_review' | 'resolved'; department: string; created_at: string; updated_at: string; review_note: string | null; analysis: Analysis };
export type Metric = { key: string; label: string; value: number; unit: string; kind: 'observed' | 'prototype_test' | 'estimated' | 'simulated'; description: string };
export type Impact = { metrics: Metric[]; trend: { label: string; enquiries: number; resolved: number }[]; categories: { label: string; count: number }[]; total_cases: number; review_count: number; resolved_count: number; provider: string; demo_mode: boolean };
export type AuditEvent = { id: number; action: string; actor: string; entity: string; created_at: string; detail: string };
export type EnquiryInput = { message: string; module_id: ModuleId; borough?: string; resident_name?: string };
