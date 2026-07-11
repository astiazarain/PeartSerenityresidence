import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export type Inquiry = {
  id: string;
  name: string;
  email: string;
  phone?: string;
  country?: string;
  service_type: string;
  message: string;
  preferred_date?: string;
  status: string;
  source: string;
  notes?: string;
  created_at: string;
};

export type WaitlistEntry = {
  id: string;
  name: string;
  email: string;
  phone?: string;
  country?: string;
  care_type: string;
  urgency: string;
  notes?: string;
  active: boolean;
  created_at: string;
};

export type Testimonial = {
  id: string;
  author_name: string;
  relation: string;
  location?: string;
  content: string;
  rating: number;
  approved: boolean;
  featured: boolean;
  created_at: string;
};

export type TourBooking = {
  id: string;
  name: string;
  email: string;
  phone?: string;
  preferred_date: string;
  preferred_time: string;
  party_size: number;
  message?: string;
  status: string;
  created_at: string;
};

export type QuoteRequest = {
  id: string;
  user_id: string | null;
  status: string;
  applicant_name: string;
  applicant_email: string;
  applicant_phone?: string;
  applicant_relationship?: string;
  resident_name: string;
  resident_dob?: string;
  resident_gender?: string;
  resident_address?: string;
  care_type_requested: string;
  preferred_start_date?: string;
  urgency: string;
  mobility_level?: string;
  requires_specialized_care: boolean;
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
  created_at: string;
};
