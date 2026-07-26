import { useEffect, useState } from 'react';
import { fetchServices, type Service } from '../lib/odoo';

/** Published, sellable service products, sourced from Odoo. */
export function useServices() {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchServices()
      .then((records) => {
        if (cancelled) return;
        setServices(records);
      })
      .catch(() => {
        if (!cancelled) setError('Failed to load services. Please refresh the page.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { services, loading, error };
}
