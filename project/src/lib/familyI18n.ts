import { useCallback, useEffect, useState } from 'react';
import type { FamilyLang } from './odoo';

// Spanish/English strings for the family portal only. The rest of the public
// site is English; this covers the portal end to end, including the labels
// for the enumerated values Odoo sends as codes (mood, route, frequency...).

const STORAGE_KEY = 'peart-family-lang';

const en = {
  title: 'Family Portal',
  backToAccount: 'Back to my account',
  loading: 'Loading...',
  loadError: 'We could not load this information. Please try again.',
  noAccessTitle: 'No resident linked to your account yet',
  noAccessBody: 'For privacy, a family member can only see a resident once our team has linked their account and recorded the family consent. Please contact us and we will set it up.',
  contactUs: 'Contact us',
  resident: 'Resident',
  room: 'Room',
  age: 'Age',
  years: 'years',
  admitted: 'In residence since',
  'tab.summary': 'Summary',
  'tab.updates': 'Daily updates',
  'tab.record': 'Health record',
  'tab.documents': 'Documents',
  'tab.aria': 'Ask ARIA',
  latestUpdate: 'Latest update',
  noUpdates: 'No updates have been shared yet.',
  vitals: 'Vital signs',
  care: 'Daily care',
  medications: 'Medication',
  allergies: 'Allergies',
  carePlan: 'Care plan',
  incidents: 'Notices',
  conditions: 'Diagnoses shared with you',
  assessments: 'Assessments',
  none: 'Nothing to show.',
  goal: 'Goal',
  actions: 'What we are doing',
  reviewOn: 'Review',
  loadMore: 'Load more',
  score: 'Score',
  'vital.bp': 'Blood pressure',
  'vital.heart_rate': 'Heart rate',
  'vital.resp_rate': 'Breathing rate',
  'vital.temperature': 'Temperature',
  'vital.spo2': 'Oxygen (SpO2)',
  'vital.glucose': 'Blood sugar',
  'vital.weight': 'Weight',
  'care.intake_pct': 'Meals eaten',
  'care.fluids_ml': 'Fluids (ml)',
  'care.hygiene': 'Personal care',
  'care.mobility': 'Mobility',
  'care.sleep': 'Sleep',
  'care.mood': 'Mood',
  'care.activities': 'Activities',
  'care.visitors': 'Visitors',
  'shift.day': 'Day shift',
  'shift.night': 'Night shift',
  'mood.cheerful': 'Cheerful', 'mood.calm': 'Calm', 'mood.anxious': 'Anxious', 'mood.agitated': 'Restless',
  'mood.sad': 'Sad', 'mood.withdrawn': 'Withdrawn', 'mood.confused': 'Confused',
  'hygiene.full': 'Completed', 'hygiene.partial': 'Partly completed', 'hygiene.refused': 'Declined',
  'mobility.independent': 'Independent', 'mobility.assisted': 'With help', 'mobility.bed': 'Bed / chair',
  'sleep.good': 'Slept well', 'sleep.fair': 'Restless', 'sleep.poor': 'Poor sleep',
  'route.oral': 'By mouth', 'route.sl': 'Under the tongue', 'route.im': 'Injection (muscle)', 'route.iv': 'Intravenous',
  'route.sc': 'Injection (skin)', 'route.topical': 'On the skin', 'route.inhaled': 'Inhaled', 'route.eye': 'Eye / ear',
  'route.rectal': 'Rectal', 'route.other': 'Other',
  'freq.od': 'Once a day', 'freq.bid': 'Twice a day', 'freq.tid': 'Three times a day', 'freq.qid': 'Four times a day',
  'freq.q8h': 'Every 8 hours', 'freq.weekly': 'Weekly', 'freq.prn': 'Only when needed', 'freq.other': 'As directed',
  'medState.active': 'Current', 'medState.stopped': 'Stopped',
  'severity.mild': 'Mild', 'severity.moderate': 'Moderate', 'severity.severe': 'Severe',
  'cond.diagnosis': 'Diagnosis', 'cond.surgery': 'Surgery', 'cond.history': 'History', 'cond.family': 'Family history',
  'condStatus.active': 'Active', 'condStatus.chronic': 'Long-term', 'condStatus.resolved': 'Resolved',
  'incident.fall': 'Fall', 'incident.injury': 'Injury', 'incident.medication': 'Medication', 'incident.behaviour': 'Behaviour',
  'incident.skin': 'Skin', 'incident.choking': 'Choking', 'incident.elopement': 'Wandering', 'incident.infection': 'Illness', 'incident.other': 'Other',
  'doc.medical_report': 'Medical report', 'doc.lab': 'Lab result', 'doc.imaging': 'Imaging', 'doc.prescription': 'Prescription',
  'doc.id_document': 'ID', 'doc.legal': 'Legal', 'doc.insurance': 'Insurance', 'doc.billing': 'Billing', 'doc.consent': 'Consent', 'doc.other': 'Other',
  download: 'Download',
  'state.active': 'In residence', 'state.hospitalized': 'In hospital', 'state.discharged': 'Discharged', 'state.deceased': 'Deceased',
  ariaIntro: 'Hi, I am ARIA. I can explain in plain words what is in this record and pass your questions to our nursing team. I cannot give medical advice or change treatment.',
  ariaPlaceholder: 'Write your question...',
  ariaSend: 'Send',
  ariaThinking: 'ARIA is typing...',
  ariaError: 'ARIA is not available right now. Please try again or call the residence.',
  ariaNoConsent: 'The ARIA assistant is not enabled for this resident. Please ask our team if you would like it turned on.',
  ariaNotice: 'ARIA is an AI assistant. Your questions are recorded so our team can follow up. For anything urgent, call the residence.',
  ariaEscalated: 'Passed to our nursing team',
  signOut: 'Sign out',
} as const;

