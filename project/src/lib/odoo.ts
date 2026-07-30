// Client for the Odoo backend. Odoo is the sole backend for this site: no
// other datastore is involved. Custom endpoints live in
// odoo/addons/peart_serenity/controllers/main.py; session endpoints
// (/web/session/*) are built into Odoo itself.
//
// Calls use relative paths so this works both behind the local dev reverse
// proxy (http://localhost:8080) and in production, where the same domain
// routes /api and /web to Odoo. Session auth is cookie-based (same-origin),
// so `credentials: 'include'` is enough - no token to manage in JS.

// Must match the Odoo database name configured in infra/docker-compose.yml
// / the production instance.
const ODOO_DB = 'peartserenity';

type OdooJsonRpcResponse<T> = {
  jsonrpc: '2.0';
  id: number | null;
  result?: T;
  error?: { code: number; message: string; data?: { message?: string } };
};

async function callOdoo<T>(path: string, params: Record<string, unknown>): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params }),
  });

  if (!response.ok) {
    throw new Error(`Odoo request failed (HTTP ${response.status})`);
  }

  const payload: OdooJsonRpcResponse<T> = await response.json();
  if (payload.error) {
    throw new Error(payload.error.data?.message || payload.error.message);
  }
  return payload.result as T;
}

const callApi = <T>(path: string, params: Record<string, unknown>) => callOdoo<T>(`/api${path}`, params);

type ApiResult = { success: boolean; id?: number; error?: string };

// ---- Session / auth --------------------------------------------------

export type SessionInfo = {
  uid: number | false;
  name?: string;
  username?: string;
  partner_id?: number;
};

const SESSION_EVENT = 'odoo-session-changed';

function notifySessionChanged() {
  window.dispatchEvent(new Event(SESSION_EVENT));
}

/** Subscribe to login/logout/signup. Returns an unsubscribe function. */
export function onSessionChanged(callback: () => void): () => void {
  window.addEventListener(SESSION_EVENT, callback);
  return () => window.removeEventListener(SESSION_EVENT, callback);
}

export async function getSession(): Promise<SessionInfo> {
  return callOdoo<SessionInfo>('/web/session/get_session_info', {});
}

export async function signup(
  name: string,
  email: string,
  password: string,
  phone: string,
  username: string
): Promise<void> {
  const result = await callApi<ApiResult>('/auth/signup', { name, email, password, phone, username });
  if (!result.success) {
    throw new Error(result.error || 'Failed to create account.');
  }
}

/** `identifier` may be the account's email, username or phone number. */
export async function login(identifier: string, password: string): Promise<SessionInfo> {
  const session = await callOdoo<SessionInfo>('/web/session/authenticate', {
    db: ODOO_DB,
    login: identifier,
    password,
  });
  if (!session.uid) {
    throw new Error('Invalid credentials.');
  }
  notifySessionChanged();
  return session;
}

export async function logout(): Promise<void> {
  await callOdoo('/web/session/destroy', {});
  notifySessionChanged();
}

// ---- Care quote ---------------------------------------------------------

export type CareQuotePayload = {
  applicant_name: string;
  applicant_email: string;
  applicant_phone?: string;
  applicant_relationship?: string;
  resident_name: string;
  resident_dob?: string | null;
  resident_gender?: string;
  resident_address?: string;
  care_type_requested: string;
  preferred_start_date?: string | null;
  urgency?: string;
  mobility_level?: string;
  requires_specialized_care?: boolean;
  specialized_care_details?: string;
  primary_diagnosis?: string;
  medications?: string;
  allergies?: string;
  dietary_restrictions?: string;
  physician_name?: string;
  physician_phone?: string;
  emergency_contact_name?: string;
  emergency_contact_relationship?: string;
  emergency_contact_phone?: string;
  emergency_contact_email?: string;
  family_physician?: string;
  insurance_provider?: string;
  insurance_number?: string;
  preferred_payment_method?: string;
  additional_notes?: string;
};

export async function submitCareQuote(payload: CareQuotePayload): Promise<number> {
  const result = await callApi<ApiResult>('/care-quote', payload);
  if (!result.success) {
    throw new Error(result.error || 'Failed to submit quote request.');
  }
  return result.id as number;
}

// ---- Contact / tours / waitlist / testimonials ---------------------------

export type ContactPayload = {
  name: string;
  email: string;
  phone?: string;
  message: string;
  country?: string;
  service_type?: string;
  preferred_date?: string;
};

export async function submitContact(payload: ContactPayload): Promise<number> {
  const result = await callApi<ApiResult>('/contact', payload);
  if (!result.success) throw new Error(result.error || 'Failed to send your message.');
  return result.id as number;
}

export type TourBookingPayload = {
  name: string;
  email: string;
  phone?: string;
  preferred_date: string;
  preferred_time?: string;
  party_size?: number;
  message?: string;
};

