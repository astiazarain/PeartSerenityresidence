import { Sun, Clock, Home as HomeIcon, Sparkles, Activity, Stethoscope, Heart, type LucideIcon } from 'lucide-react';
import type { Service } from './odoo';

/** Best-effort icon per service, matched by keywords in the product name.
 * Odoo products have no icon field, so this is purely cosmetic — an
 * unmatched name (e.g. a brand-new product) just falls back to Heart. */
const ICON_RULES: Array<{ keywords: string[]; icon: LucideIcon }> = [
  { keywords: ['day care', 'daycare'], icon: Sun },
  { keywords: ['respite'], icon: Clock },
  { keywords: ['residential', 'residence'], icon: HomeIcon },
  { keywords: ['suite'], icon: Sparkles },
  { keywords: ['recovery', 'surgical'], icon: Activity },
  { keywords: ['specialized'], icon: Stethoscope },
];

export function getServiceIcon(name: string): LucideIcon {
  const lower = name.toLowerCase();
  const match = ICON_RULES.find((rule) => rule.keywords.some((keyword) => lower.includes(keyword)));
  return match ? match.icon : Heart;
}

const PERIOD_SUFFIX: Record<Exclude<Service['price_period'], 'custom'>, string> = {
  day: '/day',
  week: '/week',
  month: '/month',
};

/** Formats a service's price for display: "Custom" for price_period='custom',
 * otherwise a "$1,234" + period suffix pair. */
export function formatServicePrice(service: Pick<Service, 'list_price' | 'price_period'>): {
  price: string;
  period: string;
} {
  if (service.price_period === 'custom') {
    return { price: 'Custom', period: '' };
  }
  const price = `$${service.list_price.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  return { price, period: PERIOD_SUFFIX[service.price_period] };
}
