import { useState, useEffect } from 'react';
import { MessageCircle, X } from 'lucide-react';

const PHONE = '18765550192';
const MESSAGE = "Hello! I'm interested in learning more about Peart Serenity Residence.";

export default function WhatsAppButton() {
  const [showTooltip, setShowTooltip] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 2000);
    const tooltipTimer = setTimeout(() => setShowTooltip(true), 4000);
    const hideTimer = setTimeout(() => setShowTooltip(false), 12000);
    return () => {
      clearTimeout(timer);
      clearTimeout(tooltipTimer);
      clearTimeout(hideTimer);
    };
  }, []);

  const link = `https://wa.me/${PHONE}?text=${encodeURIComponent(MESSAGE)}`;

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 flex items-end gap-3 transition-all duration-500 ${
        visible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'
      }`}
    >
      {/* TOOLTIP */}
      {showTooltip && (
        <div className="relative bg-white rounded-2xl shadow-2xl p-4 max-w-[240px] animate-fade-in hidden sm:block">
          <button
            onClick={() => setShowTooltip(false)}
            className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-brand-charcoal text-white flex items-center justify-center hover:bg-brand-black transition-colors"
          >
            <X className="h-3 w-3" />
          </button>
          <p className="text-sm font-semibold text-brand-black mb-1">Chat with us!</p>
          <p className="text-xs text-brand-textgrey leading-relaxed">
            Have questions about our services? Send us a WhatsApp message and we'll respond shortly.
          </p>
          <div className="absolute -bottom-2 right-8 w-4 h-4 bg-white rotate-45" />
        </div>
      )}

      {/* BUTTON */}
      <a
        href={link}
        target="_blank"
        rel="noopener noreferrer"
        className="relative w-14 h-14 md:w-16 md:h-16 rounded-full bg-[#25D366] flex items-center justify-center shadow-2xl hover:scale-110 transition-transform duration-300 group"
        aria-label="Chat on WhatsApp"
        onMouseEnter={() => setShowTooltip(true)}
      >
        {/* PULSE RING */}
        <span className="absolute inset-0 rounded-full bg-[#25D366] animate-ping opacity-20" />
        <MessageCircle className="h-7 w-7 md:h-8 md:w-8 text-white relative z-10" fill="currentColor" />
        {/* ONLINE BADGE */}
        <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-green-500 border-2 border-white" />
      </a>
    </div>
  );
}
