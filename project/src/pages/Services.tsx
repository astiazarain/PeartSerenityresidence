import { Link } from 'react-router-dom';
import {
  Sun,
  Clock,
  Home as HomeIcon,
  Sparkles,
  Activity,
  Stethoscope,
  Check,
  ArrowRight,
  Heart,
  Utensils,
  Dumbbell,
  Brain,
  Pill,
  ShowerHead,
  Users,
} from 'lucide-react';
import CTASection from '../components/CTASection';

export default function Services() {
  const services = [
    {
      icon: Sun,
      title: 'Adult Day Care',
      price: '$45',
      period: '/day',
      desc: 'Engaging daytime care for seniors who live at home but need supervised care and social interaction during the day.',
      features: [
        '8am - 6pm daily care',
        'Breakfast, lunch & snacks',
        'Group activities & social engagement',
        'Medication management',
        'Health monitoring',
        'Transportation assistance available',
      ],
      popular: false,
    },
    {
      icon: Clock,
      title: 'Respite Care',
      price: '$95',
      period: '/night',
      desc: 'Short-term overnight care giving family caregivers a well-deserved break — from a single night to several weeks.',
      features: [
        'Flexible duration (1 night to 4 weeks)',
        'Private or semi-private room',
        'All meals included',
        'Full access to amenities',
        'Personalized care plan',
        '24/7 nursing supervision',
      ],
      popular: false,
    },
    {
      icon: HomeIcon,
      title: 'Long-Term Residential',
      price: '$2,800',
      period: '/month',
      desc: 'Full-time residential care in a warm, home-like environment with 24/7 nursing supervision and personalized care plans.',
      features: [
        '24/7 nursing care & supervision',
        'Private or shared room options',
        'All meals (Caribbean & dietary options)',
        'Daily activities & wellness programs',
        'Medication management',
        'Weekly family video updates',
        'Monthly health assessments',
      ],
      popular: true,
    },
    {
      icon: Sparkles,
      title: 'Private Suites',
      price: '$4,200',
      period: '/month',
      desc: 'Our premium offering — spacious private suites with enhanced amenities and the highest level of personalized attention.',
      features: [
        'Everything in Long-Term Residential',
        'Spacious private suite with en-suite bathroom',
        'Premium furnishings & linens',
        'Personal care assistant',
        'Customized meal planning',
        'Priority activity scheduling',
        'Enhanced family communication package',
      ],
      popular: false,
    },
    {
      icon: Activity,
      title: 'Post-Surgical Recovery',
      price: '$120',
      period: '/day',
      desc: 'Clinical-grade nursing care for recovery after surgery, with physician-coordinated rehabilitation and monitoring.',
      features: [
        'Wound care & dressing changes',
        'Medication & pain management',
        'Physical therapy coordination',
        'Vital signs monitoring',
        'Physician coordination',
        'Discharge planning & family briefing',
      ],
      popular: false,
    },
    {
      icon: Stethoscope,
      title: 'Specialized Care',
      price: 'Custom',
      period: '',
      desc: 'Tailored care programs for residents with specific medical needs including diabetes, dementia, and mobility challenges.',
      features: [
        'Diabetes management & glucose monitoring',
        "Dementia & Alzheimer's care",
        'Mobility assistance & fall prevention',
        'Chronic condition management',
        'Specialized dietary plans',
        'Cognitive engagement programs',
      ],
      popular: false,
    },
  ];

  const includedServices = [
    { icon: Utensils, label: 'All Meals & Nutrition' },
    { icon: Pill, label: 'Medication Management' },
    { icon: ShowerHead, label: 'Personal Hygiene Care' },
    { icon: Dumbbell, label: 'Physical Activity Programs' },
    { icon: Brain, label: 'Cognitive Engagement' },
    { icon: Users, label: 'Social Activities' },
    { icon: Heart, label: 'Emotional Support' },
    { icon: Stethoscope, label: 'Health Monitoring' },
  ];

  return (
    <div>
      {/* HEADER */}
      <section className="relative pt-40 pb-20 bg-brand-black overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gold-500 rounded-full blur-3xl translate-x-1/2"></div>
        </div>
        <div className="container-max px-6 md:px-12 lg:px-20 relative z-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-400 mb-4">
            Services & Pricing
          </p>
          <h1 className="font-serif text-5xl md:text-6xl text-white mb-6">
            Care Plans for Every Family
          </h1>
          <p className="text-lg text-brand-cream/80 max-w-2xl mx-auto leading-relaxed">
            Transparent pricing. No hidden fees. Every plan includes our signature
            blend of clinical excellence and Caribbean warmth.
          </p>
        </div>
      </section>

      {/* PRICING CARDS */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {services.map((s, i) => (
              <div
                key={s.title}
                className={`relative bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 animate-slide-up flex flex-col ${
                  s.popular ? 'ring-2 ring-gold-500 lg:scale-105' : ''
                }`}
                style={{ animationDelay: `${i * 80}ms` }}
              >
                {s.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gold-500 text-brand-black text-xs font-semibold uppercase tracking-wider px-6 py-2 rounded-full shadow-lg">
                    Most Popular
                  </div>
                )}
                <div className="p-8 flex-1">
                  <div className="w-14 h-14 rounded-2xl bg-gold-50 flex items-center justify-center mb-6">
                    <s.icon className="h-7 w-7 text-gold-600" />
                  </div>
                  <h3 className="font-serif text-2xl text-brand-black mb-2">{s.title}</h3>
                  <p className="text-brand-textgrey leading-relaxed mb-6 text-sm">{s.desc}</p>
                  <div className="flex items-baseline gap-1 mb-6 pb-6 border-b border-brand-softgrey">
                    <span className="font-serif text-4xl font-bold text-gold-600">{s.price}</span>
                    <span className="text-brand-textgrey">{s.period}</span>
                  </div>
                  <ul className="space-y-3">
                    {s.features.map((f) => (
                      <li key={f} className="flex items-start gap-3 text-sm text-brand-textgrey">
                        <Check className="h-4 w-4 text-gold-500 flex-shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="p-8 pt-0">
                  <Link
                    to="/quote"
                    className={`w-full inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-semibold uppercase tracking-wider transition-all duration-300 ${
                      s.popular
                        ? 'bg-gold-500 text-brand-black hover:bg-gold-600 hover:text-white'
                        : 'border-2 border-gold-500 text-gold-600 hover:bg-gold-500 hover:text-brand-black'
                    }`}
                  >
                    Request Quote <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* INCLUDED SERVICES */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">
              All-Inclusive Care
            </p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">
              Every Plan Includes
            </h2>
            <p className="text-lg text-brand-textgrey max-w-2xl mx-auto">
              No matter which service you choose, these essentials are always part of the package.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {includedServices.map((s, i) => (
              <div
                key={s.label}
                className="flex flex-col items-center text-center p-6 bg-brand-cream rounded-2xl hover:bg-gold-50 transition-colors duration-300 animate-slide-up"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div className="w-12 h-12 rounded-full bg-gold-100 flex items-center justify-center mb-4">
                  <s.icon className="h-6 w-6 text-gold-600" />
                </div>
                <p className="text-sm font-semibold text-brand-black">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* INSURANCE & PAYMENT */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="bg-brand-black rounded-3xl p-10 md:p-16 text-center">
            <h2 className="font-serif text-3xl md:text-4xl text-white mb-4">
              Insurance & Payment Options
            </h2>
            <p className="text-brand-cream/80 max-w-2xl mx-auto mb-10 leading-relaxed">
              We work with most major insurance providers and offer flexible payment plans
              for families. Our team will help you navigate coverage options and find the
              most affordable path to quality care.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {[
                'Direct Insurance Billing',
                'Monthly Payment Plans',
                'Diaspora Wire Transfer Options',
              ].map((item) => (
                <div key={item} className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-gold-500/20">
                  <Check className="h-8 w-8 text-gold-400 mx-auto mb-3" />
                  <p className="text-white font-medium">{item}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <CTASection />
    </div>
  );
}
