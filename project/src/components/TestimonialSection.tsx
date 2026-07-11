import { useEffect, useState } from 'react';
import { Star, Quote } from 'lucide-react';
import { supabase, type Testimonial } from '../lib/supabase';

export default function TestimonialSection() {
  const [testimonials, setTestimonials] = useState<Testimonial[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTestimonials = async () => {
      const { data } = await supabase
        .from('testimonials')
        .select('*')
        .eq('approved', true)
        .order('created_at', { ascending: false })
        .limit(6);

      if (data) setTestimonials(data);
      setLoading(false);
    };
    fetchTestimonials();
  }, []);

  if (loading) {
    return (
      <section className="section-padding bg-brand-cream">
        <div className="container-max text-center">
          <p className="text-brand-textgrey">Loading testimonials...</p>
        </div>
      </section>
    );
  }

  if (testimonials.length === 0) return null;

  return (
    <section className="section-padding bg-brand-cream">
      <div className="container-max">
        <div className="text-center mb-16">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-3">
            Family Voices
          </p>
          <h2 className="font-serif text-4xl md:text-5xl text-brand-black mb-4">
            Stories of Peace and Trust
          </h2>
          <p className="text-lg text-brand-textgrey max-w-2xl mx-auto">
            Hear from families who have entrusted their loved ones to our care —
            from Jamaica and across the diaspora.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((t, i) => (
            <div
              key={t.id}
              className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-500 animate-slide-up"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <Quote className="h-10 w-10 text-gold-200 mb-4" fill="currentColor" />
              <p className="text-brand-textgrey leading-relaxed mb-6 italic">"{t.content}"</p>
              <div className="flex items-center gap-1 mb-4">
                {Array.from({ length: t.rating }).map((_, idx) => (
                  <Star key={idx} className="h-4 w-4 text-gold-500" fill="currentColor" />
                ))}
              </div>
              <div className="border-t border-brand-softgrey pt-4">
                <p className="font-serif text-lg font-bold text-brand-black">{t.author_name}</p>
                <p className="text-sm text-brand-textgrey">
                  {t.relation}
                  {t.location ? ` · ${t.location}` : ''}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
