import { useEffect } from 'react';
import { fetchAiWidgetConfig } from '../lib/odoo';

// Loads the AI Customer Agent chat widget (odoo/addons/ai_customer_agent) on
// top of the site. That module normally injects itself into Odoo's own
// website.layout template, but this site's public pages are served by this
// React app instead (see infra/nginx/default.conf), so Odoo's template
// inheritance never runs. This component is the bridge: it asks Odoo whether
// the widget should show (Settings -> AI Customer Agent controls this) and,
// if so, loads the same static script Odoo would have injected.
const WIDGET_SCRIPT_SRC = '/ai_customer_agent/static/src/js/ai_agent_widget.js';
const WIDGET_SCRIPT_ID = 'ai-customer-agent-widget-script';

// The widget's own launcher sits at bottom:24px/right:24px, which is exactly
// where WhatsAppButton lives. Stack it above instead of overlapping.
const STACK_OFFSET_STYLE_ID = 'ai-customer-agent-widget-stack-offset';
const STACK_OFFSET_CSS = '.aiw-root { bottom: 100px !important; }';

export default function AiChatWidget() {
  useEffect(() => {
    let cancelled = false;

    fetchAiWidgetConfig()
      .then((config) => {
        if (cancelled || !config.enabled) return;
        if (document.getElementById(WIDGET_SCRIPT_ID)) return;

        if (!document.getElementById(STACK_OFFSET_STYLE_ID)) {
          const style = document.createElement('style');
          style.id = STACK_OFFSET_STYLE_ID;
          style.textContent = STACK_OFFSET_CSS;
          document.head.appendChild(style);
        }

        const script = document.createElement('script');
        script.id = WIDGET_SCRIPT_ID;
        script.src = WIDGET_SCRIPT_SRC;
        script.dataset.endpoint = '/ai_agent/chat';
        script.dataset.lang = config.language;
        if (config.store_name) script.dataset.storeName = config.store_name;
        script.dataset.primaryColor = config.primary_color;
        script.dataset.accentColor = config.accent_color;
        if (config.welcome_message) script.dataset.welcome = config.welcome_message;
        document.body.appendChild(script);
      })
      .catch(() => {
        // Odoo briefly unreachable or widget not configured yet - fail silent,
        // same policy as WhatsAppButton's settings fetch.
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return null;
}
