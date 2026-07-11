import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

export default function CTASection() {
  return (
    <section className="relative overflow-hidden bg-brand-black py-24">
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-96 h-96 bg-gold-500 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-gold-400 rounded-full blur-3xl translate-x-1/2 translate-y-1/2"></div>
      </div>
      <div className="container-max px-6 md:px-12 lg:px-20 relative z-10">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-400 mb-4">
            Where Care Feels Like Home
          </p>
          <h2 className="font-serif text-4xl md:text-5xl text-white mb-6">
            Ready to Find Peace of Mind?
          </h2>
          <p className="text-lg text-brand-softgrey/80 mb-10 leading-relaxed">
            Schedule a personal tour of our Montego Bay residence. Meet our care team,
            walk our gardens, and discover why families across Jamaica and the diaspora
            trust us with their loved ones.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/contact" className="btn-primary">
              Book a Tour <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/quote"
              className="inline-flex items-center justify-center gap-2 rounded-full border-2 border-gold-500 px-8 py-4 text-sm font-semibold uppercase tracking-wider text-gold-400 transition-all duration-300 hover:bg-gold-500 hover:text-brand-black"
            >
              Request a Quote
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
