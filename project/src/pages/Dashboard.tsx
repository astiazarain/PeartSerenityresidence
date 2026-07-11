import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Plus,
  Calendar,
  Mail,
  Phone,
  LogOut,
  User,
} from 'lucide-react';
import { supabase } from '../lib/supabase';
import type { Session } from '@supabase/supabase-js';

type QuoteStatus = 'pending' | 'reviewed' | 'quoted' | 'accepted' | 'rejected';

const statusConfig: Record<QuoteStatus, { label: string; color: string; icon: typeof Clock }> = {
  pending:   { label: 'Pending Review',   color: 'bg-amber-100 text-amber-700',   icon: Clock },
  reviewed:  { label: 'Under Review',      color: 'bg-blue-100 text-blue-700',     icon: Clock },
  quoted:    { label: 'Quote Ready',        color: 'bg-gold-100 text-gold-700',     icon: CheckCircle2 },
  accepted:  { label: 'Accepted',           color: 'bg-green-100 text-green-700',   icon: CheckCircle2 },
  rejected:  { label: 'Rejected',            color: 'bg-red-100 text-red-700',       icon: XCircle },
};

export default function Dashboard() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [tours, setTours] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) { navigate('/auth'); return; }
      setSession(data.session);
      fetchData(data.session.user.id);
    });
  }, [navigate]);

  const fetchData = async (userId: string) => {
    setLoading(true);
    const [quotesRes, toursRes] = await Promise.all([
      supabase.from('quote_requests').select('*').eq('user_id', userId).order('created_at', { ascending: false }),
      supabase.from('tour_bookings').select('*').eq('name', session?.user?.email ?? '').order('created_at', { ascending: false }),
    ]);
    if (quotesRes.data) setQuotes(quotesRes.data);
    if (toursRes.data) setTours(toursRes.data);
    setLoading(false);
  };

  const onLogout = async () => {
    await supabase.auth.signOut();
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-brand-cream pt-20">
        <Loader2 className="h-8 w-8 animate-spin text-gold-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-brand-cream pt-24 pb-20">
      <div className="container-max px-6 md:px-12 lg:px-20">
        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-12">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-gold-600 mb-2">My Account</p>
            <h1 className="font-serif text-4xl text-brand-black">Welcome, {session?.user?.user_metadata?.full_name || session?.user?.email}</h1>
          </div>
          <button onClick={onLogout} className="inline-flex items-center gap-2 text-sm font-semibold text-brand-textgrey hover:text-gold-600 transition-colors">
            <LogOut className="h-4 w-4" /> Sign Out
          </button>
        </div>

        {/* QUICK ACTIONS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <Link to="/quote" className="bg-brand-black rounded-2xl p-8 hover:shadow-2xl transition-all duration-300 group">
            <Plus className="h-8 w-8 text-gold-400 mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="font-serif text-xl text-white mb-1">New Quote Request</h3>
            <p className="text-sm text-brand-cream/60">Submit a new care quote request</p>
          </Link>
          <Link to="/contact" className="bg-gold-500 rounded-2xl p-8 hover:shadow-2xl transition-all duration-300 group">
            <Calendar className="h-8 w-8 text-brand-black mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="font-serif text-xl text-brand-black mb-1">Book a Tour</h3>
            <p className="text-sm text-brand-black/60">Schedule a visit to our facility</p>
          </Link>
          <Link to="/services" className="bg-white rounded-2xl p-8 hover:shadow-2xl transition-all duration-300 group border border-brand-softgrey">
            <FileText className="h-8 w-8 text-gold-600 mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="font-serif text-xl text-brand-black mb-1">View Services</h3>
            <p className="text-sm text-brand-textgrey">Browse our care plans and pricing</p>
          </Link>
        </div>

        {/* QUOTE REQUESTS */}
        <div className="mb-12">
          <h2 className="font-serif text-2xl text-brand-black mb-6">Your Quote Requests</h2>
          {quotes.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 text-center shadow-lg">
              <FileText className="h-12 w-12 text-brand-softgrey mx-auto mb-4" />
              <p className="text-brand-textgrey mb-4">You haven't submitted any quote requests yet.</p>
              <Link to="/quote" className="btn-primary">Request a Quote</Link>
            </div>
          ) : (
            <div className="space-y-4">
              {quotes.map((q) => {
                const status = (q.status as QuoteStatus) || 'pending';
                const config = statusConfig[status];
                const StatusIcon = config.icon;
                return (
                  <div key={q.id} className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-xl bg-gold-50 flex items-center justify-center flex-shrink-0">
                          <FileText className="h-6 w-6 text-gold-600" />
                        </div>
                        <div>
                          <h3 className="font-serif text-lg text-brand-black">{q.resident_name}</h3>
                          <p className="text-sm text-brand-textgrey">{q.care_type_requested.replace('_', ' ')} · Submitted {new Date(q.created_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold ${config.color}`}>
                        <StatusIcon className="h-4 w-4" />
                        {config.label}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* TOUR BOOKINGS */}
        <div>
          <h2 className="font-serif text-2xl text-brand-black mb-6">Your Tour Bookings</h2>
          {tours.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 text-center shadow-lg">
              <Calendar className="h-12 w-12 text-brand-softgrey mx-auto mb-4" />
              <p className="text-brand-textgrey mb-4">No tour bookings yet.</p>
              <Link to="/contact" className="btn-outline">Book a Tour</Link>
            </div>
          ) : (
            <div className="space-y-4">
              {tours.map((t) => (
                <div key={t.id} className="bg-white rounded-2xl p-6 shadow-lg">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-xl bg-gold-50 flex items-center justify-center flex-shrink-0">
                        <Calendar className="h-6 w-6 text-gold-600" />
                      </div>
                      <div>
                        <h3 className="font-serif text-lg text-brand-black">{t.preferred_date} · {t.preferred_time}</h3>
                        <p className="text-sm text-brand-textgrey">Party of {t.party_size} · {t.status}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
