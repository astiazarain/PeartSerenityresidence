import { Link } from 'react-router-dom';
import { Mail, Phone, MapPin, Facebook, Instagram, Linkedin, Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-brand-black text-brand-softgrey">
      <div className="container-max px-6 py-16 md:px-12 lg:px-20">
        <div className="grid grid-cols-1 gap-12 md:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <img src="/logo.jpg" alt="Peart Serenity Residence" className="h-12 w-12 rounded-full object-cover ring-2 ring-gold-500" />
              <div>
                <h3 className="font-serif text-xl font-bold text-white">Peart Serenity</h3>
                <p className="text-[10px] uppercase tracking-[0.25em] text-gold-400">Nursing Home Residence</p>
              </div>
            </div>
            <p className="text-sm leading-relaxed text-brand-softgrey/70">
              Premium eldercare in Montego Bay, Jamaica. Where care feels like home —
              trusted by families across Jamaica and the diaspora.
            </p>
            <div className="flex gap-4 mt-6">
              <a href="#" className="p-2 rounded-full bg-brand-charcoal hover:bg-gold-500 hover:text-brand-black transition-colors duration-300">
                <Facebook className="h-4 w-4" />
              </a>
              <a href="#" className="p-2 rounded-full bg-brand-charcoal hover:bg-gold-500 hover:text-brand-black transition-colors duration-300">
                <Instagram className="h-4 w-4" />
              </a>
              <a href="#" className="p-2 rounded-full bg-brand-charcoal hover:bg-gold-500 hover:text-brand-black transition-colors duration-300">
                <Linkedin className="h-4 w-4" />
              </a>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wider text-gold-400 mb-6">Quick Links</h4>
            <ul className="space-y-3 text-sm">
              <li><Link to="/" className="hover:text-gold-400 transition-colors">Home</Link></li>
              <li><Link to="/services" className="hover:text-gold-400 transition-colors">Services & Pricing</Link></li>
              <li><Link to="/about" className="hover:text-gold-400 transition-colors">About Us</Link></li>
              <li><Link to="/facility" className="hover:text-gold-400 transition-colors">Our Facility</Link></li>
              <li><Link to="/contact" className="hover:text-gold-400 transition-colors">Contact & Tours</Link></li>
              <li><Link to="/quote" className="hover:text-gold-400 transition-colors">Request a Quote</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wider text-gold-400 mb-6">Our Services</h4>
            <ul className="space-y-3 text-sm">
              <li><Link to="/services" className="hover:text-gold-400 transition-colors">Adult Day Care</Link></li>
              <li><Link to="/services" className="hover:text-gold-400 transition-colors">Respite Care</Link></li>
              <li><Link to="/services" className="hover:text-gold-400 transition-colors">Long-Term Residential</Link></li>
              <li><Link to="/services" className="hover:text-gold-400 transition-colors">Private Suites</Link></li>
              <li><Link to="/services" className="hover:text-gold-400 transition-colors">Post-Surgical Recovery</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wider text-gold-400 mb-6">Get in Touch</h4>
            <ul className="space-y-4 text-sm">
              <li className="flex items-start gap-3">
                <MapPin className="h-5 w-5 text-gold-500 flex-shrink-0 mt-0.5" />
                <span>Montego Bay, St. James Parish, Jamaica</span>
              </li>
              <li className="flex items-center gap-3">
                <Phone className="h-5 w-5 text-gold-500 flex-shrink-0" />
                <span>+1 (876) 555-0192</span>
              </li>
              <li className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-gold-500 flex-shrink-0" />
                <span>care@peartserenity.com</span>
              </li>
            </ul>
            <Link to="/contact" className="btn-primary mt-6 text-xs !py-3 !px-6">
              Schedule a Tour
            </Link>
          </div>
        </div>

        <div className="border-t border-brand-charcoal mt-12 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-brand-softgrey/50">
            &copy; {new Date().getFullYear()} Peart Serenity Residence. All rights reserved.
          </p>
          <p className="text-xs text-brand-softgrey/50 flex items-center gap-2">
            Designed with <Heart className="h-3 w-3 text-gold-500" fill="currentColor" /> for families in Jamaica and the diaspora.
          </p>
        </div>
      </div>
    </footer>
  );
}
