import { useCallback, useEffect, useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, Quote, Star } from 'lucide-react';
import { fetchTestimonials, type Testimonial } from '../lib/odoo';

const CARDS_PER_PAGE = 3;

function initials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('');
}

function TestimonialCard({ t }: { t: Testimonial }) {
  return (
    <div className="bg-white rounded-2xl p-8 shadow-lg h-full flex flex-col">
      <Quote className="h-10 w-10 text-gold-200 mb-4" fill="currentColor" />
      <p className="text-brand-textgrey leading-relaxed mb-6 italic flex-1">"{t.content}"</p>
      <div className="flex items-center gap-1 mb-4">
        {Array.from({ length: t.rating }).map((_, idx) => (
          <Star key={idx} className="h-4 w-4 text-gold-500" fill="currentColor" />
        ))}
      </div>
      <div className="flex items-center gap-4 border-t border-brand-softgrey pt-4">
        {t.photo ? (
          <img
            src={`data:image/png;base64,${t.photo}`}
            alt={t.author_name}
            className="h-12 w-12 rounded-full object-cover flex-shrink-0"
          />
        ) : (
          <div className="h-12 w-12 rounded-full bg-gold-100 text-gold-700 flex items-center justify-center font-serif text-base font-bold flex-shrink-0">
            {initials(t.author_name)}
          </div>
        )}
        <div>
          <p className="font-serif text-lg font-bold text-brand-black">{t.author_name}</p>
          <p className="text-sm text-brand-textgrey">
            {t.relation}
            {t.location ? ` · ${t.location}` : ''}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function TestimonialSection() {
  const [testimonials, setTestimonials] = useState<Testimonial[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);

  useEffect(() => {
    fetchTestimonials(9)
      .then(setTestimonials)
      .catch(() => setTestimonials([]))
      .finally(() => setLoading(false));
  }, []);

  const pages = useMemo(() => {
    const chunks: Testimonial[][] = [];
    for (let i = 0; i < testimonials.length; i += CARDS_PER_PAGE) {
      chunks.push(testimonials.slice(i, i + CARDS_PER_PAGE));
    }
    return chunks;
  }, [testimonials]);

  const goTo = useCallback((idx: number) => setPage((idx + pages.length) % pages.length), [pages.length]);
  const next = useCallback(() => goTo(page + 1), [page, goTo]);
  const prev = useCallback(() => goTo(page - 1), [page, goTo]);

  useEffect(() => {
    if (pages.length < 2) return;
    const id = setInterval(next, 7000);
    return () => clearInterval(id);
  }, [next, pages.length]);

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
    <section className="section-padding bg-brand-cream overflow-hidden">
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

        <div className="relative">
          <div
            key={page}
            className="grid grid-cols-1 md:grid-cols-3 gap-8 animate-fade-in"
          >
            {pages[page].map((t) => (
              <TestimonialCard key={t.id} t={t} />
            ))}
          </div>

          {pages.length > 1 && (
            <>
              <button
                onClick={prev}
                className="hidden lg:flex absolute -left-6 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white shadow-lg items-center justify-center text-brand-black hover:bg-gold-500 transition-all duration-300"
                aria-label="Previous testimonials"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button
                onClick={next}
                className="hidden lg:flex absolute -right-6 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white shadow-lg items-center justify-center text-brand-black hover:bg-gold-500 transition-all duration-300"
                aria-label="Next testimonials"
              >
                <ChevronRight className="h-5 w-5" />
              </button>

              <div className="flex items-center justify-center gap-3 mt-10">
                {pages.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => goTo(i)}
                    className={`transition-all duration-300 rounded-full ${
                      i === page ? 'w-8 h-2.5 bg-gold-500' : 'w-2.5 h-2.5 bg-brand-softgrey hover:bg-gold-300'
                    }`}
                    aria-label={`Go to testimonials page ${i + 1}`}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
