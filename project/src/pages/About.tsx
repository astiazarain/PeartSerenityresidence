import {
  Heart,
  Shield,
  Users,
  Target,
  Eye,
  Sparkles,
  CheckCircle2,
  Globe,
} from 'lucide-react';
import CTASection from '../components/CTASection';

export default function About() {
  const values = [
    { icon: Heart, title: 'Compassion First', desc: 'Every interaction is guided by genuine empathy. We see the person, not just the care need.' },
    { icon: Shield, title: 'Clinical Excellence', desc: 'Licensed nursing staff, physician oversight, and evidence-based care protocols.' },
    { icon: Users, title: 'Family Partnership', desc: 'Families are partners in care. We communicate openly, honestly, and frequently.' },
    { icon: Sparkles, title: 'Dignity Always', desc: "We preserve independence, respect choices, and honor each resident's life story." },
  ];

  const milestones = [
    { year: '2024', title: 'The Vision', desc: 'Founded by healthcare professionals who saw the gap between hospital care and home care in Jamaica.' },
    { year: '2025', title: 'Opening Doors', desc: 'Peart Serenity Residence opens in Montego Bay with capacity for 20 residents and a full nursing team.' },
    { year: '2025+', title: 'Diaspora Connection', desc: 'Launch of digital family portal connecting overseas families with their loved ones in real-time.' },
    { year: '2026', title: 'Growing Together', desc: 'Expanding services to include specialized memory care and post-surgical recovery programs.' },
  ];

  const team = [
    { name: 'Neville Peart', role: 'Founder & Director', bio: 'Healthcare administrator with 15+ years in eldercare management across Jamaica and the UK.' },
    { name: 'Dr. Andrea Campbell', role: 'Medical Director', bio: 'Board-certified physician specializing in geriatric medicine and chronic care management.' },
    { name: 'Sister Marcia Williams', role: 'Head of Nursing', bio: 'Registered nurse with 20+ years experience in eldercare and post-surgical recovery.' },
    { name: 'Patricia Brown', role: 'Family Liaison Director', bio: 'Dedicated to keeping diaspora families connected and informed about their loved ones.' },
  ];

  return (
    <div>
      {/* HEADER */}
      <section className="relative pt-40 pb-20 bg-brand-black overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-gold-500 rounded-full blur-3xl -translate-x-1/2 translate-y-1/2"></div>
        </div>
        <div className="container-max px-6 md:px-12 lg:px-20 relative z-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-400 mb-4">Our Story</p>
          <h1 className="font-serif text-5xl md:text-6xl text-white mb-6">Built on Love, Driven by Purpose</h1>
          <p className="text-lg text-brand-cream/80 max-w-2xl mx-auto leading-relaxed">
            Peart Serenity Residence was born from a simple observation: Jamaican families deserve better eldercare options — and diaspora families deserve peace of mind.
          </p>
        </div>
      </section>

      {/* STORY */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-4">How We Began</p>
              <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-6 leading-tight">
                A Personal Mission Became a Residence
              </h2>
              <div className="space-y-4 text-lg text-brand-textgrey leading-relaxed">
                <p>When our founder Neville Peart searched for quality eldercare for his own mother in Montego Bay, he found a gap: facilities were either too clinical and cold, or warm but lacking professional nursing oversight.</p>
                <p>Having worked in UK healthcare for over a decade, he knew it was possible to have both — clinical excellence AND genuine warmth. He returned to Jamaica with a vision: to build the care home he wished he could have found for his own mother.</p>
                <p>Today, Peart Serenity Residence stands as that vision realized — a place where Jamaican families and the diaspora can trust that their loved ones receive the very best care, surrounded by the warmth of Caribbean hospitality.</p>
              </div>
            </div>
            <div className="relative">
              <img src="https://images.pexels.com/photos/7551584/pexels-photo-7551584.jpeg?auto=compress&cs=tinysrgb&w=1200&q=80" alt="Eldercare in Jamaica" className="rounded-3xl shadow-2xl w-full h-[550px] object-cover" />
            </div>
          </div>
        </div>
      </section>

      {/* MISSION & VISION */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white rounded-3xl p-10 shadow-lg">
              <div className="w-14 h-14 rounded-2xl bg-gold-50 flex items-center justify-center mb-6">
                <Target className="h-7 w-7 text-gold-600" />
              </div>
              <h3 className="font-serif text-3xl text-brand-black mb-4">Our Mission</h3>
              <p className="text-lg text-brand-textgrey leading-relaxed">
                To provide exceptional eldercare that honors the dignity of every resident while offering families — near and far — complete peace of mind through transparent, compassionate, and clinically excellent service.
              </p>
            </div>
            <div className="bg-white rounded-3xl p-10 shadow-lg">
              <div className="w-14 h-14 rounded-2xl bg-gold-50 flex items-center justify-center mb-6">
                <Eye className="h-7 w-7 text-gold-600" />
              </div>
              <h3 className="font-serif text-3xl text-brand-black mb-4">Our Vision</h3>
              <p className="text-lg text-brand-textgrey leading-relaxed">
                To become the Caribbean's most trusted eldercare residence — setting the standard for how seniors are cared for in Jamaica and becoming the first choice for diaspora families seeking quality care for their loved ones.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* VALUES */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">What We Stand For</p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">Our Core Values</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {values.map((v, i) => (
              <div key={v.title} className="text-center animate-slide-up" style={{ animationDelay: `${i * 100}ms` }}>
                <div className="w-16 h-16 rounded-full bg-gold-50 flex items-center justify-center mx-auto mb-6">
                  <v.icon className="h-8 w-8 text-gold-600" />
                </div>
                <h3 className="font-serif text-2xl text-brand-black mb-3">{v.title}</h3>
                <p className="text-brand-textgrey leading-relaxed text-sm">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TIMELINE */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">Our Journey</p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">Milestones</h2>
          </div>
          <div className="max-w-4xl mx-auto">
            {milestones.map((m, i) => (
              <div key={m.year} className={`flex gap-8 pb-12 ${i !== milestones.length - 1 ? 'border-b border-brand-softgrey' : ''}`}>
                <div className="flex-shrink-0">
                  <div className="w-20 h-20 rounded-full bg-gold-500 text-brand-black flex items-center justify-center font-serif text-lg font-bold">
                    {m.year}
                  </div>
                </div>
                <div className="pt-4">
                  <h3 className="font-serif text-2xl text-brand-black mb-2">{m.title}</h3>
                  <p className="text-brand-textgrey leading-relaxed">{m.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TEAM */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">Leadership</p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">Meet Our Care Team</h2>
            <p className="text-lg text-brand-textgrey max-w-2xl mx-auto">
              Experienced professionals who treat every resident as they would their own family.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {team.map((member, i) => (
              <div key={member.name} className="bg-brand-cream rounded-2xl p-8 text-center hover:shadow-xl transition-all duration-500 animate-slide-up" style={{ animationDelay: `${i * 100}ms` }}>
                <div className="w-24 h-24 rounded-full bg-gold-100 flex items-center justify-center mx-auto mb-6">
                  <Users className="h-12 w-12 text-gold-600" />
                </div>
                <h3 className="font-serif text-xl text-brand-black mb-1">{member.name}</h3>
                <p className="text-sm font-semibold text-gold-600 mb-3">{member.role}</p>
                <p className="text-sm text-brand-textgrey leading-relaxed">{member.bio}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* DIASPORA COMMITMENT */}
      <section className="section-padding bg-brand-black relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gold-400 rounded-full blur-3xl"></div>
        </div>
        <div className="container-max relative z-10">
          <div className="max-w-3xl mx-auto text-center">
            <Globe className="h-12 w-12 text-gold-400 mx-auto mb-6" />
            <h2 className="font-serif text-4xl md:text-5xl text-white mb-6">Our Diaspora Commitment</h2>
            <p className="text-lg text-brand-cream/80 leading-relaxed mb-8">
              Over 3 million Jamaicans live abroad. We understand the weight of being far from aging parents and relatives. That is why we have designed every aspect of our service with diaspora families in mind.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left max-w-2xl mx-auto">
              {['Weekly video call updates', 'Digital care reports 24/7 access', 'Direct staff WhatsApp channel', 'Virtual family meetings', 'Transparent monthly billing', 'Emergency contact protocol'].map((item) => (
                <div key={item} className="flex items-start gap-3 text-brand-cream/90">
                  <CheckCircle2 className="h-5 w-5 text-gold-400 flex-shrink-0 mt-0.5" />
                  <span>{item}</span>
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
