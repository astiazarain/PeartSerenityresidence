import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ChevronLeft,
  ChevronRight,
  Check,
  Send,
  AlertCircle,
  Loader2,
  User,
  Heart,
  Activity,
  Stethoscope,
  Phone,
  CreditCard,
  FileText,
  CheckCircle2,
} from 'lucide-react';
import { supabase } from '../lib/supabase';
import type { Session } from '@supabase/supabase-js';

const STEPS = [
  { id: 0, label: 'Applicant', icon: User },
  { id: 1, label: 'Resident', icon: Heart },
  { id: 2, label: 'Care Needs', icon: Activity },
  { id: 3, label: 'Medical', icon: Stethoscope },
  { id: 4, label: 'Emergency', icon: Phone },
  { id: 5, label: 'Financial', icon: CreditCard },
  { id: 6, label: 'Additional', icon: FileText },
  { id: 7, label: 'Review', icon: CheckCircle2 },
];

const initialForm = {
  applicant_name: '', applicant_email: '', applicant_phone: '', applicant_relationship: '',
  resident_name: '', resident_dob: '', resident_gender: '', resident_address: '',
  care_type_requested: 'long_term', preferred_start_date: '', urgency: 'medium',
  mobility_level: 'independent', requires_specialized_care: false, specialized_care_details: '',
  primary_diagnosis: '', medications: '', allergies: '', dietary_restrictions: '',
  physician_name: '', physician_phone: '',
  emergency_contact_name: '', emergency_contact_relationship: '', emergency_contact_phone: '', emergency_contact_email: '',
  family_physician: '', insurance_provider: '', insurance_number: '', preferred_payment_method: 'monthly',
  additional_notes: '',
};

