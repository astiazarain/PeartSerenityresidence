import { useState } from 'react';
import {
  HelpCircle,
  ClipboardList,
  HeartPulse,
  Banknote,
  ShieldCheck,
  Users,
  Plane,
  Stethoscope,
  ChevronDown,
} from 'lucide-react';
import CTASection from '../components/CTASection';

type Question = { q: string; a: string };
type Category = {
  id: string;
  label: string;
  icon: typeof HelpCircle;
  questions: Question[];
};

const categories: Category[] = [
  {
    id: 'general',
    label: 'General',
    icon: HelpCircle,
    questions: [
      {
        q: 'What is Peart Serenity Residence?',
        a: 'Peart Serenity Residence is a premium senior care and wellness residence in Montego Bay, Jamaica. We pair professional nursing care with the warmth of Caribbean hospitality, creating a safe, dignified, and emotionally supportive home for elderly residents — our promise is simple: care that feels like home, not an institution.',
      },
      {
        q: 'Where are you located?',
        a: 'Our residence is located in Montego Bay, St. James Parish, Jamaica — close to medical facilities and the international airport, which makes it easy for diaspora families to visit.',
      },
      {
        q: 'Is Peart Serenity Residence licensed?',
        a: 'We operate as a licensed residential and assisted-care facility and are built from day one to meet and exceed Jamaican healthcare facility standards, working closely with regulators to maintain compliance.',
      },
      {
        q: 'What makes Peart Serenity different from other homes in Jamaica?',
        a: 'We combine clinical credibility, a true home-like environment, and structured family communication — including scheduled updates and video calls — rather than the ad hoc communication and institutional setting common at many local providers.',
      },
      {
        q: "What is your philosophy of care?",
        a: 'Every resident is treated as a valued individual, never as a patient to be processed. Our care is guided by compassion, dignity, professionalism, safety, respect for cultural and religious preferences, and genuine human connection.',
      },
    ],
  },
  {
    id: 'admissions',
    label: 'Admissions & Assessment',
    icon: ClipboardList,
    questions: [
      {
        q: 'How do I apply for a place at Peart Serenity?',
        a: 'Start by requesting a quote or booking a tour through our website. We will guide you through a Resident Application & Care Assessment Form that helps us understand the exact level of care your loved one needs.',
      },
      {
        q: 'What is the admission and assessment process?',
        a: 'After you submit an application, our nursing team reviews the health and care details provided — mobility, cognition, continence, daily-living needs, and any special medical requirements — and may carry out a clinical assessment before admission to confirm the appropriate care level and room placement.',
      },
      {
        q: 'What documents do I need to provide?',
        a: 'Where available, please provide the resident’s ID or TRN, medical records or a hospital discharge summary, a current medication list, recent lab results, and a physician referral. The more detail you can share, the more accurate your quotation will be.',
      },
      {
        q: 'Is there a waiting list?',
        a: 'As a boutique residence, availability can be limited. If a placement isn’t immediately available, we invite you to join our waitlist and we will contact you as soon as a suitable placement opens up.',
      },
      {
        q: 'How soon can my loved one move in after approval?',
        a: 'Move-in timing depends on room availability and any final clinical checks, but we work to make the transition as fast and smooth as possible once an assessment is complete and a start date is agreed.',
      },
      {
        q: "What if my loved one's care needs change after admission?",
        a: 'Our team continuously monitors resident wellbeing. If care needs increase or change, we reassess the care plan and, where necessary, adjust services and fees to match the new level of support required.',
      },
    ],
  },
  {
    id: 'services',
    label: 'Services & Levels of Care',
    icon: HeartPulse,
    questions: [
      {
        q: 'What types of care do you offer?',
        a: 'We offer long-term residential care, short-term respite stays, day-care services, and post-surgery recovery support — so families can choose the arrangement that fits their situation, whether that’s permanent care or temporary relief.',
      },
      {
        q: 'Do you care for residents with dementia or Alzheimer’s?',
        a: 'Yes. We provide early-stage Alzheimer’s and dementia support as part of our specialized services, with staff trained to manage memory-related and behavioural needs with patience and dignity.',
      },
      {
        q: 'What specialized medical support is available?',
        a: 'Beyond core nursing care, we support diabetes management, hypertension monitoring, mobility assistance and fall prevention, wound care coordination, and other complex medical needs identified during assessment.',
      },
      {
        q: 'What does a typical day look like for residents?',
        a: 'Daily life balances care with engagement: light exercise and guided stretching, music therapy, cognitive games and reading, gardening, arts and crafts, social gatherings, and movie afternoons — plus Caribbean cultural activities and scheduled family video calls.',
      },
      {
        q: 'Do you provide physiotherapy and rehabilitation?',
        a: 'Yes, we coordinate physiotherapy and rehabilitation support, including for residents recovering from surgery or managing ongoing mobility conditions.',
      },
    ],
  },
  {
    id: 'pricing',
    label: 'Pricing & Payment',
    icon: Banknote,
    questions: [
      {
        q: 'How much does care cost?',
        a: 'Rates depend on the type and level of care. As a general guide: day care runs roughly $40–$60/day, weekly respite stays $550–$900/week, shared long-term residence $1,900–$2,600/month, private premium suites $3,200–$5,000/month, and post-surgery recovery $140–$250/day. Visit our Services & Pricing page or request a quote for exact figures.',
      },
      {
        q: 'How is the care level and rate determined?',
        a: 'Your quoted rate is based on an assessed care level (from Level 1 — low needs, to Level 4 — specialized/complex care) determined from mobility, cognition, continence, daily-living dependence, and any special medical needs identified in the assessment.',
      },
      {
        q: 'What payment methods do you accept, including from overseas?',
        a: 'We accept payment from residents, local family members, or overseas relatives, and offer flexible options including monthly payment plans and diaspora-friendly wire transfer arrangements so family abroad can pay directly.',
      },
      {
        q: 'Is a deposit required?',
        a: 'A deposit may be required depending on the assessed care plan and room type; this is confirmed as part of your personalized quotation before admission.',
      },
      {
        q: 'Do you accept health insurance?',
        a: 'We work with most major insurance providers and offer direct insurance billing where applicable. Our team will help you understand your coverage options and the most affordable path to quality care.',
      },
      {
        q: 'Can family members abroad pay directly?',
        a: 'Yes. Many of our families are overseas Jamaicans or diaspora relatives financing care remotely. You can be listed as the responsible payer on the application, and billing can be sent directly to you by email.',
      },
    ],
  },
  {
    id: 'facility',
    label: 'Facility, Safety & Daily Life',
    icon: ShieldCheck,
    questions: [
      {
        q: 'What safety measures are in place?',
        a: '24/7 security monitoring, emergency call systems in every room, fire safety systems with regular drills, non-slip flooring, grab bars in all bathrooms, secured entrances and exits, CCTV, a backup generator, and staff trained in emergency response.',
      },
      {
        q: 'What room options are available?',
        a: 'We offer both shared and private premium suites, all in comfortable, climate-controlled accommodations with accessible bathrooms and safety features built in.',
      },
      {
        q: 'What meals and dietary accommodations are provided?',
        a: 'Our dining room serves Caribbean cuisine prepared in-house, with accommodations for diabetic, low-salt, soft, and pureed diets, plus feeding assistance for residents who need it.',
      },
      {
        q: 'Can residents bring personal belongings?',
        a: 'Yes, we encourage residents to personalize their rooms with familiar items, photos, and keepsakes to help the space feel like home.',
      },
      {
        q: 'Is there 24/7 staff supervision?',
        a: 'Yes. Our nursing station is staffed around the clock, with a Registered Nurse providing clinical supervision and nursing assistants covering shifts to ensure continuous personal care.',
      },
    ],
  },
  {
    id: 'family',
    label: 'Family, Visits & Communication',
    icon: Users,
    questions: [
      {
        q: 'Can family visit anytime?',
        a: 'We welcome regular family visits. Reach out to our team to confirm current visiting arrangements so we can make sure your loved one is ready to receive you.',
      },
      {
        q: 'How do you keep overseas family updated?',
        a: 'We maintain a structured family-communication cadence, including scheduled updates and family video calls, so relatives abroad stay closely connected to their loved one’s wellbeing.',
      },
      {
        q: 'Can I schedule a tour before deciding?',
        a: 'Absolutely — we encourage it. You can book a tour of our Montego Bay residence directly from our Contact page, and virtual tours are available for families who cannot visit in person.',
      },
      {
        q: 'Who do I contact in an emergency?',
        a: 'Your family will always have a direct line to our care team. In an emergency, our on-site nursing staff and administrator coordinate immediately with the resident’s emergency contact and, where needed, the visiting physician.',
      },
    ],
  },
  {
    id: 'diaspora',
    label: 'Diaspora & International Families',
    icon: Plane,
    questions: [
      {
        q: 'I live abroad — can I manage everything remotely?',
        a: 'Yes. Many of our families are Jamaicans living overseas or expatriates. You can complete the application, receive your quotation, arrange payment, and stay updated on care — all remotely.',
      },
      {
        q: 'Do you offer virtual tours?',
        a: 'Yes, virtual tours are available for diaspora families who are unable to visit Montego Bay in person before making a decision.',
      },
      {
        q: 'How does payment work from the US, UK, or Canada?',
        a: 'We support diaspora wire transfers and flexible billing arranged directly with the overseas payer, so you can cover a parent or relative’s care from wherever you live.',
      },
      {
        q: 'Will staff communicate in English?',
        a: 'Yes, our team communicates in English and understands the cultural nuances that make Jamaican eldercare unique, so overseas families always feel informed and involved.',
      },
    ],
  },
  {
    id: 'staff',
    label: 'Staff & Qualifications',
    icon: Stethoscope,
    questions: [
      {
        q: 'What are your staff qualifications?',
        a: 'Our team includes a Registered Nurse for clinical supervision and care planning, trained nursing assistants for daily personal care, and a General Administrator with nursing experience serving as clinical lead.',
      },
      {
        q: 'Is a nurse on-site at all times?',
        a: 'Our nursing station provides 24/7 staffed supervision, with a Registered Nurse overseeing clinical care and nursing assistants covering shifts around the clock.',
      },
      {
        q: 'Do you have a visiting physician?',
        a: 'Yes, we retain a visiting physician for medical oversight, along with contracted specialists such as a physiotherapist and a nutrition specialist for meal planning.',
      },
      {
        q: 'How do you train and vet your caregivers?',
        a: 'Staff are hired against clinical and character standards, trained on our written care protocols, medication logs, infection-control procedures, and emergency response, and are continually developed as part of our investment in care quality.',
      },
    ],
  },
];

