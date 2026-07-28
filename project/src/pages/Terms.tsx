import {
  FileText,
  UserCheck,
  Banknote,
  RefreshCcw,
  ClipboardList,
  Stethoscope,
  Globe,
  ShieldAlert,
  Lock,
  Scale,
  RotateCcw,
  Mail,
} from 'lucide-react';

const sections = [
  { id: 'acceptance', label: 'Acceptance of Terms', icon: FileText },
  { id: 'services', label: 'About Our Services', icon: ClipboardList },
  { id: 'admission', label: 'Eligibility & Admission', icon: UserCheck },
  { id: 'payment', label: 'Fees, Payment & Billing', icon: Banknote },
  { id: 'cancellation', label: 'Cancellations & Refunds', icon: RefreshCcw },
  { id: 'conduct', label: 'Conduct & Responsibilities', icon: ShieldAlert },
  { id: 'medical', label: 'Health & Medical Disclaimer', icon: Stethoscope },
  { id: 'website', label: 'Website Use & Content', icon: Globe },
  { id: 'liability', label: 'Limitation of Liability', icon: Scale },
  { id: 'privacy', label: 'Confidentiality & Data', icon: Lock },
  { id: 'changes', label: 'Changes to These Terms', icon: RotateCcw },
  { id: 'contact', label: 'Contact Us', icon: Mail },
];

