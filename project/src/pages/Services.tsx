import { Link } from 'react-router-dom';
import {
  Check,
  ArrowRight,
  Heart,
  Utensils,
  Dumbbell,
  Brain,
  Pill,
  ShowerHead,
  Users,
  Stethoscope,
} from 'lucide-react';
import CTASection from '../components/CTASection';
import { useServices } from '../hooks/useServices';
import { getServiceIcon, formatServicePrice } from '../lib/serviceIcons';

export default function Services() {
  const { services, loading } = useServices();

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
          {loading ? (
            <p className="text-center text-brand-textgrey">Loading services...</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {services.map((s, i) => {
                const Icon = getServiceIcon(s.name);
                const { price, period } = formatServicePrice(s);
                return (
                  <div
                    key={s.id}
                    className={`relative bg-white rounded-3xl shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 animate-slide-up flex flex-col ${
                      s.is_popular ? 'ring-2 ring-gold-500 lg:scale-105' : ''
                    }`}
                    style={{ animationDelay: `${i * 80}ms` }}
                  >
                    {s.is_popular && (
                      <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gold-500 text-brand-black text-xs font-semibold uppercase tracking-wider px-6 py-2 rounded-full shadow-lg">
                        Most Popular
                      </div>
                    )}
                    <div className="p-8 flex-1">
                      <div className="w-14 h-14 rounded-2xl bg-gold-50 flex items-center justify-center mb-6">
                        <Icon className="h-7 w-7 text-gold-600" />
                      </div>
                      <h3 className="font-serif text-2xl text-brand-black mb-2">{s.name}</h3>
                      <p className="text-brand-textgrey leading-relaxed mb-6 text-sm">{s.description_sale}</p>
                      <div className="flex items-baseline gap-1 mb-6 pb-6 border-b border-brand-softgrey">
                        <span className="font-serif text-4xl font-bold text-gold-600">{price}</span>
                        <span className="text-brand-textgrey">{period}</span>
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
                          s.is_popular
                            ? 'bg-gold-500 text-brand-black hover:bg-gold-600 hover:text-white'
                            : 'border-2 border-gold-500 text-gold-600 hover:bg-gold-500 hover:text-brand-black'
                        }`}
                      >
                        Request Quote <ArrowRight className="h-4 w-4" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
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