export async function submitTourBooking(payload: TourBookingPayload): Promise<number> {
  const result = await callApi<ApiResult>('/tour-booking', payload);
  if (!result.success) throw new Error(result.error || 'Failed to book your tour.');
  return result.id as number;
}

export type WaitlistPayload = {
  name: string;
  email: string;
  phone?: string;
  country?: string;
  care_type: string;
  urgency?: string;
  notes?: string;
};

export async function submitWaitlist(payload: WaitlistPayload): Promise<number> {
  const result = await callApi<ApiResult>('/waitlist', payload);
  if (!result.success) throw new Error(result.error || 'Failed to join the waitlist.');
  return result.id as number;
}

// ---- Nomenclators (Care Type / Urgency Level) -----------------------------

export type NomenclatorOption = { code: string; name: string };

export async function fetchNomenclators(): Promise<{
  care_types: NomenclatorOption[];
  urgency_levels: NomenclatorOption[];
}> {
  const result = await callApi<{
    success: boolean;
    care_types: NomenclatorOption[];
    urgency_levels: NomenclatorOption[];
  }>('/nomenclators', {});
  return { care_types: result.care_types, urgency_levels: result.urgency_levels };
}

export type Testimonial = {
  id: number;
  author_name: string;
  relation: string;
  location?: string;
  content: string;
  rating: number;
  photo?: string | false;
};

export async function fetchTestimonials(limit = 6): Promise<Testimonial[]> {
  const result = await callApi<{ success: boolean; records: Testimonial[] }>('/testimonials', { limit });
  return result.records;
}

// ---- Family portal (requires a logged-in session) -------------------------

export type MyAdmission = {
  id: number;
  resident_name: string;
  care_type_requested: string;
  state: string;
  create_date: string;
};

export type MyTourBooking = {
  id: number;
  preferred_date: string;
  preferred_time: string;
  party_size: number;
  status: string;
  create_date: string;
};

export async function fetchMyAdmissions(): Promise<MyAdmission[]> {
  const result = await callApi<{ success: boolean; records: MyAdmission[] }>('/my/admissions', {});
  return result.records;
}

export async function fetchMyTours(): Promise<MyTourBooking[]> {
  const result = await callApi<{ success: boolean; records: MyTourBooking[] }>('/my/tours', {});
  return result.records;
}

// ---- Site settings (social links, WhatsApp) -------------------------------

export type SiteSettings = {
  whatsapp_number: string;
  whatsapp_message: string;
  facebook_url: string | false;
  instagram_url: string | false;
  tiktok_url: string | false;
  linkedin_url: string | false;
};

export async function fetchSiteSettings(): Promise<SiteSettings> {
  const result = await callApi<{ success: boolean } & SiteSettings>('/site-settings', {});
  const { success: _success, ...settings } = result;
  return settings;
}

// ---- Gallery ----------------------------------------------------------------

export type GalleryPhoto = {
  id: number;
  title: string;
  category: 'facility' | 'activities' | 'events';
  image: string | false;
};

export async function fetchGallery(category?: string): Promise<GalleryPhoto[]> {
  const result = await callApi<{ success: boolean; records: GalleryPhoto[] }>('/gallery', { category });
  return result.records;
}

// ---- Careers / job applications ----------------------------------------------

export type JobPosition = {
  id: number;
  name: string;
  department: string | false;
  description: string;
};

export async function fetchJobs(): Promise<JobPosition[]> {
  const result = await callApi<{ success: boolean; records: JobPosition[] }>('/jobs', {});
  return result.records;
}

// ---- Services (published service products) --------------------------------

export type ServicePeriod = 'day' | 'week' | 'month' | 'custom';

export type Service = {
  id: number;
  name: string;
  list_price: number;
  price_period: ServicePeriod;
  description_sale: string;
  features: string[];
  is_popular: boolean;
};

export async function fetchServices(): Promise<Service[]> {
  const result = await callApi<{ success: boolean; records: Service[] }>('/services', {});
  return result.records;
}

export type JobApplicationPayload = {
  name: string;
  email: string;
  phone?: string;
  job_id: number;
  years_experience?: number;
  nursing_license_number?: string;
  references?: string;
  message?: string;
  cv_filename?: string;
  cv_base64?: string;
};

export async function submitJobApplication(payload: JobApplicationPayload): Promise<number> {
  const result = await callApi<ApiResult>('/jobs/apply', payload);
  if (!result.success) throw new Error(result.error || 'Failed to submit your application.');
  return result.id as number;
}

// ---- AI customer agent widget -------------------------------------------
// Endpoints live in odoo/addons/ai_customer_agent/controllers/main.py, not
// under /api like the rest of this file - that module ships its own prefix.

export type AiWidgetConfig =
  | { enabled: false }
  | {
      enabled: true;
      language: 'en' | 'es';
      store_name: string | null;
      primary_color: string;
      accent_color: string;
      welcome_message: string | null;
    };

export async function fetchAiWidgetConfig(): Promise<AiWidgetConfig> {
  return callOdoo<AiWidgetConfig>('/ai_agent/widget_config', {});
}
