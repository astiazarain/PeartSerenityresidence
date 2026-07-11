import { Link } from 'react-router-dom';
import {
  BedDouble,
  Utensils,
  Trees,
  Activity,
  Tv,
  ShowerHead,
  Accessibility,
  Heart,
  Wifi,
  Car,
  ShieldCheck,
  Sun,
  ArrowRight,
} from 'lucide-react';
import CTASection from '../components/CTASection';

export default function Facility() {
  const amenities = [
    { icon: BedDouble, label: 'Private & Semi-Private Rooms', desc: 'Comfortable, climate-controlled accommodations' },
    { icon: Utensils, label: 'Dining Room', desc: 'Caribbean cuisine with dietary accommodations' },
    { icon: Trees, label: 'Garden Courtyard', desc: 'Safe outdoor space for relaxation and activities' },
    { icon: Activity, label: 'Therapy Room', desc: 'Physical and occupational therapy on-site' },
    { icon: Tv, label: 'Common Lounge', desc: 'TV, games, music, and social gathering space' },
    { icon: ShowerHead, label: 'Accessible Bathrooms', desc: 'Walk-in showers with safety rails and support' },
    { icon: Accessibility, label: 'Full Accessibility', desc: 'Ramps, wide corridors, and mobility-friendly design' },
    { icon: Wifi, label: 'Family Video Room', desc: 'Dedicated space for virtual family visits' },
    { icon: Car, label: 'Transportation Service', desc: 'Medical appointments and outings' },
    { icon: ShieldCheck, label: 'Nursing Station', desc: '24/7 staffed nursing station with monitoring' },
    { icon: Sun, label: 'Sun Terrace', desc: 'Outdoor seating with views of the garden' },
    { icon: Heart, label: 'Chapel & Quiet Room', desc: 'Space for prayer, meditation, and reflection' },
  ];

  const galleryImages = [
    { url: 'https://images.pexels.com/photos/7551672/pexels-photo-7551672.jpeg?auto=compress&cs=tinysrgb&w=800&q=80', alt: 'Comfortable room', label: 'Private Suite' },
    { url: 'https://images.pexels.com/photos/7551570/pexels-photo-7551570.jpeg?auto=compress&cs=tinysrgb&w=800&q=80', alt: 'Dining area', label: 'Dining Room' },
    { url: 'https://images.pexels.com/photos/7551759/pexels-photo-7551759.jpeg?auto=compress&cs=tinysrgb&w=800&q=80', alt: 'Lounge area', label: 'Common Lounge' },
    { url: 'https://images.pexels.com/photos/7551617/pexels-photo-7551617.jpeg?auto=compress&cs=tinysrgb&w=800&q=80', alt: 'Garden', label: 'Garden Courtyard' },
    { url: 'https://images.pexels.com/photos/7551596/pexels-photo-7551596.jpeg?auto=compress&cs=tinysrgb&w=800&q=80', alt: 'Therapy room', label: 'Therapy Room' },
    { url: 'https://images.pexels.com/photos/7551673/pexels-photo-7551673.jpeg?auto=compress&cs=tinysrgb&w=800&q=80', alt: 'Nursing care', label: 'Nursing Station' },
  ];

  const safetyFeatures = [
    '24/7 security monitoring',
    'Emergency call systems in every room',
    'Fire safety systems and regular drills',
    'Non-slip flooring throughout',
    'Grab bars in all bathrooms',
    'Secured entrances and exits',
    'Regular safety inspections',
    'Staff trained in emergency response',
  ];

  return (
    <div>
      {/* HEADER */}
      <section className="relative pt-40 pb-20 bg-brand-black overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-gold-500 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
        </div>
        <div className="container-max px-6 md:px-12 lg:px-20 relative z-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-400 mb-4">Our Facility</p>
          <h1 className="font-serif text-5xl md:text-6xl text-white mb-6">A Home, Not a Hospital</h1>
          <p className="text-lg text-brand-cream/80 max-w-2xl mx-auto leading-relaxed">
            Every detail of our Montego Bay residence has been designed to feel like home — warm, welcoming, and dignified — while meeting the highest clinical standards.
          </p>
        </div>
      </section>

      {/* GALLERY */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">Take a Look Around</p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">Our Spaces</h2>
            <p className="text-lg text-brand-textgrey max-w-2xl mx-auto">Bright, comfortable, and designed for both living and healing.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {galleryImages.map((img, i) => (
              <div key={i} className="group relative rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-500 animate-slide-up" style={{ animationDelay: `${i * 80}ms` }}>
                <img src={img.url} alt={img.alt} className="w-full h-72 object-cover group-hover:scale-105 transition-transform duration-700" />
                <div className="absolute inset-0 bg-gradient-to-t from-brand-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 flex items-end p-6">
                  <p className="text-white font-serif text-xl">{img.label}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AMENITIES */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">Amenities & Features</p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">Everything They Need</h2>
            <p className="text-lg text-brand-textgrey max-w-2xl mx-auto">Thoughtful amenities that make daily life comfortable, engaging, and dignified.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {amenities.map((a, i) => (
              <div key={a.label} className="flex gap-4 p-6 bg-brand-cream rounded-2xl hover:bg-gold-50 transition-colors duration-300 animate-slide-up" style={{ animationDelay: `${i * 60}ms` }}>
                <div className="w-12 h-12 rounded-xl bg-gold-100 flex items-center justify-center flex-shrink-0">
                  <a.icon className="h-6 w-6 text-gold-600" />
                </div>
                <div>
                  <h3 className="font-serif text-lg text-brand-black mb-1">{a.label}</h3>
                  <p className="text-sm text-brand-textgrey">{a.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SAFETY */}
      <section className="section-padding bg-brand-cream">
        <div className="container-max">
          <div className="bg-brand-black rounded-3xl p-10 md:p-16">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <div>
                <div className="w-14 h-14 rounded-2xl bg-gold-500/20 flex items-center justify-center mb-6">
                  <ShieldCheck className="h-7 w-7 text-gold-400" />
                </div>
                <h2 className="font-serif text-3xl md:text-4xl text-white mb-4">Safety Is Non-Negotiable</h2>
                <p className="text-brand-cream/80 leading-relaxed mb-6">
                  Our facility meets and exceeds Jamaican healthcare facility standards. Every safety measure is in place to ensure your loved one is protected at all times — because peace of mind is part of our care.
                </p>
                <Link to="/contact" className="inline-flex items-center gap-2 text-gold-400 font-semibold hover:gap-3 transition-all">
                  Schedule a Safety Tour <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {safetyFeatures.map((f) => (
                  <div key={f} className="flex items-start gap-2 text-brand-cream/90 text-sm">
                    <span className="w-2 h-2 rounded-full bg-gold-400 flex-shrink-0 mt-1.5" />
                    <span>{f}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* LOCATION */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="text-center mb-12">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">Find Us</p>
            <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">Montego Bay, Jamaica</h2>
            <p className="text-lg text-brand-textgrey max-w-2xl mx-auto">
              Conveniently located in Montego Bay, St. James Parish — close to medical facilities and the international airport for diaspora families visiting.
            </p>
          </div>
          <div className="rounded-3xl overflow-hidden shadow-2xl h-[400px]">
            <iframe
              title="Peart Serenity Location"
              src="https://www.openstreetmap.org/export/embed.html?bbox=-77.95%2C18.45%2C-77.85%2C18.52&layer=mapnik&marker=18.4762%2C-77.8936"
              className="w-full h-full border-0"
              loading="lazy"
            />
          </div>
        </div>
      </section>

      <CTASection />
    </div>
  );
}