export default function Terms() {
  return (
    <div>
      {/* HEADER */}
      <section className="relative pt-40 pb-20 bg-brand-black overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gold-500 rounded-full blur-3xl translate-x-1/2"></div>
        </div>
        <div className="container-max px-6 md:px-12 lg:px-20 relative z-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-400 mb-4">Legal</p>
          <h1 className="font-serif text-5xl md:text-6xl text-white mb-6">Terms &amp; Conditions</h1>
          <p className="text-lg text-brand-cream/80 max-w-2xl mx-auto leading-relaxed">
            Please read these terms carefully before using our website or requesting care services from Peart Serenity Residence.
          </p>
          <p className="text-sm text-gold-300 mt-4">Last updated: July 27, 2026</p>
        </div>
      </section>

      {/* BODY */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-10">
            {/* TOC */}
            <aside className="lg:sticky lg:top-28 lg:self-start">
              <div className="flex lg:flex-col gap-2 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
                {sections.map((s) => {
                  const Icon = s.icon;
                  return (
                    <a
                      key={s.id}
                      href={`#${s.id}`}
                      className="flex items-center gap-3 flex-shrink-0 lg:flex-shrink text-left px-4 py-3 rounded-xl text-sm font-medium text-brand-textgrey bg-white hover:bg-gold-50 hover:text-gold-700 transition-colors duration-200 whitespace-nowrap lg:whitespace-normal"
                    >
                      <Icon className="h-4 w-4 flex-shrink-0 text-gold-600" />
                      {s.label}
                    </a>
                  );
                })}
              </div>
            </aside>

            {/* CONTENT */}
            <div className="bg-white rounded-3xl shadow-lg p-8 md:p-12 space-y-12">
              <div id="acceptance" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">1. Acceptance of Terms</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  By accessing this website or submitting any form — including a quote request, tour booking, waitlist signup, or resident application — you agree to be bound by these Terms &amp; Conditions. If you do not agree with any part of these terms, please do not use this website or our services. These terms apply to all visitors, prospective residents, family members, and payers acting on a resident's behalf.
                </p>
              </div>

              <div id="services" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">2. About Our Services</h2>
                <p className="text-brand-textgrey leading-relaxed mb-3">
                  Peart Serenity Residence provides long-term residential care, respite stays, day-care services, and post-surgery recovery support for seniors at our facility in Montego Bay, St. James, Jamaica. Information published on this website — including descriptions of services, amenities, and indicative pricing — is provided for general guidance only and does not constitute a binding offer or a guarantee of availability.
                </p>
                <p className="text-brand-textgrey leading-relaxed">
                  Final services, room assignment, and fees are confirmed only after a formal care assessment and written agreement between you and Peart Serenity Residence.
                </p>
              </div>

              <div id="admission" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">3. Eligibility &amp; Admission</h2>
                <p className="text-brand-textgrey leading-relaxed mb-3">
                  Admission is subject to completion of our Resident Application &amp; Care Assessment Form and, where required, an in-person or remote clinical assessment. We reserve the right to decline or defer admission where a prospective resident's medical or behavioural needs exceed the level of care we are licensed and equipped to safely provide.
                </p>
                <p className="text-brand-textgrey leading-relaxed">
                  The applicant confirms that all information provided — medical history, current conditions, and emergency contacts — is true, complete, and provided with the resident's consent (or that of their legal representative).
                </p>
              </div>

              <div id="payment" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">4. Fees, Payment &amp; Billing</h2>
                <p className="text-brand-textgrey leading-relaxed mb-3">
                  Fees are determined by the assessed level of care and selected accommodation, as set out in your written quotation. Rates published on our Services page are indicative ranges and may change. A deposit may be required to confirm a placement.
                </p>
                <p className="text-brand-textgrey leading-relaxed">
                  Payment may be made by the resident, a local family member, or an overseas relative acting as payer. We accept direct billing arrangements, monthly payment plans, and diaspora wire transfers; where insurance coverage applies, we will assist with direct billing to the provider where possible. Invoices are due on the schedule stated in your admission agreement, and late payment may affect continuity of services.
                </p>
              </div>

              <div id="cancellation" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">5. Cancellations &amp; Refunds</h2>
                <p className="text-brand-textgrey leading-relaxed mb-3">
                  Tour bookings and waitlist entries may be cancelled or rescheduled at any time at no charge by contacting our team.
                </p>
                <p className="text-brand-textgrey leading-relaxed">
                  For respite, day-care, and post-surgery recovery bookings, cancellation and refund terms (including any notice period required to avoid forfeiting a deposit) will be specified in your individual booking confirmation or admission agreement. For long-term residential care, notice periods for discharge or transfer are set out in the admission agreement signed at intake.
                </p>
              </div>

              <div id="conduct" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">6. Conduct &amp; Responsibilities</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  Residents, family members, and visitors are expected to treat our staff, other residents, and the facility with respect. We ask families to keep us promptly informed of any change in a resident's health, medication, or emergency contact details. Peart Serenity Residence reserves the right to restrict visitation or, in serious cases, to end a care arrangement where conduct threatens the safety or wellbeing of residents or staff.
                </p>
              </div>

              <div id="medical" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">7. Health &amp; Medical Disclaimer</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  Content on this website is provided for general informational purposes only and is not medical advice. While our team includes qualified nursing staff and coordinates with a visiting physician and specialist contractors, any specific medical decision should be discussed directly with the resident's care team and personal physician. In a medical emergency, our staff will act in the resident's best interest and contact emergency services and next of kin as appropriate.
                </p>
              </div>

              <div id="website" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">8. Website Use &amp; Content</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  All text, images, logos, and branding on this website are the property of Peart Serenity Residence unless otherwise credited, and may not be reproduced without permission. You agree not to misuse the website, attempt unauthorized access to our systems, or submit false information through our forms.
                </p>
              </div>

              <div id="liability" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">9. Limitation of Liability</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  To the fullest extent permitted by law, Peart Serenity Residence is not liable for indirect, incidental, or consequential damages arising from your use of this website or reliance on general information published here. Our liability in connection with care services provided is governed by the written admission agreement and applicable Jamaican law, not by this website.
                </p>
              </div>

              <div id="privacy" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">10. Confidentiality &amp; Data</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  Personal and medical information you share with us — including through our forms — is handled in accordance with our{' '}
                  <a href="/privacy" className="text-gold-600 font-semibold hover:underline">Privacy Policy</a>, confidentiality obligations under Jamaican law, and standard healthcare recordkeeping practices.
                </p>
              </div>

              <div id="changes" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">11. Changes to These Terms</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  We may update these Terms &amp; Conditions from time to time to reflect changes in our services or legal requirements. The "Last updated" date at the top of this page indicates when the terms were last revised. Continued use of the website after changes are posted constitutes acceptance of the updated terms.
                </p>
              </div>

              <div id="contact" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">12. Contact Us</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  Questions about these Terms &amp; Conditions can be sent to{' '}
                  <a href="mailto:care@peartserenity.com" className="text-gold-600 font-semibold hover:underline">care@peartserenity.com</a>{' '}
                  or by calling +1 (876) 555-0192. Our residence is located in Montego Bay, St. James Parish, Jamaica.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
