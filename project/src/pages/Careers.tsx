import { useEffect, useState } from 'react';
import {
  Briefcase,
  Send,
  Upload,
  CheckCircle2,
  AlertCircle,
  FileText,
} from 'lucide-react';
import { fetchJobs, submitJobApplication, type JobPosition } from '../lib/odoo';

const initialForm = {
  name: '',
  email: '',
  phone: '',
  job_id: '',
  years_experience: '',
  nursing_license_number: '',
  references: '',
  message: '',
};

function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      resolve(result.split(',')[1] ?? '');
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export default function Careers() {
  const [jobs, setJobs] = useState<JobPosition[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [form, setForm] = useState(initialForm);
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [cvError, setCvError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    fetchJobs()
      .then(setJobs)
      .catch(() => setJobs([]))
      .finally(() => setLoadingJobs(false));
  }, []);

  const selectJob = (id: number) => {
    setForm((prev) => ({ ...prev, job_id: String(id) }));
    document.getElementById('apply-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const onCvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setCvError(null);
    if (file && file.type !== 'application/pdf') {
      setCvError('Please upload your CV as a PDF file.');
      setCvFile(null);
      return;
    }
    if (file && file.size > 5 * 1024 * 1024) {
      setCvError('The CV file must be smaller than 5MB.');
      setCvFile(null);
      return;
    }
    setCvFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const cv = cvFile ? await readFileAsBase64(cvFile) : undefined;
      await submitJobApplication({
        name: form.name,
        email: form.email,
        phone: form.phone || undefined,
        job_id: parseInt(form.job_id, 10),
        years_experience: form.years_experience ? parseInt(form.years_experience, 10) : undefined,
        nursing_license_number: form.nursing_license_number || undefined,
        references: form.references || undefined,
        message: form.message || undefined,
        cv_filename: cvFile?.name,
        cv_base64: cv,
      });
      setSuccess(true);
      setForm(initialForm);
      setCvFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit your application.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      {/* HEADER */}
      <section className="relative pt-40 pb-20 bg-brand-black overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-gold-500 rounded-full blur-3xl translate-x-1/2 translate-y-1/2"></div>
        </div>
        <div className="container-max px-6 md:px-12 lg:px-20 relative z-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-400 mb-4">Join Our Team</p>
          <h1 className="font-serif text-5xl md:text-6xl text-white mb-6">Careers at Peart Serenity</h1>
          <p className="text-lg text-brand-cream/80 max-w-2xl mx-auto leading-relaxed">
            We are always looking for compassionate people to care for our residents. Explore our open
            positions below and apply directly online.
          </p>
        </div>
      </section>

      {/* OPEN POSITIONS */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">Open Positions</p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black">Current Opportunities</h2>
          </div>

          {loadingJobs && <p className="text-center text-brand-textgrey">Loading positions...</p>}

          {!loadingJobs && jobs.length === 0 && (
            <p className="text-center text-brand-textgrey">
              We have no open positions right now — check back soon, or send us your CV below for future opportunities.
            </p>
          )}

          {!loadingJobs && jobs.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {jobs.map((job) => (
                <div key={job.id} className="bg-brand-cream rounded-2xl p-8 border border-brand-softgrey">
                  <div className="w-12 h-12 rounded-xl bg-gold-500 flex items-center justify-center mb-5">
                    <Briefcase className="h-6 w-6 text-brand-black" />
                  </div>
                  <h3 className="font-serif text-2xl text-brand-black mb-1">{job.name}</h3>
                  {job.department && <p className="text-sm text-gold-600 font-semibold mb-3">{job.department}</p>}
                  {job.description && (
                    <p className="text-brand-textgrey leading-relaxed mb-6 whitespace-pre-wrap">{job.description}</p>
                  )}
                  <button onClick={() => selectJob(job.id)} className="btn-outline text-xs !py-3 !px-6">
                    Apply for this role
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* APPLICATION FORM */}
      <section id="apply-form" className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="max-w-3xl mx-auto">
            {success ? (
              <div className="bg-gold-50 border-2 border-gold-200 rounded-2xl p-8 text-center animate-fade-in">
                <CheckCircle2 className="h-12 w-12 text-gold-600 mx-auto mb-4" />
                <h3 className="font-serif text-2xl text-brand-black mb-2">Application Received!</h3>
                <p className="text-brand-textgrey mb-4">
                  Thank you for your interest in joining Peart Serenity Residence. Our team will review your
                  application and reach out if there is a match.
                </p>
                <button onClick={() => setSuccess(false)} className="text-gold-600 font-semibold text-sm hover:underline">
                  Submit another application
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="bg-white rounded-3xl shadow-xl p-8 md:p-10 animate-fade-in">
                <h2 className="font-serif text-3xl text-brand-black mb-2">Apply Now</h2>
                <p className="text-brand-textgrey mb-8">Tell us about yourself and attach your CV.</p>

                {error && (
                  <div className="mb-6 bg-red-50 border-2 border-red-200 rounded-2xl p-6 flex items-start gap-3">
                    <AlertCircle className="h-6 w-6 text-red-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-red-800">Something went wrong</p>
                      <p className="text-red-600 text-sm mt-1">{error}</p>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="label-field">Full Name *</label>
                    <input type="text" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input-field" placeholder="Jane Doe" />
                  </div>
                  <div>
                    <label className="label-field">Email *</label>
                    <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input-field" placeholder="jane@example.com" />
                  </div>
                  <div>
                    <label className="label-field">Phone</label>
                    <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="input-field" placeholder="+1 (876) 555-0100" />
                  </div>
                  <div>
                    <label className="label-field">Position *</label>
                    <select required value={form.job_id} onChange={(e) => setForm({ ...form, job_id: e.target.value })} className="input-field">
                      <option value="" disabled>Select a position</option>
                      {jobs.map((job) => (
                        <option key={job.id} value={job.id}>{job.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label-field">Years of Experience</label>
                    <input type="number" min={0} value={form.years_experience} onChange={(e) => setForm({ ...form, years_experience: e.target.value })} className="input-field" placeholder="5" />
                  </div>
                  <div>
                    <label className="label-field">Nursing License Number</label>
                    <input type="text" value={form.nursing_license_number} onChange={(e) => setForm({ ...form, nursing_license_number: e.target.value })} className="input-field" placeholder="If applicable" />
                  </div>
                </div>

                <div className="mt-6">
                  <label className="label-field">References</label>
                  <textarea rows={3} value={form.references} onChange={(e) => setForm({ ...form, references: e.target.value })} className="input-field resize-none" placeholder="Name, relationship and contact details of 1-2 references" />
                </div>

                <div className="mt-6">
                  <label className="label-field">Cover Message</label>
                  <textarea rows={4} value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} className="input-field resize-none" placeholder="Tell us why you'd be a great fit..." />
                </div>

                <div className="mt-6">
                  <label className="label-field">CV (PDF) *</label>
                  <label className="flex items-center gap-3 border-2 border-dashed border-brand-softgrey rounded-xl px-6 py-8 cursor-pointer hover:border-gold-400 transition-colors">
                    <Upload className="h-6 w-6 text-gold-600 flex-shrink-0" />
                    <div className="flex-1">
                      {cvFile ? (
                        <span className="flex items-center gap-2 text-brand-black font-medium">
                          <FileText className="h-4 w-4" /> {cvFile.name}
                        </span>
                      ) : (
                        <span className="text-brand-textgrey text-sm">Click to upload your CV (PDF, max 5MB)</span>
                      )}
                    </div>
                    <input type="file" accept="application/pdf" required onChange={onCvChange} className="hidden" />
                  </label>
                  {cvError && <p className="text-red-600 text-sm mt-2">{cvError}</p>}
                </div>

                <button type="submit" disabled={submitting || !cvFile} className="btn-primary w-full mt-8 disabled:opacity-60">
                  {submitting ? 'Submitting...' : 'Submit Application'} <Send className="h-4 w-4" />
                </button>
              </form>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
