import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, User, LogOut } from 'lucide-react';
import { getSession, logout, onSessionChanged, type SessionInfo } from '../lib/odoo';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [session, setSession] = useState<SessionInfo | null>(null);
  const location = useLocation();

  useEffect(() => {
    const refresh = () => getSession().then(setSession).catch(() => setSession(null));
    refresh();
    return onSessionChanged(refresh);
  }, []);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Services', path: '/services' },
    { name: 'About', path: '/about' },
    { name: 'Facility', path: '/facility' },
    { name: 'Contact', path: '/contact' },
  ];

  const isActive = (path: string) => location.pathname === path;

  const onLogout = async () => {
    await logout();
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-brand-cream/95 backdrop-blur-md shadow-lg py-3'
          : 'bg-transparent py-5'
      }`}
    >
      <div className="container-max px-6 md:px-12 lg:px-20">
        <div className="flex items-center justify-between">
          {/* LOGO */}
          <Link to="/" className="flex items-center gap-3">
            <img
              src="/logo.jpg"
              alt="Peart Serenity Residence"
              className={`h-12 w-12 rounded-full object-cover ring-2 transition-all duration-300 ${scrolled ? 'ring-gold-500' : 'ring-gold-400/70'}`}
            />
            <div>
              <h1 className={`font-serif text-lg font-bold leading-none transition-colors duration-300 ${scrolled ? 'text-brand-black' : 'text-white'}`}>
                Peart Serenity
              </h1>
              <p className={`text-[10px] uppercase tracking-[0.25em] transition-colors duration-300 ${scrolled ? 'text-gold-600' : 'text-gold-300'}`}>
                Nursing Home Residence
              </p>
            </div>
          </Link>

          {/* DESKTOP NAV */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`text-sm font-medium uppercase tracking-wider transition-colors duration-300 ${
                  scrolled
                    ? isActive(link.path)
                      ? 'text-gold-600'
                      : 'text-brand-textgrey hover:text-gold-600'
                    : isActive(link.path)
                      ? 'text-white border-b-2 border-gold-400 pb-1'
                      : 'text-cream/80 hover:text-white'
                }`}
              >
                {link.name}
              </Link>
            ))}

            {session?.uid ? (
              <div className="flex items-center gap-3">
                <Link to="/dashboard" className="flex items-center gap-2 text-sm font-medium text-brand-textgrey hover:text-gold-600 transition-colors">
                  <User className="h-4 w-4" />
                  Dashboard
                </Link>
                <button onClick={onLogout} className="text-sm font-medium text-brand-textgrey hover:text-gold-600 transition-colors flex items-center gap-1">
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <Link to="/auth" className="text-sm font-medium uppercase tracking-wider text-brand-textgrey hover:text-gold-600 transition-colors">
                Sign In
              </Link>
            )}

            <Link to="/quote" className="btn-primary !py-3 !px-6 text-xs">
              Request Quote
            </Link>
          </div>

          {/* MOBILE TOGGLE */}
          <button
            className="md:hidden"
            onClick={() => setIsOpen(!isOpen)}
            aria-label="Toggle menu"
          >
            {isOpen ? (
              <X className={`h-6 w-6 ${scrolled ? 'text-brand-black' : 'text-white'}`} />
            ) : (
              <Menu className={`h-6 w-6 ${scrolled ? 'text-brand-black' : 'text-white'}`} />
            )}
          </button>
        </div>

        {/* MOBILE MENU */}
        {isOpen && (
          <div className="md:hidden mt-4 pb-4 animate-fade-in">
            <div className="flex flex-col gap-4 bg-white rounded-2xl shadow-xl p-6">
              <div className="flex items-center gap-3 pb-4 border-b border-brand-softgrey">
                <img src="/logo.jpg" alt="Logo" className="h-10 w-10 rounded-full object-cover ring-2 ring-gold-400" />
                <div>
                  <p className="font-serif font-bold text-brand-black text-sm">Peart Serenity</p>
                  <p className="text-[10px] uppercase tracking-widest text-gold-600">Nursing Home Residence</p>
                </div>
              </div>
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`text-sm font-medium uppercase tracking-wider ${
                    isActive(link.path) ? 'text-gold-600' : 'text-brand-textgrey'
                  }`}
                >
                  {link.name}
                </Link>
              ))}
              <div className="border-t border-brand-softgrey pt-4">
                {session?.uid ? (
                  <>
                    <Link to="/dashboard" className="block text-sm font-medium text-brand-textgrey mb-3">Dashboard</Link>
                    <button onClick={onLogout} className="block text-sm font-medium text-brand-textgrey">Sign Out</button>
                  </>
                ) : (
                  <Link to="/auth" className="block text-sm font-medium text-brand-textgrey mb-3">Sign In / Register</Link>
                )}
                <Link to="/quote" className="btn-primary text-xs w-full mt-3">
                  Request Quote
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
