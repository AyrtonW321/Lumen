// Shapes of the JSON the Python server sends. Keep in sync with lumen/config.py, lumen/leads.py and lumen/db.py.

export type Brand = "Haneco" | "JWL" | "Exceledy";
export type Product = "Solar" | "Lighting" | "BESS" | "EV Charging";
export type Source = "new" | "follow-up" | "winner" | "loser";
export type Label = "good" | "poor";
export type PhoneType = "direct" | "mobile" | "business";

export interface Outcome {
  label: string;
  key: string;
  retry: number | null;
  human?: boolean;
  positive?: boolean;
  closes?: boolean;
  move_to?: Source;
}

export interface ModelMetrics {
  examples: number;
  positive_rate: number;
  train_loss: number;
  hidden: number;
  val_examples?: number;
  val_brier_model?: number;
  val_brier_baseline?: number;
  beats_baseline?: boolean;
}

export interface Config {
  caller_name?: string | null;
  brands: Record<Brand, string>;
  products: Product[];
  sources: Record<Source, string>;
  outcomes: Record<string, Outcome>;
  phone_types: Record<PhoneType, string>;
  meeting_types: string[];
  model: ModelMetrics | null;
  warning_traits?: string[];
}

/** A stored trait. contact_id is null for company traits. global = offered in the picker and filter. */
export interface Trait {
  id: number;
  lead_id: number;
  contact_id: number | null;
  name: string;
  note: string | null;
  global: number;
  created_at: string;
}

/** Compact trait as sent on list and callback rows. */
export interface TraitChip { name: string; note: string | null; person: boolean; }

/** GET /api/traits: names offered in the picker and filter. */
export interface TraitCatalog { person: string[]; company: string[]; }

export type CallbackSection = "expecting" | "overdue" | "today" | "upcoming";

/** One row of GET /api/callbacks. */
export interface CallbackRow {
  id: number;
  name: string;
  brand: Brand;
  section: CallbackSection;
  callback_at: string | null;
  late: boolean;
  contact: { name: string; title: string | null } | null;
  phone: string | null;
  ext: string | null;
  last_note: string | null;
  traits: TraitChip[];
  badges: string[];
}

export interface Contact {
  status?: string | null;
  sort_order?: number;
  id: number;
  lead_id: number;
  name: string;
  title: string | null;
  phone: string | null;
  email: string | null;
  ext: string | null;
  phone_type: PhoneType | null;
  prefers_email: number;
  created_at: string;
  traits?: Trait[];
  badges?: string[];
}

export interface Activity {
  id: number;
  lead_id: number;
  contact_id: number | null;
  timestamp: string;
  weekday: string;
  hour_block: string;
  outcome: string;
  note: string | null;
  caller: string | null;
  myphoner_comment: string;
  called_back?: number | null;
}

/** One row of GET /api/leads. `score` and `why` exist only for open leads once a model is trained. */
/** Pinned contact, or the one picked by default (decision-maker, else top non-reception contact). */
export interface MainContact { id: number; name: string; title: string | null; pinned: boolean; }

export interface LeadRow {
  id: number;
  name: string;
  brand: Brand;
  products: string;
  source: Source;
  list_name: string | null;
  label: Label | null;
  closed: string | null;
  next_action_date: string | null;
  last_outcome: string | null;
  last_contacted?: string | null;
  attempts: number;
  advice: string[];
  tier: number;
  open: boolean;
  due: boolean;
  score?: number;
  why?: string[];
  callback_at?: string | null;
  expecting_call?: number;
  traits?: TraitChip[];
  badges?: string[];
  main_contact?: MainContact | null;
}

/** GET /api/leads/:id. Activities are newest first. */
export interface LeadDetail {
  id: number;
  name: string;
  brand: Brand;
  products: string;
  source: Source;
  list_name: string | null;
  phone: string | null;
  label: Label | null;
  closed: string | null;
  next_action_date: string | null;
  created_at: string;
  address: string | null;
  facility_size: string | null;
  solar_reference: string | null;
  lighting_reference: string | null;
  meeting_type: string | null;
  appt_at: string | null;
  callback_at?: string | null;
  expecting_call?: number;
  contacts: Contact[];
  activities: Activity[];
  traits?: Trait[];
  badges?: string[];
  main_contact?: MainContact | null;
}

export type TabId = Source | "all";

export interface CallForm {
  outcome: string | null;
  contact_id: number | null;
}

export type SyncCounts = Record<string, number>;