export default function QuoteRequest() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [session, setSession] = useState<Session | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
  }, []);

  const update = (field: string, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const canProceed = () => {
    if (step === 0) return form.applicant_name && form.applicant_email;
    if (step === 1) return form.resident_name;
    if (step === 2) return form.care_type_requested;
    return true;
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        ...form,
        user_id: session?.user?.id || null,
        resident_dob: form.resident_dob || null,
        preferred_start_date: form.preferred_start_date || null,
      };
      const { error: insertError } = await supabase.from('quote_requests').insert(payload);
      if (insertError) throw insertError;
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit quote request.');
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-brand-cream pt-20">
        <div className="max-w-lg text-center px-6">
          <div className="w-24 h-24 rounded-full bg-gold-100 flex items-center justify-center mx-auto mb-8 animate-fade-in">
            <CheckCircle2 className="h-12 w-12 text-gold-600" />
          </div>
          <h1 className="font-serif text-4xl text-brand-black mb-4">Quote Request Received!</h1>
          <p className="text-lg text-brand-textgrey mb-8 leading-relaxed">
            Thank you for choosing Peart Serenity Residence. Our care team will review your
            request and prepare a personalized quote within 48 hours. We will contact you
            at <span className="font-semibold text-gold-600">{form.applicant_email}</span> with the details.
          </p>
          <div className="bg-white rounded-2xl p-6 shadow-lg mb-8 text-left">
            <h3 className="font-serif text-xl text-brand-black mb-4">What Happens Next?</h3>
            <ol className="space-y-3 text-sm text-brand-textgrey">
              <li className="flex gap-3"><span className="w-6 h-6 rounded-full bg-gold-500 text-brand-black flex items-center justify-center font-bold text-xs flex-shrink-0">1</span>Our team reviews your care needs and requirements.</li>
              <li className="flex gap-3"><span className="w-6 h-6 rounded-full bg-gold-500 text-brand-black flex items-center justify-center font-bold text-xs flex-shrink-0">2</span>We prepare a personalized quote with pricing and care plan options.</li>
              <li className="flex gap-3"><span className="w-6 h-6 rounded-full bg-gold-500 text-brand-black flex items-center justify-center font-bold text-xs flex-shrink-0">3</span>We schedule a call to walk you through the proposal and answer questions.</li>
              <li className="flex gap-3"><span className="w-6 h-6 rounded-full bg-gold-500 text-brand-black flex items-center justify-center font-bold text-xs flex-shrink-0">4</span>Upon acceptance, we arrange a tour and finalize the admission process.</li>
            </ol>
          </div>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/" className="btn-primary">Back to Home</Link>
            <Link to="/contact" className="btn-outline">Contact Us</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brand-cream pt-24 pb-20">
      <div className="container-max px-6 md:px-12 lg:px-20">
        {/* HEADER */}
        <div className="text-center mb-12">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-600 mb-4">Request a Quote</p>
          <h1 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">Personalized Care Quote</h1>
          <p className="text-lg text-brand-textgrey max-w-2xl mx-auto">
            Complete the form below and our team will prepare a customized quote tailored to your loved one's specific care needs.
          </p>
        </div>

        {/* PROGRESS BAR */}
        <div className="max-w-4xl mx-auto mb-12">
          <div className="flex items-center justify-between overflow-x-auto pb-2">
            {STEPS.map((s, i) => (
              <div key={s.id} className="flex items-center flex-shrink-0">
                <div className="flex flex-col items-center">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 ${
                      i < step ? 'bg-gold-500 text-brand-black' :
                      i === step ? 'bg-brand-black text-gold-400 ring-4 ring-gold-200' :
                      'bg-white text-brand-textgrey border-2 border-brand-softgrey'
                    }`}
                  >
                    {i < step ? <Check className="h-5 w-5" /> : <s.icon className="h-5 w-5" />}
                  </div>
                  <span className={`text-xs mt-2 font-medium uppercase tracking-wider hidden md:block ${
                    i === step ? 'text-brand-black' : 'text-brand-textgrey'
                  }`}>{s.label}</span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className={`h-0.5 w-8 md:w-16 mx-1 transition-colors duration-300 ${
                    i < step ? 'bg-gold-500' : 'bg-brand-softgrey'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* FORM CARD */}
        <div className="max-w-3xl mx-auto">
          <div className="bg-white rounded-3xl shadow-xl p-8 md:p-10">
            {error && (
              <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-xl p-4 flex items-start gap-3 animate-fade-in">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            {/* STEP 0: APPLICANT */}
            {step === 0 && (
              <div className="animate-fade-in space-y-6">
                <div>
                  <h2 className="font-serif text-2xl text-brand-black mb-2">Section A — Applicant Information</h2>
                  <p className="text-brand-textgrey text-sm mb-6">Tell us about yourself — the person submitting this request.</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div><label className="label-field">Full Name *</label><input type="text" required value={form.applicant_name} onChange={(e) => update('applicant_name', e.target.value)} className="input-field" placeholder="Jane Doe" /></div>
                  <div><label className="label-field">Email *</label><input type="email" required value={form.applicant_email} onChange={(e) => update('applicant_email', e.target.value)} className="input-field" placeholder="jane@example.com" /></div>
                  <div><label className="label-field">Phone</label><input type="tel" value={form.applicant_phone} onChange={(e) => update('applicant_phone', e.target.value)} className="input-field" placeholder="+1 (876) 555-0100" /></div>
                  <div><label className="label-field">Relationship to Resident</label><select value={form.applicant_relationship} onChange={(e) => update('applicant_relationship', e.target.value)} className="input-field"><option value="">Select...</option><option value="spouse">Spouse</option><option value="child">Child / Daughter / Son</option><option value="sibling">Sibling</option><option value="parent">Parent</option><option value="guardian">Legal Guardian</option><option value="other">Other</option></select></div>
                </div>
              </div>
            )}

            {/* STEP 1: RESIDENT */}
            {step === 1 && (
              <div className="animate-fade-in space-y-6">
                <div>
                  <h2 className="font-serif text-2xl text-brand-black mb-2">Section B — Resident Information</h2>
                  <p className="text-brand-textgrey text-sm mb-6">Tell us about the person who will be receiving care.</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div><label className="label-field">Resident Full Name *</label><input type="text" required value={form.resident_name} onChange={(e) => update('resident_name', e.target.value)} className="input-field" placeholder="John Doe" /></div>
                  <div><label className="label-field">Date of Birth</label><input type="date" value={form.resident_dob} onChange={(e) => update('resident_dob', e.target.value)} className="input-field" /></div>
                  <div><label className="label-field">Gender</label><select value={form.resident_gender} onChange={(e) => update('resident_gender', e.target.value)} className="input-field"><option value="">Select...</option><option value="male">Male</option><option value="female">Female</option><option value="other">Other</option></select></div>
                  <div><label className="label-field">Current Address</label><input type="text" value={form.resident_address} onChange={(e) => update('resident_address', e.target.value)} className="input-field" placeholder="Montego Bay, Jamaica" /></div>
                </div>
              </div>
            )}

            {/* STEP 2: CARE NEEDS */}
            {step === 2 && (
              <div className="animate-fade-in space-y-6">
                <div>
                  <h2 className="font-serif text-2xl text-brand-black mb-2">Section C — Care Needs</h2>
                  <p className="text-brand-textgrey text-sm mb-6">What type of care are you looking for and when?</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="md:col-span-2"><label className="label-field">Type of Care Requested *</label><select value={form.care_type_requested} onChange={(e) => update('care_type_requested', e.target.value)} className="input-field"><option value="day_care">Adult Day Care</option><option value="respite">Respite Care</option><option value="long_term">Long-Term Residential</option><option value="private_suite">Private Suite</option><option value="recovery">Post-Surgical Recovery</option><option value="specialized">Specialized Care</option></select></div>
                  <div><label className="label-field">Preferred Start Date</label><input type="date" value={form.preferred_start_date} onChange={(e) => update('preferred_start_date', e.target.value)} className="input-field" /></div>
                  <div><label className="label-field">Urgency</label><select value={form.urgency} onChange={(e) => update('urgency', e.target.value)} className="input-field"><option value="low">Low — Exploring options</option><option value="medium">Medium — Within 3 months</option><option value="high">High — Immediate need</option></select></div>
                  <div><label className="label-field">Mobility Level</label><select value={form.mobility_level} onChange={(e) => update('mobility_level', e.target.value)} className="input-field"><option value="independent">Independent</option><option value="assisted">Requires assistance</option><option value="wheelchair">Wheelchair user</option><option value="bedbound">Bedbound</option></select></div>
                  <div className="flex items-center gap-3 pt-8">
                    <input type="checkbox" id="specialized_care" checked={form.requires_specialized_care} onChange={(e) => update('requires_specialized_care', e.target.checked)} className="w-5 h-5 rounded accent-gold-500" />
                    <label htmlFor="specialized_care" className="text-sm font-medium text-brand-black">Requires specialized care</label>
                  </div>
                </div>
                {form.requires_specialized_care && (
                  <div><label className="label-field">Specialized Care Details</label><textarea rows={3} value={form.specialized_care_details} onChange={(e) => update('specialized_care_details', e.target.value)} className="input-field resize-none" placeholder="Describe the specialized care needed (dementia, diabetes management, wound care, etc.)" /></div>
                )}
              </div>
            )}

            {/* STEP 3: MEDICAL */}
            {step === 3 && (
              <div className="animate-fade-in space-y-6">
                <div>
                  <h2 className="font-serif text-2xl text-brand-black mb-2">Section D — Medical Information</h2>
                  <p className="text-brand-textgrey text-sm mb-6">Help us understand the resident's medical needs. All information is confidential.</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="md:col-span-2"><label className="label-field">Primary Diagnosis / Condition</label><input type="text" value={form.primary_diagnosis} onChange={(e) => update('primary_diagnosis', e.target.value)} className="input-field" placeholder="e.g. Hypertension, early-stage dementia, post-hip surgery" /></div>
                  <div className="md:col-span-2"><label className="label-field">Current Medications</label><textarea rows={2} value={form.medications} onChange={(e) => update('medications', e.target.value)} className="input-field resize-none" placeholder="List current medications and dosages" /></div>
                  <div><label className="label-field">Allergies</label><input type="text" value={form.allergies} onChange={(e) => update('allergies', e.target.value)} className="input-field" placeholder="e.g. Penicillin, peanuts, none" /></div>
                  <div><label className="label-field">Dietary Restrictions</label><input type="text" value={form.dietary_restrictions} onChange={(e) => update('dietary_restrictions', e.target.value)} className="input-field" placeholder="e.g. Low sodium, diabetic, vegetarian" /></div>
                  <div><label className="label-field">Physician Name</label><input type="text" value={form.physician_name} onChange={(e) => update('physician_name', e.target.value)} className="input-field" placeholder="Dr. Smith" /></div>
                  <div><label className="label-field">Physician Phone</label><input type="tel" value={form.physician_phone} onChange={(e) => update('physician_phone', e.target.value)} className="input-field" placeholder="+1 (876) 555-0100" /></div>
                </div>
              </div>
            )}

            {/* STEP 4: EMERGENCY CONTACT */}
            {step === 4 && (
              <div className="animate-fade-in space-y-6">
                <div>
                  <h2 className="font-serif text-2xl text-brand-black mb-2">Section E — Emergency Contact</h2>
                  <p className="text-brand-textgrey text-sm mb-6">Who should we contact in case of an emergency?</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div><label className="label-field">Emergency Contact Name</label><input type="text" value={form.emergency_contact_name} onChange={(e) => update('emergency_contact_name', e.target.value)} className="input-field" placeholder="John Doe Jr." /></div>
                  <div><label className="label-field">Relationship</label><select value={form.emergency_contact_relationship} onChange={(e) => update('emergency_contact_relationship', e.target.value)} className="input-field"><option value="">Select...</option><option value="spouse">Spouse</option><option value="child">Child</option><option value="sibling">Sibling</option><option value="parent">Parent</option><option value="other">Other</option></select></div>
                  <div><label className="label-field">Phone</label><input type="tel" value={form.emergency_contact_phone} onChange={(e) => update('emergency_contact_phone', e.target.value)} className="input-field" placeholder="+1 (876) 555-0100" /></div>
                  <div><label className="label-field">Email</label><input type="email" value={form.emergency_contact_email} onChange={(e) => update('emergency_contact_email', e.target.value)} className="input-field" placeholder="john@example.com" /></div>
                </div>
              </div>
            )}

            {/* STEP 5: FINANCIAL */}
            {step === 5 && (
              <div className="animate-fade-in space-y-6">
                <div>
                  <h2 className="font-serif text-2xl text-brand-black mb-2">Section F — Family & Financial</h2>
                  <p className="text-brand-textgrey text-sm mb-6">Insurance and payment preference information helps us prepare an accurate quote.</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div><label className="label-field">Family Physician</label><input type="text" value={form.family_physician} onChange={(e) => update('family_physician', e.target.value)} className="input-field" placeholder="Dr. Smith, Montego Bay" /></div>
                  <div><label className="label-field">Insurance Provider</label><input type="text" value={form.insurance_provider} onChange={(e) => update('insurance_provider', e.target.value)} className="input-field" placeholder="e.g. Sagicor, Blue Cross, N/A" /></div>
                  <div><label className="label-field">Insurance / Policy Number</label><input type="text" value={form.insurance_number} onChange={(e) => update('insurance_number', e.target.value)} className="input-field" placeholder="Policy number" /></div>
                  <div><label className="label-field">Preferred Payment Method</label><select value={form.preferred_payment_method} onChange={(e) => update('preferred_payment_method', e.target.value)} className="input-field"><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="annual">Annual</option><option value="wire">Wire Transfer (Diaspora)</option><option value="insurance">Insurance Billing</option></select></div>
                </div>
              </div>
            )}

            {/* STEP 6: ADDITIONAL */}
            {step === 6 && (
              <div className="animate-fade-in space-y-6">
                <div>
                  <h2 className="font-serif text-2xl text-brand-black mb-2">Section G — Additional Information</h2>
                  <p className="text-brand-textgrey text-sm mb-6">Anything else we should know to better serve your loved one?</p>
                </div>
                <div><label className="label-field">Additional Notes</label><textarea rows={6} value={form.additional_notes} onChange={(e) => update('additional_notes', e.target.value)} className="input-field resize-none" placeholder="Share any preferences, concerns, or special requirements. For example: preferred activities, religious or cultural considerations, language preferences, behavioral notes, etc." /></div>
              </div>
            )}

            {/* STEP 7: REVIEW */}
            {step === 7 && (
              <div className="animate-fade-in space-y-6">
                <div>
                  <h2 className="font-serif text-2xl text-brand-black mb-2">Review Your Request</h2>
                  <p className="text-brand-textgrey text-sm mb-6">Please review the information below before submitting.</p>
                </div>
                <div className="space-y-4">
                  {[
                    { label: 'Applicant', values: [form.applicant_name, form.applicant_email, form.applicant_phone, form.applicant_relationship].filter(Boolean) },
                    { label: 'Resident', values: [form.resident_name, form.resident_dob, form.resident_gender, form.resident_address].filter(Boolean) },
                    { label: 'Care Needs', values: [form.care_type_requested, form.preferred_start_date, form.urgency, form.mobility_level, form.requires_specialized_care ? 'Specialized care required' : ''].filter(Boolean) },
                    { label: 'Medical', values: [form.primary_diagnosis, form.medications, form.allergies, form.dietary_restrictions].filter(Boolean) },
                    { label: 'Emergency Contact', values: [form.emergency_contact_name, form.emergency_contact_relationship, form.emergency_contact_phone, form.emergency_contact_email].filter(Boolean) },
                    { label: 'Financial', values: [form.insurance_provider, form.preferred_payment_method].filter(Boolean) },
                    { label: 'Additional', values: form.additional_notes ? [form.additional_notes] : ['No additional notes'] },
                  ].map((section) => (
                    <div key={section.label} className="bg-brand-cream rounded-2xl p-5">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-serif text-lg text-brand-black">{section.label}</h3>
                        <button onClick={() => setStep(STEPS.find((s) => s.label === section.label)?.id ?? 0)} className="text-xs text-gold-600 font-semibold hover:underline">Edit</button>
                      </div>
                      <p className="text-sm text-brand-textgrey">{section.values.join(' · ') || 'Not provided'}</p>
                    </div>
                  ))}
                </div>
                {!session && (
                  <div className="bg-gold-50 border border-gold-200 rounded-xl p-4 text-sm text-brand-charcoal">
                    <p className="font-semibold mb-1">Tip: Create an account to track your quote request.</p>
                    <p>You can submit this form as a guest, but <Link to="/auth" className="text-gold-600 font-semibold hover:underline">creating an account</Link> lets you track status and manage all your requests in one place.</p>
                  </div>
                )}
              </div>
            )}

            {/* NAVIGATION */}
            <div className="flex items-center justify-between mt-10 pt-6 border-t border-brand-softgrey">
              <button
                onClick={() => setStep(Math.max(0, step - 1))}
                disabled={step === 0 || submitting}
                className="inline-flex items-center gap-2 text-sm font-semibold text-brand-textgrey hover:text-gold-600 transition-colors disabled:opacity-40"
              >
                <ChevronLeft className="h-4 w-4" /> Back
              </button>

              {step < STEPS.length - 1 ? (
                <button
                  onClick={() => setStep(step + 1)}
                  disabled={!canProceed()}
                  className="btn-primary disabled:opacity-40"
                >
                  Continue <ChevronRight className="h-4 w-4" />
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="btn-primary disabled:opacity-60"
                >
                  {submitting ? <><Loader2 className="h-4 w-4 animate-spin" /> Submitting...</> : <>Submit Request <Send className="h-4 w-4" /></>}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
