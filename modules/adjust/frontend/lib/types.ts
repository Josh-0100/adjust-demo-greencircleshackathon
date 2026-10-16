export interface Situation { description: string; role: string; constraints: string; answers: Record<string, string>; use_ai: boolean }
export interface Analysis { role: string | null; tasks: string[]; barriers: string[]; reported_limitations: string[]; constraints: string[]; missing_information: string[]; clarification_required: boolean; scenarios: string[] }
export interface Source { id: string; topic: string; summary: string; official_url: string; publisher: string; last_reviewed: string; content_owner: string; scenarios: string[]; verification_status: string; evidence_locator: string; review_due: string }
export interface Recommendation { id: string; title: string; barrier_addressed: string; steps: string[]; employee_questions: string[]; source_ids: string[]; limitations: string; referral_guidance: string; effort: string }
export interface Referral { id: string; name: string; publisher: string; provides: string; eligibility: string; access: string; official_url: string; verified_on: string; status: string; limitations: string }
export interface Conversation { opening: string; questions: string[]; potential_options: string[]; agreement_summary: string; follow_up: string[]; source_ids: string[] }
export interface Result {
  status: 'ready' | 'clarification' | 'insufficient_evidence' | 'urgent' | 'emergency'; analysis: Analysis;
  questions: { id: string; question: string; hint: string; required: boolean }[];
  recommendations: Recommendation[]; conversation: Conversation | null; sources: Source[]; referrals: Referral[];
  safety: { level: string; title: string; message: string; actions: string[]; official_url: string | null };
  provider: string; simulated: boolean; provider_note: string | null; human_review_required: true;
  data_persisted: false; notices: string[]; created_on: string;
}
export interface Plan { title: string; status: string; workplace_situation: string; barriers: string[]; adjustments: Recommendation[]; discussion_questions: string[]; agreed_next_steps: string; external_support: Referral[]; review_date: string; sources: Source[]; disclaimer: string; created_on: string; human_reviewed: boolean }
export interface Scenario { id: string; label: string; description: string; role: string; constraints: string; expected: string }
export interface Health { status: string; module: string; provider: string; data_persisted: boolean; ai_configured: boolean; knowledge_entries: number; professional_review: string }
