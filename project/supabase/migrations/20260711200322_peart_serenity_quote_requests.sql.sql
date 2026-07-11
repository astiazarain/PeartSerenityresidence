/*
# Quote Requests table for Peart Serenity Residence

## Purpose
Allows prospective clients to submit a detailed care quote request from the website.
The form mirrors the Peart Serenity Admission Form (sections A–I) so staff receive
all the information needed to generate a personalised quote.

## New Tables
- `quote_requests`
  - `id`              uuid PK
  - `user_id`         uuid FK → auth.users (nullable — guests can submit too)
  - `status`          text (pending / reviewed / quoted / accepted / rejected)
  - Section A – Applicant Info: `applicant_name`, `applicant_email`, `applicant_phone`, `applicant_relationship`
  - Section B – Resident Info: `resident_name`, `resident_dob`, `resident_gender`, `resident_address`
  - Section C – Care Needs: `care_type_requested`, `preferred_start_date`, `urgency`, `mobility_level`, `requires_specialized_care`, `specialized_care_details`
  - Section D – Medical Info: `primary_diagnosis`, `medications`, `allergies`, `dietary_restrictions`, `physician_name`, `physician_phone`
  - Section E – Emergency Contact: `emergency_contact_name`, `emergency_contact_relationship`, `emergency_contact_phone`, `emergency_contact_email`
  - Section F – Family/Financial: `family_physician`, `insurance_provider`, `insurance_number`, `preferred_payment_method`
  - Section G – Additional: `additional_notes`
  - `created_at`       timestamptz default now()

## Security
- RLS enabled.
- SELECT: authenticated users can read their own submissions; anon cannot read.
- INSERT: both anon and authenticated can insert (guests may submit quotes).
- UPDATE/DELETE: authenticated users can update/delete their own submissions.
*/

CREATE TABLE IF NOT EXISTS quote_requests (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  status          text NOT NULL DEFAULT 'pending',

  applicant_name        text NOT NULL,
  applicant_email       text NOT NULL,
  applicant_phone      text,
  applicant_relationship text,

  resident_name   text NOT NULL,
  resident_dob   date,
  resident_gender text,
  resident_address text,

  care_type_requested text NOT NULL,
  preferred_start_date date,
  urgency text DEFAULT 'medium',
  mobility_level text,
  requires_specialized_care boolean DEFAULT false,
  specialized_care_details text,

  primary_diagnosis text,
  medications text,
  allergies text,
  dietary_restrictions text,
  physician_name text,
  physician_phone text,

  emergency_contact_name text,
  emergency_contact_relationship text,
  emergency_contact_phone text,
  emergency_contact_email text,

  family_physician text,
  insurance_provider text,
  insurance_number text,
  preferred_payment_method text,

  additional_notes text,

  created_at timestamptz DEFAULT now()
);

ALTER TABLE quote_requests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_insert_quote_requests" ON quote_requests;
CREATE POLICY "anon_insert_quote_requests"
ON quote_requests FOR INSERT
TO anon, authenticated
WITH CHECK (true);

DROP POLICY IF EXISTS "select_own_quote_requests" ON quote_requests;
CREATE POLICY "select_own_quote_requests"
ON quote_requests FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "update_own_quote_requests" ON quote_requests;
CREATE POLICY "update_own_quote_requests"
ON quote_requests FOR UPDATE
TO authenticated
USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "delete_own_quote_requests" ON quote_requests;
CREATE POLICY "delete_own_quote_requests"
ON quote_requests FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_quote_requests_user_id ON quote_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_quote_requests_status ON quote_requests(status);
CREATE INDEX IF NOT EXISTS idx_quote_requests_created_at ON quote_requests(created_at DESC);