export default function FAQ() {
  const [activeCat, setActiveCat] = useState(categories[0].id);
  const [openItems, setOpenItems] = useState<Set<string>>(new Set());

  const toggle = (key: string) => {
    setOpenItems((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const current = categories.find((c) => c.id === activeCat)!;

  return (
    <div>
      {/* HEADER */}
      <section className="relative pt-40 pb-20 bg-brand-black overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-gold-500 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
        </div>
        <div className="container-max px-6 md:px-12 lg:px-20 relative z-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-400 mb-4">Have Questions?</p>
          <h1 className="font-serif text-5xl md:text-6xl text-white mb-6">Frequently Asked Questions</h1>
          <p className="text-lg text-brand-cream/80 max-w-2xl mx-auto leading-relaxed">
            Everything families ask us about admissions, care, pricing, and daily life at Peart Serenity Residence — organized by topic.
          </p>
        </div>
      </section>

      {/* FAQ BODY */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-10">
            {/* SIDEBAR */}
            <aside className="lg:sticky lg:top-28 lg:self-start">
              <div className="flex lg:flex-col gap-3 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
                {categories.map((cat) => {
                  const Icon = cat.icon;
                  const isActive = activeCat === cat.id;
                  return (
                    <button
                      key={cat.id}
                      onClick={() => setActiveCat(cat.id)}
                      className={`flex items-center gap-3 flex-shrink-0 lg:flex-shrink lg:w-full text-left px-5 py-4 rounded-2xl font-semibold text-sm transition-all duration-300 ${
                        isActive ? 'bg-gold-500 text-brand-black shadow-lg' : 'bg-white text-brand-textgrey hover:bg-gold-50'
                      }`}
                    >
                      <Icon className="h-5 w-5 flex-shrink-0" />
                      <span className="whitespace-nowrap lg:whitespace-normal">{cat.label}</span>
                    </button>
                  );
                })}
              </div>
            </aside>

            {/* CONTENT */}
            <div>
              <div className="flex items-center gap-4 mb-8 animate-fade-in" key={current.id}>
                <div className="w-14 h-14 rounded-2xl bg-gold-100 flex items-center justify-center flex-shrink-0">
                  <current.icon className="h-7 w-7 text-gold-600" />
                </div>
                <h2 className="font-serif text-3xl md:text-4xl text-brand-black">{current.label}</h2>
              </div>

              <div className="space-y-4">
                {current.questions.map((item, idx) => {
                  const key = `${current.id}-${idx}`;
                  const isOpen = openItems.has(key);
                  return (
                    <div key={key} className="bg-white rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-300 overflow-hidden">
                      <button
                        onClick={() => toggle(key)}
                        aria-expanded={isOpen}
                        className="w-full flex items-center justify-between gap-4 text-left px-6 py-5"
                      >
                        <span className="font-semibold text-brand-black">{item.q}</span>
                        <ChevronDown
                          className={`h-5 w-5 text-gold-600 flex-shrink-0 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}
                        />
                      </button>
                      <div className={`grid transition-all duration-300 ease-out ${isOpen ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}>
                        <div className="overflow-hidden">
                          <p className="px-6 pb-5 text-brand-textgrey leading-relaxed text-sm">{item.a}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </section>

      <CTASection />
    </div>
  );
}
