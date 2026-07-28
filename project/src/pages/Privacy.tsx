import {
  ShieldCheck,
  Database,
  Settings2,
  HeartPulse,
  Share2,
  Lock,
  Clock,
  UserCog,
  Cookie,
  Baby,
  Globe2,
  RotateCcw,
  Mail,
} from 'lucide-react';

const sections = [
  { id: 'intro', label: 'Introduction', icon: ShieldCheck },
  { id: 'collect', label: 'Information We Collect', icon: Database },
  { id: 'use', label: 'How We Use It', icon: Settings2 },
  { id: 'medical', label: 'Health & Medical Information', icon: HeartPulse },
  { id: 'share', label: 'How We Share Information', icon: Share2 },
  { id: 'security', label: 'Data Security', icon: Lock },
  { id: 'retention', label: 'Data Retention', icon: Clock },
  { id: 'rights', label: 'Your Rights & Choices', icon: UserCog },
  { id: 'cookies', label: 'Cookies & Analytics', icon: Cookie },
  { id: 'children', label: "Children's Privacy", icon: Baby },
  { id: 'international', label: 'Diaspora & International Data', icon: Globe2 },
  { id: 'changes', label: 'Changes to This Policy', icon: RotateCcw },
  { id: 'contact', label: 'Contact Us', icon: Mail },
];

export default function Privacy() {
  return (
    <div>
      {/* HEADER */}
      <section className="relative pt-40 pb-20 bg-brand-black overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-gold-500 rounded-full blur-3xl -translate-x-1/2 translate-y-1/2"></div>
        </div>
        <div className="container-max px-6 md:px-12 lg:px-20 relative z-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-400 mb-4">Legal</p>
          <h1 className="font-serif text-5xl md:text-6xl text-white mb-6">Privacy Policy</h1>
          <p className="text-lg text-brand-cream/80 max-w-2xl mx-auto leading-relaxed">
            How Peart Serenity Residence collects, uses, and protects your personal and medical information.
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
              <div id="intro" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">1. Introduction</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  Peart Serenity Residence ("we", "us", "our") respects your privacy and that of our residents and their families. This Privacy Policy explains what information we collect through our website and care-related forms, how we use it, and the choices you have. By using this website or submitting a form to us, you agree to the practices described here.
                </p>
              </div>

              <div id="collect" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">2. Information We Collect</h2>
                <ul className="space-y-2 text-brand-textgrey leading-relaxed list-disc pl-5">
                  <li><span className="font-semibold text-brand-black">Contact details</span> — name, email, phone number, and country, submitted through our contact, tour, and waitlist forms.</li>
                  <li><span className="font-semibold text-brand-black">Care assessment information</span> — details submitted through our Resident Application &amp; Care Assessment Form, including the prospective resident's health status, mobility, cognition, medications, allergies, and emergency contacts.</li>
                  <li><span className="font-semibold text-brand-black">Payment &amp; billing details</span> — information about the responsible payer, such as name, relationship to the resident, and country, used to prepare invoices.</li>
                  <li><span className="font-semibold text-brand-black">Account information</span> — if you register for our family dashboard, we collect login credentials and associated resident information.</li>
                  <li><span className="font-semibold text-brand-black">Careers information</span> — resumes and application details submitted through our Careers page.</li>
                  <li><span className="font-semibold text-brand-black">Technical data</span> — basic website usage data such as pages visited, used to keep the site secure and working properly.</li>
                </ul>
              </div>

              <div id="use" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">3. How We Use It</h2>
                <p className="text-brand-textgrey leading-relaxed mb-3">We use the information we collect to:</p>
                <ul className="space-y-2 text-brand-textgrey leading-relaxed list-disc pl-5">
                  <li>Respond to inquiries, schedule tours, and manage waitlist requests;</li>
                  <li>Assess care needs and prepare accurate, personalized quotations;</li>
                  <li>Coordinate admission, care planning, and ongoing resident support;</li>
                  <li>Communicate with families, including overseas relatives, about a resident's wellbeing;</li>
                  <li>Process payments and manage billing;</li>
                  <li>Evaluate job applications; and</li>
                  <li>Improve our website and services.</li>
                </ul>
              </div>

              <div id="medical" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">4. Health &amp; Medical Information</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  Health and medical information is sensitive personal data. We collect it only to assess the level of care a prospective resident needs and to deliver safe, appropriate care once admitted. Access to medical information is limited to our clinical staff (nursing team, administrator), the resident's visiting physician, and contracted specialists directly involved in the resident's care, in keeping with applicable confidentiality standards and Jamaican law.
                </p>
              </div>

              <div id="share" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">5. How We Share Information</h2>
                <p className="text-brand-textgrey leading-relaxed mb-3">
                  We do not sell your personal information. We may share information only:
                </p>
                <ul className="space-y-2 text-brand-textgrey leading-relaxed list-disc pl-5">
                  <li>With our clinical and care staff, and contracted healthcare providers (e.g., visiting physician, physiotherapist), strictly for care purposes;</li>
                  <li>With our secure backend systems and service providers who process data on our behalf (for example, our practice-management platform), under confidentiality obligations;</li>
                  <li>With payment processors necessary to complete billing you have requested;</li>
                  <li>Where required by law, regulation, or a valid request from Jamaican authorities; or</li>
                  <li>With your consent, such as when you ask us to coordinate with an external physician or insurer.</li>
                </ul>
              </div>

              <div id="security" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">6. Data Security</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  We apply reasonable administrative, technical, and physical safeguards to protect personal and medical information against unauthorized access, loss, or misuse, including restricted staff access and secure storage of records. No system is completely secure, and we continuously work to maintain appropriate safeguards as our systems evolve.
                </p>
              </div>

              <div id="retention" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">7. Data Retention</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  We retain inquiry and waitlist information only as long as needed to respond to your request. Resident care and medical records are retained for as long as required for continuity of care, legal, and healthcare recordkeeping obligations, after which they are securely deleted or anonymized.
                </p>
              </div>

              <div id="rights" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">8. Your Rights &amp; Choices</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  You may ask us to access, correct, or delete the personal information we hold about you or your loved one, subject to our legal and clinical recordkeeping obligations. You may also withdraw consent for non-essential communications at any time. To exercise these rights, contact us using the details below.
                </p>
              </div>

              <div id="cookies" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">9. Cookies &amp; Analytics</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  Our website may use minimal cookies or similar technologies necessary for the site to function and, where enabled, basic analytics to understand how visitors use the site. We do not use this data for third-party advertising profiling.
                </p>
              </div>

              <div id="children" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">10. Children's Privacy</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  Our services are intended for the care of elderly adults, and our website is not directed at children. We do not knowingly collect personal information from children.
                </p>
              </div>

              <div id="international" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">11. Diaspora &amp; International Data</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  Many of our families live outside Jamaica. If you contact us or submit forms from abroad, your information may be transmitted to and processed in Jamaica, where our residence and systems are based. We take steps to protect your information consistently, regardless of where it is accessed from.
                </p>
              </div>

              <div id="changes" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">12. Changes to This Policy</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  We may update this Privacy Policy from time to time to reflect changes in our practices or legal requirements. The "Last updated" date at the top of this page shows when it was last revised. We encourage you to review this page periodically.
                </p>
              </div>

              <div id="contact" className="scroll-mt-28">
                <h2 className="font-serif text-2xl text-brand-black mb-3">13. Contact Us</h2>
                <p className="text-brand-textgrey leading-relaxed">
                  For questions about this Privacy Policy or to exercise your data rights, contact us at{' '}
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
