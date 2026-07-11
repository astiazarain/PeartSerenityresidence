import { Link } from 'react-router-dom';
import {
  Heart,
  Shield,
  Activity,
  Users,
  Sun,
  Stethoscope,
  Home as HomeIcon,
  Clock,
  ArrowRight,
  CheckCircle2,
  Plane,
  Sparkles,
} from 'lucide-react';
import TestimonialSection from '../components/TestimonialSection';
import CTASection from '../components/CTASection';
import HeroCarousel from '../components/HeroCarousel';

export default function Home() {
  const services = [
    { icon: Sun, title: 'Adult Day Care', desc: 'Engaging daytime care with activities, meals, and social connection.', price: 'From $45/day' },
    { icon: Clock, title: 'Respite Care', desc: 'Short-term relief for family caregivers — from a few days to weeks.', price: 'From $95/night' },
    { icon: HomeIcon, title: 'Long-Term Residential', desc: '24/7 compassionate care in a warm, home-like environment.', price: 'From $2,800/mo' },
    { icon: Sparkles, title: 'Private Suites', desc: 'Premium private suites with personalized care plans.', price: 'From $4,200/mo' },
    { icon: Activity, title: 'Post-Surgical Recovery', desc: 'Clinical-grade nursing care for recovery after surgery.', price: 'From $120/day' },
    { icon: Stethoscope, title: 'Specialized Care', desc: 'Diabetes, dementia, mobility, and chronic condition management.', price: 'Custom' },
  ];

  const features = [
    { icon: Shield, title: 'Clinical-Grade Supervision', desc: '24/7 nursing oversight with personalized care plans reviewed by licensed physicians.' },
    { icon: Heart, title: 'Caribbean Warmth', desc: 'Genuine Jamaican hospitality — every resident is treated as family, not a patient.' },
    { icon: Plane, title: 'Diaspora Peace of Mind', desc: 'Weekly video updates, digital reports, and transparent communication for overseas families.' },
    { icon: Users, title: 'Family Integration', desc: 'Open visiting hours, family events, and a community that welcomes loved ones.' },
  ];

  const stats = [
    { value: '24/7', label: 'Nursing Care' },
    { value: '1:5', label: 'Staff-to-Resident Ratio' },
    { value: '15+', label: 'Years of Experience' },
    { value: '100%', label: 'Family Satisfaction' },
  ];

  return (
    <div>
      {/* HERO CAROUSEL */}
      <HeroCarousel />

      {/* INTRO */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-4">
                Our Promise
              </p>
              <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-6 leading-tight">
                A New Standard of Eldercare in Jamaica
              </h2>
              <p className="text-lg text-brand-textgrey leading-relaxed mb-6">
                Peart Serenity Residence was founded on a simple belief: that our elders
                deserve care that is as compassionate as it is clinical. In the warmth of
                Montego Bay, we have created a home where dignity, joy, and professional
                excellence meet.
              </p>
              <p className="text-lg text-brand-textgrey leading-relaxed mb-8">
                For Jamaican families and the diaspora alike, we offer something rare —
                the peace of mind that comes from knowing your loved one is safe, engaged,
                and truly cared for.
              </p>
              <Link to="/about" className="btn-outline">
                Our Story <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="relative">
              <img
                src="https://images.pexels.com/photos/7551672/pexels-photo-7551672.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80"
                alt="Caring for elderly"
                className="rounded-3xl shadow-2xl w-full h-[500px] object-cover"
              />
              <div className="absolute -bottom-6 -left-6 bg-gold-500 text-brand-black rounded-2xl p-6 shadow-xl hidden md:block">
                <p className="font-serif text-3xl font-bold">100%</p>
                <p className="text-sm text-brand-black/70">Family Satisfaction</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">
              Why Peart Serenity
            </p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">
              Care That Goes Beyond
            </h2>
            <p className="text-lg text-brand-textgrey max-w-2xl mx-auto">
              We combine clinical excellence with genuine Caribbean warmth to create
              an environment where residents thrive.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((f, i) => (
              <div
                key={f.title}
                className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 animate-slide-up"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="w-14 h-14 rounded-2xl bg-gold-50 flex items-center justify-center mb-6">
                  <f.icon className="h-7 w-7 text-gold-600" />
                </div>
                <h3 className="font-serif text-2xl text-brand-black mb-3">{f.title}</h3>
                <p className="text-brand-textgrey leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SERVICES PREVIEW */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">
              Our Services
            </p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">
              Care for Every Need
            </h2>
            <p className="text-lg text-brand-textgrey max-w-2xl mx-auto">
              From daytime engagement to full-time residential care, we have a plan
              that fits your family's needs and budget.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {services.map((s, i) => (
              <div
                key={s.title}
                className="group bg-brand-cream rounded-2xl p-8 hover:bg-white hover:shadow-2xl transition-all duration-500 border border-brand-softgrey hover:border-gold-200 animate-slide-up"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className="w-14 h-14 rounded-2xl bg-gold-500 flex items-center justify-center mb-6 group-hover:bg-gold-600 transition-colors">
                  <s.icon className="h-7 w-7 text-brand-black" />
                </div>
                <h3 className="font-serif text-2xl text-brand-black mb-2">{s.title}</h3>
                <p className="text-sm text-gold-600 font-semibold mb-3">{s.price}</p>
                <p className="text-brand-textgrey leading-relaxed mb-4">{s.desc}</p>
                <Link
                  to="/services"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-gold-600 hover:gap-3 transition-all"
                >
                  Learn More <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* DIASPORA SECTION */}
      <section className="section-padding bg-brand-black relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-10 right-10 w-72 h-72 bg-gold-400 rounded-full blur-3xl"></div>
        </div>
        <div className="container-max relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="order-2 lg:order-1">
              <img
                src="https://images.pexels.com/photos/7551762/pexels-photo-7551762.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80"
                alt="Family connection"
                className="rounded-3xl shadow-2xl w-full h-[450px] object-cover"
              />
            </div>
            <div className="order-1 lg:order-2">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-400 mb-4">
                For the Jamaican Diaspora
              </p>
              <h2 className="font-serif text-4xl md:text-5xl text-white mb-6 leading-tight">
                Caring from Afar,
                <br />
                <span className="italic text-gold-300">Connected Always</span>
              </h2>
              <p className="text-lg text-brand-cream/80 leading-relaxed mb-8">
                We understand the unique challenge of ensuring quality care for your
                loved ones while living abroad. That is why we have built a system
                that keeps you informed and connected — no matter where in the world
                you are.
              </p>
              <ul className="space-y-4">
                {[
                  'Weekly video updates of your loved one',
                  'Digital care reports accessible 24/7',
                  'Direct communication with care staff',
                  'Virtual family meetings and consultations',
                  'Transparent billing and care documentation',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3 text-brand-cream/90">
                    <CheckCircle2 className="h-5 w-5 text-gold-400 flex-shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      <TestimonialSection />
      <CTASection />
    </div>
  );
}
