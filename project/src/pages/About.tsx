import {
  Heart,
  Shield,
  Users,
  Target,
  Eye,
  Sparkles,
  CheckCircle2,
  Globe,
  MapPin,
  Award,
  Stethoscope,
  Quote,
  HandHeart,
} from 'lucide-react';
import CTASection from '../components/CTASection';

export default function About() {
  const founderFacts = [
    { icon: MapPin, label: 'Born in Cuba, rooted in Jamaica' },
    { icon: Stethoscope, label: '50+ years as a nurse' },
    { icon: Award, label: 'Registered Nurse, Cornwall Regional Hospital' },
    { icon: Heart, label: '68 years young, still at the bedside' },
  ];

  const journey = [
    {
      icon: MapPin,
      title: 'Born in Cuba',
      desc: 'Yolanda Peart Rodríguez is born in Cuba to a family carrying deep Jamaican roots — her grandparents had emigrated from Jamaica generations before.',
    },
    {
      icon: Stethoscope,
      title: 'A Nursing Mission to Jamaica',
      desc: 'Trained as a nurse in Cuba, she is sent to serve on a medical mission in Jamaica — and finds herself on the island her grandparents once called home.',
    },
    {
      icon: Award,
      title: 'Becoming Jamaican',
      desc: 'What began as a mission becomes a life. Yolanda chooses to stay, builds her family on the island, and becomes a Jamaican citizen.',
    },
    {
      icon: Heart,
      title: 'Still at the Bedside',
      desc: 'Today, at 68, she continues to practice as a Registered Nurse at Cornwall Regional Hospital in Montego Bay — over 50 years of nursing and counting.',
    },
    {
      icon: HandHeart,
      title: 'A Family Enterprise Is Born',
      desc: "Seeing how few dignified options existed for Jamaica's elders, she founds Peart Serenity Residence. Her cousin and her daughter-in-law are among the family members who join her in building it from the ground up.",
    },
  ];

  const stats = [
    { value: '17%', label: 'of Jamaicans are now aged 60 and over' },
    { value: '~400,000', label: 'seniors nationwide need trustworthy care' },
    { value: 'Mid-70s', label: 'average life expectancy today, and rising' },
  ];

  const values = [
    { icon: Heart, title: 'Compassion', desc: 'Every interaction is led by empathy and genuine care.' },
    { icon: Sparkles, title: 'Dignity', desc: 'Residents are treated as valued individuals, never as patients to be processed.' },
    { icon: Award, title: 'Professionalism', desc: 'Trained staff, clinical standards, and accountable processes.' },
    { icon: Shield, title: 'Safety', desc: 'Secure environments, emergency readiness, and rigorous protocols.' },
    { icon: HandHeart, title: 'Respect', desc: 'Cultural, religious, and personal preferences are honored.' },
    { icon: Users, title: 'Human Connection', desc: 'Family communication and social engagement are central, not optional.' },
  ];

  const whoWeServe = [
    { icon: Users, title: 'Jamaican Families', desc: 'Seeking quality, trustworthy care for elderly relatives close to home.' },
    { icon: Globe, title: 'Overseas Jamaicans', desc: 'The diaspora financing and coordinating care for parents back home.' },
    { icon: MapPin, title: 'Expatriates & Retirees', desc: 'Foreign residents living in, or relocating to, Jamaica.' },
  ];

  const team = [
    {
      name: 'Yolanda Peart Rodríguez',
      role: 'Founder, Administrator & Clinical Lead',
      bio: 'A Registered Nurse with 50+ years of experience, Yolanda oversees daily operations and sets the clinical standard for every resident\'s care.',
      founder: true,
    },
    { name: 'Registered Nurse', role: 'Clinical Supervision & Care Planning', bio: 'Leads day-to-day clinical care, medication management, and individualized care plans.' },
    { name: 'Nursing Assistants', role: 'Hands-On Personal Care', bio: 'A rotating team providing round-the-clock personal care, companionship, and support.' },
    { name: 'Visiting Physician', role: 'Medical Oversight (Retainer)', bio: "Provides regular medical review, coordinating with our nursing team on every resident's health." },
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
          <h1 className="font-serif text-5xl md:text-6xl text-white mb-6">Where Care Feels Like Home</h1>
          <p className="text-lg text-brand-cream/80 max-w-2xl mx-auto leading-relaxed">
            Peart Serenity Residence began with one nurse's promise: that growing old in Jamaica could mean comfort, dignity, and family — not isolation. It is a social enterprise founded by Yolanda Peart Rodríguez, built for the nearly 400,000 Jamaicans aged 60 and over who deserve better care.
          </p>
        </div>
      </section>

      {/* FOUNDER SPOTLIGHT */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="relative">
              <div className="rounded-3xl shadow-2xl w-full h-[550px] bg-gradient-to-br from-brand-black to-[#2a2a2a] flex flex-col items-center justify-center text-center p-10 relative overflow-hidden">
                <div className="absolute -top-10 -right-10 w-56 h-56 bg-gold-400/10 rounded-full blur-3xl"></div>
                <div className="absolute bottom-0 left-0 w-72 h-72 bg-gold-500/5 rounded-full blur-3xl"></div>
                <div className="w-32 h-32 rounded-full bg-gold-500/10 border-2 border-gold-400/40 flex items-center justify-center mb-6 relative z-10">
                  <span className="font-serif text-4xl text-gold-400">YPR</span>
                </div>
                <p className="text-gold-400 text-sm uppercase tracking-[0.3em] mb-2 relative z-10">Founder Portrait</p>
                <p className="text-brand-cream/50 text-sm max-w-xs relative z-10">Photo coming soon</p>
              </div>
              <div className="absolute -bottom-8 -left-8 bg-white rounded-2xl shadow-xl p-6 hidden md:block max-w-[220px]">
                <p className="font-serif text-3xl text-brand-black mb-1">50+</p>
                <p className="text-sm text-brand-textgrey leading-snug">years of nursing experience, and still counting</p>
              </div>
            </div>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-4">Meet Our Founder</p>
              <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-6 leading-tight">
                Yolanda Peart Rodríguez
              </h2>
              <div className="space-y-4 text-lg text-brand-textgrey leading-relaxed mb-8">
                <p>Yolanda was born in Cuba, the granddaughter of Jamaican migrants who carried their island's memory with them for generations. She trained as a nurse in Cuba and, true to the country's long tradition of medical missions abroad, was sent to serve in Jamaica — the homeland her grandparents had left behind.</p>
                <p>What began as a mission became a life. Yolanda stayed, built her family on the island, and became a Jamaican citizen. Today, at 68, she is still practicing — a Registered Nurse at Cornwall Regional Hospital in Montego Bay, with more than five decades of hands-on care behind her.</p>
                <p>It was at the bedside of Jamaica's elderly that she saw the gap up close: a rapidly aging population and too few places where they could grow old with both medical care and dignity. Peart Serenity Residence is her answer — and what started as her personal mission has become a family calling, with her cousin and her daughter-in-law among the relatives who joined her to build it from the ground up.</p>
              </div>
              <div className="bg-brand-cream rounded-2xl p-8 mb-8 relative">
                <Quote className="h-8 w-8 text-gold-400 mb-3" />
                <p className="font-serif text-xl text-brand-black leading-relaxed italic mb-3">
                  "I have spent my whole life caring for people who weren't my own family. I wanted to build a place where every elder is treated like family — because so many of ours are."
                </p>
                <p className="text-sm font-semibold text-gold-600">— Yolanda Peart Rodríguez, Founder</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {founderFacts.map((fact) => (
                  <div key={fact.label} className="flex items-start gap-3">
                    <fact.icon className="h-5 w-5 text-gold-600 flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-brand-textgrey leading-relaxed">{fact.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* HER JOURNEY */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">From Cuba to Montego Bay</p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">Her Journey</h2>
          </div>
          <div className="max-w-4xl mx-auto">
            {journey.map((step, i) => (
              <div key={step.title} className={`flex gap-8 pb-12 ${i !== journey.length - 1 ? 'border-b border-brand-softgrey' : ''}`}>
                <div className="flex-shrink-0">
                  <div className="w-20 h-20 rounded-full bg-gold-500 text-brand-black flex items-center justify-center">
                    <step.icon className="h-8 w-8" />
                  </div>
                </div>
                <div className="pt-4">
                  <h3 className="font-serif text-2xl text-brand-black mb-2">{step.title}</h3>
                  <p className="text-brand-textgrey leading-relaxed">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WHY NOW / STATS */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">Why Now</p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">Jamaica Is Aging — and Deserves Better Care</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {stats.map((s) => (
              <div key={s.label} className="text-center bg-brand-cream rounded-3xl p-10">
                <p className="font-serif text-5xl text-gold-600 mb-3">{s.value}</p>
                <p className="text-brand-textgrey leading-relaxed">{s.label}</p>
              </div>
            ))}
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
                To provide compassionate, safe, and professional care that improves the physical, emotional, and social wellbeing of every elderly resident in our home.
              </p>
            </div>
            <div className="bg-white rounded-3xl p-10 shadow-lg">
              <div className="w-14 h-14 rounded-2xl bg-gold-50 flex items-center justify-center mb-6">
                <Eye className="h-7 w-7 text-gold-600" />
              </div>
              <h3 className="font-serif text-3xl text-brand-black mb-4">Our Vision</h3>
              <p className="text-lg text-brand-textgrey leading-relaxed">
                To become Jamaica's most trusted and respected senior wellness and assisted-living brand — a benchmark for dignity, professionalism, and Caribbean warmth.
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
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

      {/* WHO WE SERVE */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">Who We Serve</p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">Three Families, One Promise</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {whoWeServe.map((w) => (
              <div key={w.title} className="bg-white rounded-3xl p-10 text-center shadow-lg">
                <div className="w-14 h-14 rounded-2xl bg-gold-50 flex items-center justify-center mx-auto mb-6">
                  <w.icon className="h-7 w-7 text-gold-600" />
                </div>
                <h3 className="font-serif text-2xl text-brand-black mb-3">{w.title}</h3>
                <p className="text-brand-textgrey leading-relaxed">{w.desc}</p>
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
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">The Team We're Building</h2>
            <p className="text-lg text-brand-textgrey max-w-2xl mx-auto">
              A lean, hands-on team led by our founder, growing alongside the residence.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {team.map((member, i) => (
              <div
                key={member.name}
                className={`rounded-2xl p-8 text-center hover:shadow-xl transition-all duration-500 animate-slide-up ${
                  member.founder ? 'bg-brand-black' : 'bg-brand-cream'
                }`}
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className={`w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 ${
                  member.founder ? 'bg-gold-500/15 border border-gold-400/40' : 'bg-gold-100'
                }`}>
                  {member.founder ? (
                    <Heart className="h-12 w-12 text-gold-400" />
                  ) : (
                    <Users className="h-12 w-12 text-gold-600" />
                  )}
                </div>
                {member.founder && (
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gold-400 mb-2">Founder</p>
                )}
                <h3 className={`font-serif text-xl mb-1 ${member.founder ? 'text-white' : 'text-brand-black'}`}>{member.name}</h3>
                <p className="text-sm font-semibold text-gold-600 mb-3">{member.role}</p>
                <p className={`text-sm leading-relaxed ${member.founder ? 'text-brand-cream/70' : 'text-brand-textgrey'}`}>{member.bio}</p>
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
