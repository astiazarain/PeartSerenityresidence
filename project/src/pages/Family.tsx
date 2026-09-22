import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Bot, Download, FileText, HeartPulse, Loader2, Lock, Pill, Send, ShieldAlert, User,
} from 'lucide-react';
import {
  askAria, fetchMyResidents, fetchResidentDocuments, fetchResidentRecord, fetchResidentSummary,
  fetchResidentTimeline, getSession, residentDocumentUrl,
  type AriaTurn, type FamilyLang, type MyResident, type PortalDocument, type PortalMedication,
  type ResidentRecord, type ResidentSummary, type ShiftUpdate,
} from '../lib/odoo';
import { useFamilyLang } from '../lib/familyI18n';

type Tab = 'summary' | 'updates' | 'record' | 'documents' | 'aria';
type T = (key: string) => string;

const TABS: Tab[] = ['summary', 'updates', 'record', 'documents', 'aria'];

const fmtDate = (value: string, lang: FamilyLang) =>
  new Date(value.length <= 10 ? `${value}T00:00:00` : value.replace(' ', 'T') + 'Z')
    .toLocaleDateString(lang === 'es' ? 'es-JM' : 'en-JM', { year: 'numeric', month: 'short', day: 'numeric' });

function Section({ title, icon: Icon, children }: { title: string; icon?: typeof HeartPulse; children: React.ReactNode }) {
  return (
    <section className="bg-white rounded-2xl p-6 shadow-lg">
      <h3 className="font-serif text-xl text-brand-black mb-4 flex items-center gap-2">
        {Icon && <Icon className="h-5 w-5 text-gold-600" />}
        {title}
      </h3>
      {children}
    </section>
  );
}

const Empty = ({ t }: { t: T }) => <p className="text-sm text-brand-textgrey">{t('none')}</p>;

