// Client for the Odoo backend's public JSON-RPC API (see
// odoo/addons/peart_serenity/controllers/main.py). Calls are made with a
// relative path so this works both behind the local dev reverse proxy
// (http://localhost:8080) and in production, where the same domain routes
// /api to Odoo.

type OdooJsonRpcResponse<T> = {
  jsonrpc: '2.0';
  id: number | null;
  result?: T;
  error?: { code: number; message: string; data?: { message?: string } };
};

async function callOdoo<T>(path: string, params: Record<string, unknown>): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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

type ApiResult = { success: boolean; id?: number; error?: string };

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
  const result = await callOdoo<ApiResult>('/care-quote', payload);
  if (!result.success) {
    throw new Error(result.error || 'Failed to submit quote request.');
  }
  return result.id as number;
}

export async function registerContact(name: string, email: string, phone?: string): Promise<number> {
  const result = await callOdoo<ApiResult>('/register-contact', { name, email, phone });
  if (!result.success) {
    throw new Error(result.error || 'Failed to register contact.');
  }
  return result.id as number;
}