type Key = keyof typeof en;

const es: Record<Key, string> = {
  title: 'Portal familiar',
  backToAccount: 'Volver a mi cuenta',
  loading: 'Cargando...',
  loadError: 'No pudimos cargar esta información. Inténtalo de nuevo.',
  noAccessTitle: 'Aún no hay ningún residente vinculado a tu cuenta',
  noAccessBody: 'Por privacidad, un familiar solo puede ver a un residente cuando nuestro equipo ha vinculado su cuenta y registrado el consentimiento familiar. Contáctanos y lo configuramos.',
  contactUs: 'Contáctanos',
  resident: 'Residente',
  room: 'Habitación',
  age: 'Edad',
  years: 'años',
  admitted: 'En la residencia desde',
  'tab.summary': 'Resumen',
  'tab.updates': 'Novedades diarias',
  'tab.record': 'Expediente de salud',
  'tab.documents': 'Documentos',
  'tab.aria': 'Preguntar a ARIA',
  latestUpdate: 'Última novedad',
  noUpdates: 'Todavía no se ha compartido ninguna novedad.',
  vitals: 'Signos vitales',
  care: 'Cuidados del día',
  medications: 'Medicación',
  allergies: 'Alergias',
  carePlan: 'Plan de cuidados',
  incidents: 'Avisos',
  conditions: 'Diagnósticos compartidos contigo',
  assessments: 'Valoraciones',
  none: 'Nada que mostrar.',
  goal: 'Objetivo',
  actions: 'Qué estamos haciendo',
  reviewOn: 'Revisión',
  loadMore: 'Ver más',
  score: 'Puntaje',
  'vital.bp': 'Presión arterial',
  'vital.heart_rate': 'Pulso',
  'vital.resp_rate': 'Respiración',
  'vital.temperature': 'Temperatura',
  'vital.spo2': 'Oxígeno (SpO2)',
  'vital.glucose': 'Azúcar en sangre',
  'vital.weight': 'Peso',
  'care.intake_pct': 'Comidas ingeridas',
  'care.fluids_ml': 'Líquidos (ml)',
  'care.hygiene': 'Aseo personal',
  'care.mobility': 'Movilidad',
  'care.sleep': 'Sueño',
  'care.mood': 'Ánimo',
  'care.activities': 'Actividades',
  'care.visitors': 'Visitas',
  'shift.day': 'Turno de día',
  'shift.night': 'Turno de noche',
  'mood.cheerful': 'Alegre', 'mood.calm': 'Tranquilo/a', 'mood.anxious': 'Ansioso/a', 'mood.agitated': 'Inquieto/a',
  'mood.sad': 'Triste', 'mood.withdrawn': 'Retraído/a', 'mood.confused': 'Confundido/a',
  'hygiene.full': 'Completado', 'hygiene.partial': 'Parcial', 'hygiene.refused': 'Lo rechazó',
  'mobility.independent': 'Independiente', 'mobility.assisted': 'Con ayuda', 'mobility.bed': 'Cama / silla',
  'sleep.good': 'Durmió bien', 'sleep.fair': 'Sueño inquieto', 'sleep.poor': 'Durmió mal',
  'route.oral': 'Por la boca', 'route.sl': 'Bajo la lengua', 'route.im': 'Inyección (músculo)', 'route.iv': 'Intravenosa',
  'route.sc': 'Inyección (piel)', 'route.topical': 'En la piel', 'route.inhaled': 'Inhalada', 'route.eye': 'Ojo / oído',
  'route.rectal': 'Rectal', 'route.other': 'Otra',
  'freq.od': 'Una vez al día', 'freq.bid': 'Dos veces al día', 'freq.tid': 'Tres veces al día', 'freq.qid': 'Cuatro veces al día',
  'freq.q8h': 'Cada 8 horas', 'freq.weekly': 'Semanal', 'freq.prn': 'Solo si hace falta', 'freq.other': 'Según indicación',
  'medState.active': 'Vigente', 'medState.stopped': 'Suspendida',
  'severity.mild': 'Leve', 'severity.moderate': 'Moderada', 'severity.severe': 'Grave',
  'cond.diagnosis': 'Diagnóstico', 'cond.surgery': 'Cirugía', 'cond.history': 'Antecedente', 'cond.family': 'Antecedente familiar',
  'condStatus.active': 'Activo', 'condStatus.chronic': 'Crónico', 'condStatus.resolved': 'Resuelto',
  'incident.fall': 'Caída', 'incident.injury': 'Lesión', 'incident.medication': 'Medicación', 'incident.behaviour': 'Conducta',
  'incident.skin': 'Piel', 'incident.choking': 'Atragantamiento', 'incident.elopement': 'Desorientación', 'incident.infection': 'Enfermedad', 'incident.other': 'Otro',
  'doc.medical_report': 'Informe médico', 'doc.lab': 'Análisis', 'doc.imaging': 'Imagen', 'doc.prescription': 'Receta',
  'doc.id_document': 'Identificación', 'doc.legal': 'Legal', 'doc.insurance': 'Seguro', 'doc.billing': 'Facturación', 'doc.consent': 'Consentimiento', 'doc.other': 'Otro',
  download: 'Descargar',
  'state.active': 'En residencia', 'state.hospitalized': 'Hospitalizado/a', 'state.discharged': 'De alta', 'state.deceased': 'Fallecido/a',
  ariaIntro: 'Hola, soy ARIA. Puedo explicarte en palabras sencillas lo que hay en este expediente y pasar tus preguntas a nuestro equipo de enfermería. No puedo dar consejo médico ni cambiar tratamientos.',
  ariaPlaceholder: 'Escribe tu pregunta...',
  ariaSend: 'Enviar',
  ariaThinking: 'ARIA está escribiendo...',
  ariaError: 'ARIA no está disponible ahora. Inténtalo de nuevo o llama a la residencia.',
  ariaNoConsent: 'El asistente ARIA no está habilitado para este residente. Pídele a nuestro equipo que lo active si lo deseas.',
  ariaNotice: 'ARIA es un asistente de IA. Tus preguntas quedan registradas para que nuestro equipo pueda dar seguimiento. Para algo urgente, llama a la residencia.',
  ariaEscalated: 'Enviado a nuestro equipo de enfermería',
  signOut: 'Cerrar sesión',
};

const DICT: Record<FamilyLang, Record<Key, string>> = { en, es };

export type TKey = Key;

function initialLang(): FamilyLang {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'en' || saved === 'es') return saved;
  } catch {
    // storage blocked - fall through
  }
  return navigator.language?.toLowerCase().startsWith('es') ? 'es' : 'en';
}

export function useFamilyLang() {
  const [lang, setLangState] = useState<FamilyLang>(initialLang);

  useEffect(() => {
    const previous = document.documentElement.lang;
    document.documentElement.lang = lang;
    return () => {
      document.documentElement.lang = previous;
    };
  }, [lang]);

  const setLang = useCallback((next: FamilyLang) => {
    setLangState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // ignore
    }
  }, []);

  // Falls back to the key itself so a missing translation is visible, not blank.
  const t = useCallback((key: string): string => (DICT[lang] as Record<string, string>)[key] ?? key, [lang]);

  return { lang, setLang, t };
}