function Facts({ items }: { items: [string, string][] }) {
  if (!items.length) return null;
  return (
    <dl className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-xl bg-brand-cream px-4 py-3">
          <dt className="text-xs uppercase tracking-wider text-brand-textgrey">{label}</dt>
          <dd className="font-semibold text-brand-black mt-1">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function updateFacts(u: ShiftUpdate, t: T): { vitals: [string, string][]; care: [string, string][] } {
  const v = u.vitals;
  const vitals: [string, string][] = [];
  if (v.bp_systolic && v.bp_diastolic) vitals.push([t('vital.bp'), `${v.bp_systolic}/${v.bp_diastolic} mmHg`]);
  if (v.heart_rate) vitals.push([t('vital.heart_rate'), `${v.heart_rate} bpm`]);
  if (v.resp_rate) vitals.push([t('vital.resp_rate'), `${v.resp_rate} /min`]);
  if (v.temperature) vitals.push([t('vital.temperature'), `${v.temperature} °C`]);
  if (v.spo2) vitals.push([t('vital.spo2'), `${v.spo2}%`]);
  if (v.glucose) vitals.push([t('vital.glucose'), `${v.glucose} mg/dL`]);
  if (v.weight) vitals.push([t('vital.weight'), `${v.weight} kg`]);

  const c = u.care;
  const care: [string, string][] = [];
  if (c.intake_pct !== undefined) care.push([t('care.intake_pct'), `${c.intake_pct}%`]);
  if (c.fluids_ml) care.push([t('care.fluids_ml'), String(c.fluids_ml)]);
  if (c.hygiene) care.push([t('care.hygiene'), t(`hygiene.${c.hygiene}`)]);
  if (c.mobility) care.push([t('care.mobility'), t(`mobility.${c.mobility}`)]);
  if (c.sleep) care.push([t('care.sleep'), t(`sleep.${c.sleep}`)]);
  if (c.mood) care.push([t('care.mood'), t(`mood.${c.mood}`)]);
  if (c.activities) care.push([t('care.activities'), String(c.activities)]);
  if (c.visitors) care.push([t('care.visitors'), String(c.visitors)]);
  return { vitals, care };
}

function UpdateCard({ update, lang, t }: { update: ShiftUpdate; lang: FamilyLang; t: T }) {
  const { vitals, care } = updateFacts(update, t);
  return (
    <div className="space-y-4">
      <p className="text-sm font-semibold text-gold-700">
        {fmtDate(update.date, lang)} · {t(`shift.${update.shift}`)}
      </p>
      {update.family_note && <p className="text-brand-black leading-relaxed whitespace-pre-line">{update.family_note}</p>}
      {vitals.length > 0 && (<div><p className="text-sm font-semibold mb-2">{t('vitals')}</p><Facts items={vitals} /></div>)}
      {care.length > 0 && (<div><p className="text-sm font-semibold mb-2">{t('care')}</p><Facts items={care} /></div>)}
    </div>
  );
}

function Medications({ meds, t }: { meds: PortalMedication[]; t: T }) {
  if (!meds.length) return <Empty t={t} />;
  return (
    <ul className="divide-y divide-brand-softgrey">
      {meds.map((m) => (
        <li key={m.id} className={`py-3 ${m.state === 'stopped' ? 'opacity-60' : ''}`}>
          <p className="font-semibold text-brand-black">{m.name} <span className="font-normal text-brand-textgrey">· {m.dose}</span></p>
          <p className="text-sm text-brand-textgrey">
            {t(`route.${m.route}`)} · {t(`freq.${m.frequency}`)}
            {m.schedule_times ? ` (${m.schedule_times})` : ''}
            {m.prn_reason ? ` · ${m.prn_reason}` : ''}
            {m.state === 'stopped' ? ` · ${t('medState.stopped')}` : ''}
          </p>
        </li>
      ))}
    </ul>
  );
}

function Allergies({ items, t }: { items: ResidentRecord['allergies']; t: T }) {
  if (!items.length) return <Empty t={t} />;
  return (
    <ul className="flex flex-wrap gap-2">
      {items.map((a) => (
        <li key={a.id} className="px-3 py-1.5 rounded-full bg-red-50 text-red-700 text-sm font-semibold">
          {a.name}{a.reaction ? ` (${a.reaction})` : ''} · {t(`severity.${a.severity}`)}
        </li>
      ))}
    </ul>
  );
}

function CarePlan({ items, lang, t }: { items: ResidentRecord['care_plan']; lang: FamilyLang; t: T }) {
  if (!items.length) return <Empty t={t} />;
  return (
    <ul className="space-y-4">
      {items.map((c) => (
        <li key={c.id}>
          <p className="font-semibold text-brand-black">{c.name}</p>
          <p className="text-sm text-brand-textgrey"><strong>{t('goal')}:</strong> {c.goal}</p>
          <p className="text-sm text-brand-textgrey"><strong>{t('actions')}:</strong> {c.intervention}</p>
          {c.review_date && <p className="text-xs text-brand-textgrey mt-1">{t('reviewOn')}: {fmtDate(c.review_date, lang)}</p>}
        </li>
      ))}
    </ul>
  );
}

function Notices({ items, lang, t }: { items: ResidentRecord['incidents']; lang: FamilyLang; t: T }) {
  if (!items.length) return <Empty t={t} />;
  return (
    <ul className="space-y-3">
      {items.map((i) => (
        <li key={i.id} className="rounded-xl bg-amber-50 px-4 py-3">
          <p className="text-sm font-semibold text-amber-800">{t(`incident.${i.kind}`)} · {fmtDate(i.date, lang)}</p>
          <p className="text-sm text-brand-black mt-1 whitespace-pre-line">{i.summary}</p>
        </li>
      ))}
    </ul>
  );
}

function SummaryTab({ data, lang, t }: { data: ResidentSummary; lang: FamilyLang; t: T }) {
  return (
    <div className="grid gap-6">
      <Section title={t('latestUpdate')} icon={HeartPulse}>
        {data.latest_update ? <UpdateCard update={data.latest_update} lang={lang} t={t} /> : <p className="text-sm text-brand-textgrey">{t('noUpdates')}</p>}
      </Section>
      <div className="grid md:grid-cols-2 gap-6">
        <Section title={t('medications')} icon={Pill}><Medications meds={data.medications} t={t} /></Section>
        <Section title={t('allergies')} icon={ShieldAlert}><Allergies items={data.allergies} t={t} /></Section>
      </div>
      <Section title={t('carePlan')}><CarePlan items={data.care_plan} lang={lang} t={t} /></Section>
      {data.incidents.length > 0 && <Section title={t('incidents')}><Notices items={data.incidents} lang={lang} t={t} /></Section>}
    </div>
  );
}

function UpdatesTab({ residentId, lang, t }: { residentId: number; lang: FamilyLang; t: T }) {
  const [items, setItems] = useState<ShiftUpdate[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback((offset: number) => {
    setLoading(true);
    fetchResidentTimeline(residentId, lang, offset, 20)
      .then((res) => {
        setTotal(res.total);
        setItems((prev) => (offset === 0 ? res.items : [...prev, ...res.items]));
        setError(false);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [residentId, lang]);

  useEffect(() => { load(0); }, [load]);

  if (error) return <p className="text-red-600">{t('loadError')}</p>;
  return (
    <div className="space-y-4">
      {items.map((u) => (
        <div key={u.id} className="bg-white rounded-2xl p-6 shadow-lg"><UpdateCard update={u} lang={lang} t={t} /></div>
      ))}
      {!loading && items.length === 0 && <p className="text-brand-textgrey">{t('noUpdates')}</p>}
      {loading && <Loader2 className="h-6 w-6 animate-spin text-gold-500 mx-auto" />}
      {!loading && items.length < total && (
        <button onClick={() => load(items.length)} className="btn-outline mx-auto block">{t('loadMore')}</button>
      )}
    </div>
  );
}

function RecordTab({ residentId, lang, t }: { residentId: number; lang: FamilyLang; t: T }) {
  const [rec, setRec] = useState<ResidentRecord | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    setRec(null);
    fetchResidentRecord(residentId, lang).then(setRec).catch(() => setError(true));
  }, [residentId, lang]);

  if (error) return <p className="text-red-600">{t('loadError')}</p>;
  if (!rec) return <Loader2 className="h-6 w-6 animate-spin text-gold-500 mx-auto" />;
  return (
    <div className="grid gap-6">
      <Section title={t('conditions')}>
        {rec.conditions.length === 0 ? <Empty t={t} /> : (
          <ul className="divide-y divide-brand-softgrey">
            {rec.conditions.map((c) => (
              <li key={c.id} className="py-3 flex justify-between gap-4">
                <span className="font-semibold">{c.name} <span className="font-normal text-brand-textgrey">· {t(`cond.${c.kind}`)}</span></span>
                <span className="text-sm text-brand-textgrey">{t(`condStatus.${c.status}`)}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>
      <Section title={t('allergies')} icon={ShieldAlert}><Allergies items={rec.allergies} t={t} /></Section>
      <Section title={t('medications')} icon={Pill}><Medications meds={rec.medications} t={t} /></Section>
      <Section title={t('carePlan')}><CarePlan items={rec.care_plan} lang={lang} t={t} /></Section>
      <Section title={t('assessments')}>
        {rec.assessments.length === 0 ? <Empty t={t} /> : (
          <ul className="divide-y divide-brand-softgrey">
            {rec.assessments.map((a) => (
              <li key={a.id} className="py-3">
                <p className="font-semibold">{a.scale}</p>
                <p className="text-sm text-brand-textgrey">
                  {fmtDate(a.date, lang)} · {t('score')} {a.total}/{a.max_score}{a.result ? ` · ${a.result}` : ''}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Section>
      {rec.incidents.length > 0 && <Section title={t('incidents')}><Notices items={rec.incidents} lang={lang} t={t} /></Section>}
    </div>
  );
}

function DocumentsTab({ residentId, lang, t }: { residentId: number; lang: FamilyLang; t: T }) {
  const [docs, setDocs] = useState<PortalDocument[] | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    fetchResidentDocuments(residentId, lang).then(setDocs).catch(() => setError(true));
  }, [residentId, lang]);

  if (error) return <p className="text-red-600">{t('loadError')}</p>;
  if (!docs) return <Loader2 className="h-6 w-6 animate-spin text-gold-500 mx-auto" />;
  if (!docs.length) return <Empty t={t} />;
  return (
    <div className="space-y-3">
      {docs.map((d) => (
        <div key={d.id} className="bg-white rounded-2xl p-5 shadow-lg flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <FileText className="h-6 w-6 text-gold-600 flex-shrink-0" />
            <div className="min-w-0">
              <p className="font-semibold text-brand-black truncate">{d.name}</p>
              <p className="text-sm text-brand-textgrey">{t(`doc.${d.category}`)}{d.date ? ` · ${fmtDate(d.date, lang)}` : ''}</p>
            </div>
          </div>
          <a href={residentDocumentUrl(d.id)} download className="btn-outline inline-flex items-center gap-2 flex-shrink-0">
            <Download className="h-4 w-4" /> {t('download')}
          </a>
        </div>
      ))}
    </div>
  );
}

type ChatItem = AriaTurn & { escalated?: boolean };

function AriaTab({ resident, lang, t }: { resident: MyResident; lang: FamilyLang; t: T }) {
  const [messages, setMessages] = useState<ChatItem[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => { setMessages([]); }, [resident.id]);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, busy]);

  if (!resident.ai_enabled) {
    return <div className="bg-white rounded-2xl p-8 shadow-lg text-center text-brand-textgrey"><Lock className="h-8 w-8 mx-auto mb-3 text-brand-softgrey" />{t('ariaNoConsent')}</div>;
  }

  const send = async () => {
    const text = draft.trim();
    if (!text || busy) return;
    const history: AriaTurn[] = messages.map(({ role, content }) => ({ role, content }));
    setMessages((m) => [...m, { role: 'user', content: text }]);
    setDraft('');
    setBusy(true);
    try {
      const res = await askAria(resident.id, text, history, lang);
      setMessages((m) => [...m, { role: 'aria', content: res.reply, escalated: res.route === 'escalated' }]);
    } catch {
      setMessages((m) => [...m, { role: 'aria', content: t('ariaError') }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      <div className="p-6 space-y-4 min-h-[320px] max-h-[520px] overflow-y-auto">
        <div className="flex gap-3">
          <Bot className="h-6 w-6 text-gold-600 flex-shrink-0 mt-1" />
          <p className="rounded-2xl bg-brand-cream px-4 py-3 text-brand-black">{t('ariaIntro')}</p>
        </div>
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : ''}`}>
            {m.role === 'aria' && <Bot className="h-6 w-6 text-gold-600 flex-shrink-0 mt-1" />}
            <div className={`rounded-2xl px-4 py-3 max-w-[85%] whitespace-pre-line ${m.role === 'user' ? 'bg-brand-black text-white' : 'bg-brand-cream text-brand-black'}`}>
              {m.content}
              {m.escalated && <p className="text-xs text-gold-700 font-semibold mt-2">{t('ariaEscalated')}</p>}
            </div>
          </div>
        ))}
        {busy && <p className="text-sm text-brand-textgrey">{t('ariaThinking')}</p>}
        <div ref={bottom} />
      </div>
      <form onSubmit={(e) => { e.preventDefault(); void send(); }} className="border-t border-brand-softgrey p-4 flex gap-3">
        <input value={draft} onChange={(e) => setDraft(e.target.value)} maxLength={1000}
               placeholder={t('ariaPlaceholder')} className="input-field flex-1" aria-label={t('ariaPlaceholder')} />
        <button type="submit" disabled={busy || !draft.trim()} className="btn-primary inline-flex items-center gap-2 disabled:opacity-50">
          <Send className="h-4 w-4" /> {t('ariaSend')}
        </button>
      </form>
      <p className="px-6 pb-4 text-xs text-brand-textgrey">{t('ariaNotice')}</p>
    </div>
  );
}

export default function Family() {
  const navigate = useNavigate();
  const { lang, setLang, t } = useFamilyLang();
  const [residents, setResidents] = useState<MyResident[] | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [tab, setTab] = useState<Tab>('summary');
  const [summary, setSummary] = useState<ResidentSummary | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getSession().then((s) => {
      if (!s.uid) { navigate('/auth'); return; }
      fetchMyResidents()
        .then((list) => {
          setResidents(list);
          if (list[0]) setSelectedId(list[0].id);
        })
        .catch(() => setError(true));
    });
  }, [navigate]);

  useEffect(() => {
    if (selectedId === null) return;
    setSummary(null);
    fetchResidentSummary(selectedId, lang).then(setSummary).catch(() => setError(true));
  }, [selectedId, lang]);

  const resident = residents?.find((r) => r.id === selectedId) ?? null;

  return (
    <div className="min-h-screen bg-brand-cream pt-24 pb-20">
      <div className="container-max px-6 md:px-12 lg:px-20">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
          <div>
            <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm font-semibold text-brand-textgrey hover:text-gold-600 mb-3">
              <ArrowLeft className="h-4 w-4" /> {t('backToAccount')}
            </Link>
            <h1 className="font-serif text-4xl text-brand-black">{t('title')}</h1>
          </div>
          <div role="group" aria-label="Language" className="inline-flex rounded-full border border-brand-softgrey bg-white overflow-hidden">
            {(['en', 'es'] as const).map((l) => (
              <button key={l} onClick={() => setLang(l)} aria-pressed={lang === l}
                      className={`px-4 py-2 text-sm font-semibold ${lang === l ? 'bg-brand-black text-white' : 'text-brand-textgrey'}`}>
                {l.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-red-600 mb-6">{t('loadError')}</p>}
        {!residents && !error && <Loader2 className="h-8 w-8 animate-spin text-gold-500 mx-auto" />}

        {residents && residents.length === 0 && (
          <div className="bg-white rounded-2xl p-12 text-center shadow-lg">
            <Lock className="h-12 w-12 text-brand-softgrey mx-auto mb-4" />
            <h2 className="font-serif text-2xl mb-2">{t('noAccessTitle')}</h2>
            <p className="text-brand-textgrey mb-6 max-w-xl mx-auto">{t('noAccessBody')}</p>
            <Link to="/contact" className="btn-primary">{t('contactUs')}</Link>
          </div>
        )}

        {resident && (
          <>
            <div className="bg-brand-black rounded-2xl p-6 mb-6 flex flex-wrap items-center gap-5 text-white">
              {resident.photo
                ? <img src={`data:image/png;base64,${resident.photo}`} alt="" className="w-20 h-20 rounded-full object-cover" />
                : <div className="w-20 h-20 rounded-full bg-white/10 flex items-center justify-center"><User className="h-8 w-8 text-gold-400" /></div>}
              <div className="flex-1 min-w-[200px]">
                {residents!.length > 1 ? (
                  <select value={selectedId ?? ''} onChange={(e) => { setSelectedId(Number(e.target.value)); setTab('summary'); }}
                          className="bg-transparent font-serif text-2xl border-b border-white/30" aria-label={t('resident')}>
                    {residents!.map((r) => <option key={r.id} value={r.id} className="text-black">{r.name}</option>)}
                  </select>
                ) : <h2 className="font-serif text-2xl">{resident.name}</h2>}
                <p className="text-sm text-brand-cream/70 mt-1">
                  {t(`state.${resident.state}`)}
                  {summary ? ` · ${t('age')} ${summary.age} ${t('years')}` : ''}
                  {summary?.room ? ` · ${t('room')} ${summary.room}` : ''}
                  {summary?.admission_date ? ` · ${t('admitted')} ${fmtDate(summary.admission_date, lang)}` : ''}
                </p>
              </div>
            </div>

            <div role="tablist" className="flex gap-2 overflow-x-auto mb-6">
              {TABS.map((id) => (
                <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}
                        className={`px-5 py-2.5 rounded-full text-sm font-semibold whitespace-nowrap ${tab === id ? 'bg-gold-500 text-brand-black' : 'bg-white text-brand-textgrey'}`}>
                  {t(`tab.${id}`)}
                </button>
              ))}
            </div>

            {tab === 'summary' && (summary ? <SummaryTab data={summary} lang={lang} t={t} /> : <Loader2 className="h-6 w-6 animate-spin text-gold-500 mx-auto" />)}
            {tab === 'updates' && <UpdatesTab residentId={resident.id} lang={lang} t={t} />}
            {tab === 'record' && <RecordTab residentId={resident.id} lang={lang} t={t} />}
            {tab === 'documents' && <DocumentsTab residentId={resident.id} lang={lang} t={t} />}
            {tab === 'aria' && <AriaTab resident={resident} lang={lang} t={t} />}
          </>
        )}
      </div>
    </div>
  );
}
