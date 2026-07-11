import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ChevronLeft, ChevronRight } from 'lucide-react';

const slides = [
  {
    image: 'https://images.pexels.com/photos/7551617/pexels-photo-7551617.jpeg?auto=compress&cs=tinysrgb&w=1920&q=80',
    tag: 'Montego Bay · Jamaica',
    headline: 'Where Care Feels',
    headline2: 'Like Home',
    sub: 'Premium eldercare in the heart of Montego Bay. Compassionate, professional care your loved ones deserve — trusted by Jamaican families and the diaspora.',
  },
  {
    image: 'https://images.pexels.com/photos/7551570/pexels-photo-7551570.jpeg?auto=compress&cs=tinysrgb&w=1920&q=80',
    tag: '24/7 Nursing Supervision',
    headline: 'Clinical Excellence,',
    headline2: 'Caribbean Warmth',
    sub: 'Our licensed nursing team provides round-the-clock care — treating every resident with the respect, dignity, and love they have always deserved.',
  },
  {
    image: 'https://images.pexels.com/photos/7551759/pexels-photo-7551759.jpeg?auto=compress&cs=tinysrgb&w=1920&q=80',
    tag: 'For Diaspora Families',
    headline: 'Peace of Mind,',
    headline2: 'No Matter Where You Are',
    sub: 'Weekly video updates, digital care reports, and a dedicated family liaison — so you can be present for your loved one even from thousands of miles away.',
  },
  {
    image: 'https://images.pexels.com/photos/7551596/pexels-photo-7551596.jpeg?auto=compress&cs=tinysrgb&w=1920&q=80',
    tag: 'A Life Well Lived',
    headline: 'Joy, Dignity &',
    headline2: 'Connection Every Day',
    sub: 'Activities, garden walks, music, and a vibrant community — because quality of life matters just as much as quality of care.',
  },
];

export default function HeroCarousel() {
  const [current, setCurrent] = useState(0);
  const [animating, setAnimating] = useState(false);

  const goTo = useCallback(
    (idx: number) => {
      if (animating) return;
      setAnimating(true);
      setCurrent(idx);
      setTimeout(() => setAnimating(false), 700);
    },
    [animating]
  );

  const next = useCallback(() => goTo((current + 1) % slides.length), [current, goTo]);
  const prev = useCallback(() => goTo((current - 1 + slides.length) % slides.length), [current, goTo]);

  useEffect(() => {
    const id = setInterval(next, 6000);
    return () => clearInterval(id);
  }, [next]);

  const stats = [
    { value: '24/7', label: 'Nursing Care' },
    { value: '1:5', label: 'Staff Ratio' },
    { value: '15+', label: 'Yrs Experience' },
    { value: '100%', label: 'Family Trust' },
  ];

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* SLIDES */}
      {slides.map((slide, i) => (
        <div
          key={i}
          className={`absolute inset-0 transition-opacity duration-700 ${i === current ? 'opacity-100 z-10' : 'opacity-0 z-0'}`}
        >
          <img
            src={slide.image}
            alt={slide.headline}
            className="w-full h-full object-cover object-center scale-105"
            style={{ transform: i === current ? 'scale(1.02)' : 'scale(1)', transition: 'transform 7s ease-out' }}
          />
          <div className="absolute inset-0 bg-gradient-to-r from-brand-black/90 via-brand-black/60 to-brand-black/20" />
          <div className="absolute inset-0 bg-gradient-to-t from-brand-black/60 via-transparent to-transparent" />
        </div>
      ))}

      {/* CONTENT */}
      <div className="relative z-20 container-max px-6 md:px-12 lg:px-20 w-full">
        <div className="max-w-3xl">
          <p
            key={`tag-${current}`}
            className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-300 mb-6 animate-fade-in"
          >
            {slides[current].tag}
          </p>
          <h1
            key={`h-${current}`}
            className="font-serif text-5xl md:text-7xl lg:text-8xl text-white leading-tight mb-8 animate-slide-up text-shadow-lg"
          >
            {slides[current].headline}
            <br />
            <span className="italic text-gold-300">{slides[current].headline2}</span>
          </h1>
          <p
            key={`sub-${current}`}
            className="text-lg md:text-xl text-brand-cream/90 leading-relaxed mb-10 max-w-2xl animate-fade-in-delay-1"
          >
            {slides[current].sub}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 animate-fade-in-delay-2">
            <Link to="/contact" className="btn-primary">
              Schedule a Tour <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/quote"
              className="inline-flex items-center justify-center gap-2 rounded-full border-2 border-white/70 px-8 py-4 text-sm font-semibold uppercase tracking-wider text-white transition-all duration-300 hover:bg-white hover:text-brand-black backdrop-blur-sm"
            >
              Request a Quote
            </Link>
          </div>
        </div>
      </div>

      {/* ARROWS */}
      <button
        onClick={prev}
        className="absolute left-4 md:left-8 top-1/2 -translate-y-1/2 z-30 w-12 h-12 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center text-white hover:bg-gold-500 hover:text-brand-black transition-all duration-300"
        aria-label="Previous slide"
      >
        <ChevronLeft className="h-6 w-6" />
      </button>
      <button
        onClick={next}
        className="absolute right-4 md:right-8 top-1/2 -translate-y-1/2 z-30 w-12 h-12 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center text-white hover:bg-gold-500 hover:text-brand-black transition-all duration-300"
        aria-label="Next slide"
      >
        <ChevronRight className="h-6 w-6" />
      </button>

      {/* DOTS */}
      <div className="absolute bottom-32 left-1/2 -translate-x-1/2 z-30 flex gap-3">
        {slides.map((_, i) => (
          <button
            key={i}
            onClick={() => goTo(i)}
            className={`transition-all duration-300 rounded-full ${
              i === current
                ? 'w-10 h-2.5 bg-gold-400'
                : 'w-2.5 h-2.5 bg-white/40 hover:bg-white/70'
            }`}
            aria-label={`Go to slide ${i + 1}`}
          />
        ))}
      </div>

      {/* STATS BAR */}
      <div className="absolute bottom-0 left-0 right-0 z-30">
        <div className="container-max px-6 md:px-12 lg:px-20 pb-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-brand-black/60 backdrop-blur-xl rounded-2xl p-6 border border-white/10">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="font-serif text-3xl md:text-4xl font-bold text-gold-300">{stat.value}</p>
                <p className="text-xs uppercase tracking-wider text-brand-cream/60 mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* SLIDE COUNTER */}
      <div className="absolute top-32 right-6 md:right-12 z-30 text-white/50 text-sm font-mono">
        <span className="text-gold-300 font-bold">{String(current + 1).padStart(2, '0')}</span>
        {' / '}
        {String(slides.length).padStart(2, '0')}
      </div>
    </section>
  );
}
