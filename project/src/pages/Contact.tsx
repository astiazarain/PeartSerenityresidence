import { useState, useEffect } from 'react';
import {
  MapPin,
  Phone,
  Mail,
  Clock,
  Send,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Heart,
  Plane,
  Users,
} from 'lucide-react';
import { submitTourBooking, submitContact, submitWaitlist } from '../lib/odoo';

type FormMode = 'tour' | 'inquiry' | 'waitlist';

export default function Contact() {
  const [mode, setMode] = useState<FormMode>('tour');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [tourForm, setTourForm] = useState({ name: '', email: '', phone: '', preferred_date: '', preferred_time: 'morning', party_size: 1, message: '' });
  const [inquiryForm, setInquiryForm] = useState({ name: '', email: '', phone: '', country: 'Jamaica', service_type: 'general', message: '', preferred_date: '' });
  const [waitlistForm, setWaitlistForm] = useState({ name: '', email: '', phone: '', country: 'Jamaica', care_type: 'long_term', urgency: 'medium', notes: '' });

  useEffect(() => { setSuccess(false); setError(null); }, [mode]);

  const handleTourSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true); setError(null);
    try {
      await submitTourBooking({
        name: tourForm.name, email: tourForm.email, phone: tourForm.phone || undefined,
        preferred_date: tourForm.preferred_date, preferred_time: tourForm.preferred_time,
        party_size: tourForm.party_size, message: tourForm.message || undefined,
      });
      setSuccess(true);
      setTourForm({ name: '', email: '', phone: '', preferred_date: '', preferred_time: 'morning', party_size: 1, message: '' });
    } catch (err) { setError(err instanceof Error ? err.message : 'Something went wrong.'); }
    finally { setSubmitting(false); }
  };

  const handleInquirySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true); setError(null);
    try {
      await submitContact({
        name: inquiryForm.name, email: inquiryForm.email, phone: inquiryForm.phone || undefined,
        country: inquiryForm.country, service_type: inquiryForm.service_type, message: inquiryForm.message,
        preferred_date: inquiryForm.preferred_date || undefined,
      });
      setSuccess(true);
      setInquiryForm({ name: '', email: '', phone: '', country: 'Jamaica', service_type: 'general', message: '', preferred_date: '' });
    } catch (err) { setError(err instanceof Error ? err.message : 'Something went wrong.'); }
    finally { setSubmitting(false); }
  };

  const handleWaitlistSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true); setError(null);
    try {
      await submitWaitlist({
        name: waitlistForm.name, email: waitlistForm.email, phone: waitlistForm.phone || undefined,
        country: waitlistForm.country, care_type: waitlistForm.care_type, urgency: waitlistForm.urgency,
        notes: waitlistForm.notes || undefined,
      });
      setSuccess(true);
      setWaitlistForm({ name: '', email: '', phone: '', country: 'Jamaica', care_type: 'long_term', urgency: 'medium', notes: '' });
    } catch (err) { setError(err instanceof Error ? err.message : 'Something went wrong.'); }
    finally { setSubmitting(false); }
  };

  const tabs = [
    { id: 'tour' as FormMode, label: 'Book a Tour', icon: Calendar },
    { id: 'inquiry' as FormMode, label: 'General Inquiry', icon: Mail },
    { id: 'waitlist' as FormMode, label: 'Join Waitlist', icon: Clock },
  ];

  const today = new Date().toISOString().split('T')[0];

  return (
    <div>
      {/* HEADER */}
      <section className="relative pt-40 pb-20 bg-brand-black overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-gold-500 rounded-full blur-3xl translate-x-1/2 translate-y-1/2"></div>
        </div>
        <div className="container-max px-6 md:px-12 lg:px-20 relative z-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-400 mb-4">Get in Touch</p>
          <h1 className="font-serif text-5xl md:text-6xl text-white mb-6">Let's Start a Conversation</h1>
          <p className="text-lg text-brand-cream/80 max-w-2xl mx-auto leading-relaxed">
            Whether you're ready to book a tour, have questions about our services, or want to join our waitlist — we're here to help your family find peace of mind.
          </p>
        </div>
      </section>

      {/* CONTACT INFO BAR */}
      <section className="bg-white border-b border-brand-softgrey">
        <div className="container-max px-6 md:px-12 lg:px-20 py-10">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { icon: Phone, label: 'Call Us', value: '+1 (876) 555-0192' },
              { icon: Mail, label: 'Email Us', value: 'care@peartserenity.com' },
              { icon: MapPin, label: 'Visit Us', value: 'Montego Bay, St. James, Jamaica' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gold-50 flex items-center justify-center flex-shrink-0">
                  <item.icon className="h-6 w-6 text-gold-600" />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-brand-textgrey font-semibold">{item.label}</p>
                  <p className="text-brand-black font-medium">{item.value}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FORM SECTION */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="max-w-3xl mx-auto">
            <div className="flex flex-col sm:flex-row gap-3 mb-10">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setMode(tab.id)}
                  className={`flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-2xl font-semibold text-sm uppercase tracking-wider transition-all duration-300 ${
                    mode === tab.id ? 'bg-gold-500 text-brand-black shadow-lg' : 'bg-white text-brand-textgrey hover:bg-gold-50'
                  }`}
                >
                  <tab.icon className="h-5 w-5" />
                  {tab.label}
                </button>
              ))}
            </div>

            {success && (
              <div className="mb-8 bg-gold-50 border-2 border-gold-200 rounded-2xl p-8 text-center animate-fade-in">
                <CheckCircle2 className="h-12 w-12 text-gold-600 mx-auto mb-4" />
                <h3 className="font-serif text-2xl text-brand-black mb-2">Thank You!</h3>
                <p className="text-brand-textgrey mb-4">
                  {mode === 'tour' && 'Your tour request has been received. Our team will contact you within 24 hours to confirm your appointment.'}
                  {mode === 'inquiry' && 'Your message has been sent. We will respond within 24 hours.'}
                  {mode === 'waitlist' && 'You have been added to our waitlist. We will contact you as soon as a suitable placement becomes available.'}
                </p>
                <button onClick={() => setSuccess(false)} className="text-gold-600 font-semibold text-sm hover:underline">Submit another request</button>
              </div>
            )}

            {error && (
              <div className="mb-8 bg-red-50 border-2 border-red-200 rounded-2xl p-6 flex items-start gap-3 animate-fade-in">
                <AlertCircle className="h-6 w-6 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-red-800">Something went wrong</p>
                  <p className="text-red-600 text-sm mt-1">{error}</p>
                </div>
              </div>
            )}

            {mode === 'tour' && !success && (
              <form onSubmit={handleTourSubmit} className="bg-white rounded-3xl shadow-xl p-8 md:p-10 animate-fade-in">
                <h2 className="font-serif text-3xl text-brand-black mb-2">Book a Facility Tour</h2>
                <p className="text-brand-textgrey mb-8">Schedule a personal visit to our Montego Bay residence.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div><label className="label-field">Full Name *</label><input type="text" required value={tourForm.name} onChange={(e) => setTourForm({ ...tourForm, name: e.target.value })} className="input-field" placeholder="Jane Doe" /></div>
                  <div><label className="label-field">Email *</label><input type="email" required value={tourForm.email} onChange={(e) => setTourForm({ ...tourForm, email: e.target.value })} className="input-field" placeholder="jane@example.com" /></div>
                  <div><label className="label-field">Phone</label><input type="tel" value={tourForm.phone} onChange={(e) => setTourForm({ ...tourForm, phone: e.target.value })} className="input-field" placeholder="+1 (876) 555-0100" /></div>
                  <div><label className="label-field">Party Size</label><select value={tourForm.party_size} onChange={(e) => setTourForm({ ...tourForm, party_size: parseInt(e.target.value) })} className="input-field">{[1, 2, 3, 4, 5, 6].map((n) => <option key={n} value={n}>{n} {n === 1 ? 'person' : 'people'}</option>)}</select></div>
                  <div><label className="label-field">Preferred Date *</label><input type="date" required min={today} value={tourForm.preferred_date} onChange={(e) => setTourForm({ ...tourForm, preferred_date: e.target.value })} className="input-field" /></div>
                  <div><label className="label-field">Preferred Time</label><select value={tourForm.preferred_time} onChange={(e) => setTourForm({ ...tourForm, preferred_time: e.target.value })} className="input-field"><option value="morning">Morning (9am - 12pm)</option><option value="afternoon">Afternoon (1pm - 5pm)</option></select></div>
                </div>
                <div className="mt-6"><label className="label-field">Special Requests</label><textarea rows={4} value={tourForm.message} onChange={(e) => setTourForm({ ...tourForm, message: e.target.value })} className="input-field resize-none" placeholder="Any specific areas you'd like to see or questions you have..." /></div>
                <button type="submit" disabled={submitting} className="btn-primary w-full mt-8 disabled:opacity-60">{submitting ? 'Sending...' : 'Request Tour'} <Send className="h-4 w-4" /></button>
              </form>
            )}

            {mode === 'inquiry' && !success && (
              <form onSubmit={handleInquirySubmit} className="bg-white rounded-3xl shadow-xl p-8 md:p-10 animate-fade-in">
                <h2 className="font-serif text-3xl text-brand-black mb-2">Send Us a Message</h2>
                <p className="text-brand-textgrey mb-8">Have questions about our services, pricing, or care options?</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div><label className="label-field">Full Name *</label><input type="text" required value={inquiryForm.name} onChange={(e) => setInquiryForm({ ...inquiryForm, name: e.target.value })} className="input-field" placeholder="Jane Doe" /></div>
                  <div><label className="label-field">Email *</label><input type="email" required value={inquiryForm.email} onChange={(e) => setInquiryForm({ ...inquiryForm, email: e.target.value })} className="input-field" placeholder="jane@example.com" /></div>
                  <div><label className="label-field">Phone</label><input type="tel" value={inquiryForm.phone} onChange={(e) => setInquiryForm({ ...inquiryForm, phone: e.target.value })} className="input-field" placeholder="+1 (876) 555-0100" /></div>
                  <div><label className="label-field">Country</label><select value={inquiryForm.country} onChange={(e) => setInquiryForm({ ...inquiryForm, country: e.target.value })} className="input-field"><option value="Jamaica">Jamaica</option><option value="USA">United States</option><option value="UK">United Kingdom</option><option value="Canada">Canada</option><option value="Other">Other</option></select></div>
                  <div><label className="label-field">Service of Interest</label><select value={inquiryForm.service_type} onChange={(e) => setInquiryForm({ ...inquiryForm, service_type: e.target.value })} className="input-field"><option value="general">General Inquiry</option><option value="day_care">Adult Day Care</option><option value="respite">Respite Care</option><option value="long_term">Long-Term Residential</option><option value="private_suite">Private Suite</option><option value="recovery">Post-Surgical Recovery</option><option value="specialized">Specialized Care</option></select></div>
                  <div><label className="label-field">Preferred Start Date</label><input type="date" min={today} value={inquiryForm.preferred_date} onChange={(e) => setInquiryForm({ ...inquiryForm, preferred_date: e.target.value })} className="input-field" /></div>
                </div>
                <div className="mt-6"><label className="label-field">Your Message *</label><textarea rows={5} required value={inquiryForm.message} onChange={(e) => setInquiryForm({ ...inquiryForm, message: e.target.value })} className="input-field resize-none" placeholder="Tell us about your loved one's needs, your timeline, and any questions you have..." /></div>
                <button type="submit" disabled={submitting} className="btn-primary w-full mt-8 disabled:opacity-60">{submitting ? 'Sending...' : 'Send Message'} <Send className="h-4 w-4" /></button>
              </form>
            )}

            {mode === 'waitlist' && !success && (
              <form onSubmit={handleWaitlistSubmit} className="bg-white rounded-3xl shadow-xl p-8 md:p-10 animate-fade-in">
                <h2 className="font-serif text-3xl text-brand-black mb-2">Join Our Waitlist</h2>
                <p className="text-brand-textgrey mb-8">Be the first to know when a placement becomes available.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div><label className="label-field">Full Name *</label><input type="text" required value={waitlistForm.name} onChange={(e) => setWaitlistForm({ ...waitlistForm, name: e.target.value })} className="input-field" placeholder="Jane Doe" /></div>
                  <div><label className="label-field">Email *</label><input type="email" required value={waitlistForm.email} onChange={(e) => setWaitlistForm({ ...waitlistForm, email: e.target.value })} className="input-field" placeholder="jane@example.com" /></div>
                  <div><label className="label-field">Phone</label><input type="tel" value={waitlistForm.phone} onChange={(e) => setWaitlistForm({ ...waitlistForm, phone: e.target.value })} className="input-field" placeholder="+1 (876) 555-0100" /></div>
                  <div><label className="label-field">Country</label><select value={waitlistForm.country} onChange={(e) => setWaitlistForm({ ...waitlistForm, country: e.target.value })} className="input-field"><option value="Jamaica">Jamaica</option><option value="USA">United States</option><option value="UK">United Kingdom</option><option value="Canada">Canada</option><option value="Other">Other</option></select></div>
                  <div><label className="label-field">Type of Care Needed</label><select value={waitlistForm.care_type} onChange={(e) => setWaitlistForm({ ...waitlistForm, care_type: e.target.value })} className="input-field"><option value="long_term">Long-Term Residential</option><option value="private_suite">Private Suite</option><option value="respite">Respite Care</option><option value="recovery">Post-Surgical Recovery</option><option value="specialized">Specialized Care</option></select></div>
                  <div><label className="label-field">Urgency</label><select value={waitlistForm.urgency} onChange={(e) => setWaitlistForm({ ...waitlistForm, urgency: e.target.value })} className="input-field"><option value="low">Low — Exploring options</option><option value="medium">Medium — Within 3 months</option><option value="high">High — Immediate need</option></select></div>
                </div>
                <div className="mt-6"><label className="label-field">Additional Notes</label><textarea rows={4} value={waitlistForm.notes} onChange={(e) => setWaitlistForm({ ...waitlistForm, notes: e.target.value })} className="input-field resize-none" placeholder="Any specific needs, conditions, or timing considerations..." /></div>
                <button type="submit" disabled={submitting} className="btn-primary w-full mt-8 disabled:opacity-60">{submitting ? 'Joining...' : 'Join Waitlist'} <Send className="h-4 w-4" /></button>
              </form>
            )}
          </div>
        </div>
      </section>

      {/* DIASPORA INFO */}
      <section className="section-padding bg-brand-black">
        <div className="container-max">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            {[
              { icon: Plane, title: 'Diaspora Families', desc: 'We welcome families from the US, UK, Canada, and beyond. Virtual tours available for those who cannot visit in person.' },
              { icon: Heart, title: 'Compassionate Team', desc: 'Our staff speaks English and understands the cultural nuances that make Jamaican eldercare unique.' },
              { icon: Users, title: 'Family Support', desc: 'We support the whole family — not just the resident. Ask about our family counseling and transition support services.' },
            ].map((item) => (
              <div key={item.title} className="p-8">
                <item.icon className="h-10 w-10 text-gold-400 mx-auto mb-4" />
                <h3 className="font-serif text-xl text-white mb-2">{item.title}</h3>
                <p className="text-brand-cream/70 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
