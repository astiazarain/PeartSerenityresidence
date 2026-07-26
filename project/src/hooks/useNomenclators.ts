import { useEffect, useState } from 'react';
import { fetchNomenclators, type NomenclatorOption } from '../lib/odoo';

/** Active Care Type / Urgency Level options, sourced from Odoo. */
export function useNomenclators() {
  const [careTypes, setCareTypes] = useState<NomenclatorOption[]>([]);
  const [urgencyLevels, setUrgencyLevels] = useState<NomenclatorOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchNomenclators()
      .then(({ care_types, urgency_levels }) => {
        if (cancelled) return;
        setCareTypes(care_types);
        setUrgencyLevels(urgency_levels);
      })
      .catch(() => {
        if (!cancelled) setError('Failed to load form options. Please refresh the page.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { careTypes, urgencyLevels, loading, error };
}
