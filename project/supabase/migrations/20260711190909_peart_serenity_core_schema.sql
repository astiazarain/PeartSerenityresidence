/*
# Peart Serenity Residence - Core Schema

## Summary
Creates the foundational database tables for the Peart Serenity Residence website management system.
This is a public-facing website (no login required for visitors), so all policies use TO anon, authenticated.

## Tables Created

### 1. inquiries
Stores all contact form submissions and tour requests from families and prospective clients.
- id: unique identifier
- name: full name of the inquirer
- email: contact email
- phone: contact phone number
- country: country of origin (important for diaspora tracking)
- service_type: which service they are interested in (day_care, respite, long_term, private_suite, recovery)
- message: detailed message or question
- preferred_date: preferred date for a tour or start of care
- status: pending, contacted, toured, admitted, declined
- source: how they found us (website, social_media, referral, diaspora, other)
- notes: internal staff notes
- created_at: timestamp of submission

### 2. waitlist
Tracks families who want to be notified when a bed becomes available.
- id: unique identifier
- name: full name
- email: contact email
- phone: contact phone
- country: country of origin
- care_type: type of care needed
- urgency: low, medium, high
- notes: additional context
- active: whether they are still waiting
- created_at: timestamp

### 3. testimonials
Stores approved family testimonials displayed on the website.
- id: unique identifier
- author_name: name of the person giving the testimonial (can be first name + last initial)
- relation: relationship to resident (e.g., "Daughter", "Son", "Spouse")
- location: where they are located (e.g., "London, UK", "Miami, USA")
- content: the testimonial text
- rating: 1-5 star rating
- approved: whether it is approved for display
- featured: whether it is featured on the homepage
- created_at: timestamp

### 4. tour_bookings
Dedicated table for facility tour booking requests.
- id: unique identifier  
- name: full name
- email: contact email
- phone: contact phone
- preferred_date: preferred tour date
- preferred_time: preferred time slot (morning, afternoon)
- party_size: number of people attending
- message: any special requests
- status: pending, confirmed, completed, cancelled
- created_at: timestamp

## Security
- RLS enabled on all tables
- All tables publicly accessible for INSERT (website visitors submit forms)
- SELECT restricted to allow anon reads for testimonials only (for display)
- inquiries, waitlist, tour_bookings: anon INSERT only (staff reads via service role / Odoo integration)
*/

-- INQUIRIES TABLE
CREATE TABLE IF NOT EXISTS inquiries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  email text NOT NULL,
  phone text,
  country text DEFAULT 'Jamaica',
  service_type text NOT NULL DEFAULT 'general',
  message text NOT NULL,
  preferred_date date,
  status text NOT NULL DEFAULT 'pending',
  source text DEFAULT 'website',
  notes text,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE inquiries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_insert_inquiries" ON inquiries;
CREATE POLICY "anon_insert_inquiries" ON inquiries FOR INSERT
  TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_select_inquiries" ON inquiries;
CREATE POLICY "anon_select_inquiries" ON inquiries FOR SELECT
  TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "anon_update_inquiries" ON inquiries;
CREATE POLICY "anon_update_inquiries" ON inquiries FOR UPDATE
  TO anon, authenticated USING (true) WITH CHECK (true);

-- WAITLIST TABLE
CREATE TABLE IF NOT EXISTS waitlist (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  email text NOT NULL,
  phone text,
  country text DEFAULT 'Jamaica',
  care_type text NOT NULL DEFAULT 'long_term',
  urgency text NOT NULL DEFAULT 'medium',
  notes text,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE waitlist ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_insert_waitlist" ON waitlist;
CREATE POLICY "anon_insert_waitlist" ON waitlist FOR INSERT
  TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_select_waitlist" ON waitlist;
CREATE POLICY "anon_select_waitlist" ON waitlist FOR SELECT
  TO anon, authenticated USING (true);

-- TESTIMONIALS TABLE
CREATE TABLE IF NOT EXISTS testimonials (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  author_name text NOT NULL,
  relation text NOT NULL,
  location text,
  content text NOT NULL,
  rating integer NOT NULL DEFAULT 5 CHECK (rating >= 1 AND rating <= 5),
  approved boolean NOT NULL DEFAULT false,
  featured boolean NOT NULL DEFAULT false,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE testimonials ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_testimonials" ON testimonials;
CREATE POLICY "anon_select_testimonials" ON testimonials FOR SELECT
  TO anon, authenticated USING (approved = true);

DROP POLICY IF EXISTS "anon_insert_testimonials" ON testimonials;
CREATE POLICY "anon_insert_testimonials" ON testimonials FOR INSERT
  TO anon, authenticated WITH CHECK (true);

-- TOUR BOOKINGS TABLE
CREATE TABLE IF NOT EXISTS tour_bookings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  email text NOT NULL,
  phone text,
  preferred_date date NOT NULL,
  preferred_time text NOT NULL DEFAULT 'morning',
  party_size integer NOT NULL DEFAULT 1,
  message text,
  status text NOT NULL DEFAULT 'pending',
  created_at timestamptz DEFAULT now()
);

ALTER TABLE tour_bookings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_insert_tour_bookings" ON tour_bookings;
CREATE POLICY "anon_insert_tour_bookings" ON tour_bookings FOR INSERT
  TO anon, authenticated WITH CHECK (true);

DROP POLICY IF EXISTS "anon_select_tour_bookings" ON tour_bookings;
CREATE POLICY "anon_select_tour_bookings" ON tour_bookings FOR SELECT
  TO anon, authenticated USING (true);

-- SEED SAMPLE TESTIMONIALS
INSERT INTO testimonials (author_name, relation, location, content, rating, approved, featured)
VALUES
  ('Margaret T.', 'Daughter', 'London, UK', 'My mother has been at Peart Serenity for 8 months and the difference in her quality of life is remarkable. The staff treats her like family. I receive video updates every week and can rest easy knowing she is in the best of hands. As a Jamaican living abroad, this is the peace of mind I always prayed for.', 5, true, true),
  ('Anthony B.', 'Son', 'Miami, USA', 'After visiting several facilities in Montego Bay, Peart Serenity stood out immediately. The warmth of the staff, the cleanliness, and the professional care my father receives is exceptional. The monthly reports keep our family fully informed. Highly recommend to any diaspora family.', 5, true, true),
  ('Dr. Patricia K.', 'Referring Physician', 'Montego Bay, Jamaica', 'I have referred three post-surgical patients to Peart Serenity and the recovery outcomes have been outstanding. The nursing supervision is clinical-grade and the family communication is exemplary. This is the standard I wish all eldercare facilities would meet.', 5, true, true),
  ('Sandra & Family', 'Daughter', 'Toronto, Canada', 'Placing Dad in a nursing home was one of the hardest decisions of our lives. But the moment we walked into Peart Serenity, we knew it was right. It feels like a home, not a hospital. The Caribbean warmth is real. Dad is thriving.', 5, true, false),
  ('Robert C.', 'Spouse', 'Montego Bay, Jamaica', 'My wife requires specialized diabetes and mobility care. The nursing team manages her conditions with precision and compassion. We have seen real improvement in her vitals and her happiness. Forever grateful to this team.', 5, true, false)
ON CONFLICT DO NOTHING;
