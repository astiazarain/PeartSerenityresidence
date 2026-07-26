import { useEffect, useState } from 'react';
import { Image as ImageIcon } from 'lucide-react';
import { fetchGallery, type GalleryPhoto } from '../lib/odoo';

const CATEGORIES: { id: GalleryPhoto['category'] | 'all'; label: string }[] = [
  { id: 'all', label: 'All Photos' },
  { id: 'facility', label: 'Facility' },
  { id: 'activities', label: 'Activities' },
  { id: 'events', label: 'Events' },
];

export default function Gallery() {
  const [photos, setPhotos] = useState<GalleryPhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState<(typeof CATEGORIES)[number]['id']>('all');

  useEffect(() => {
    setLoading(true);
    fetchGallery(category === 'all' ? undefined : category)
      .then(setPhotos)
      .catch(() => setPhotos([]))
      .finally(() => setLoading(false));
  }, [category]);

  return (
    <div>
      {/* HEADER */}
      <section className="relative pt-40 pb-20 bg-brand-black overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-gold-500 rounded-full blur-3xl translate-x-1/2 translate-y-1/2"></div>
        </div>
        <div className="container-max px-6 md:px-12 lg:px-20 relative z-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-gold-400 mb-4">Life at Peart Serenity</p>
          <h1 className="font-serif text-5xl md:text-6xl text-white mb-6">Gallery</h1>
          <p className="text-lg text-brand-cream/80 max-w-2xl mx-auto leading-relaxed">
            A glimpse into our facility, our residents' activities, and the moments that make our
            community feel like home.
          </p>
        </div>
      </section>

      {/* GALLERY */}
      <section className="section-padding bg-white">
        <div className="container-max">
          <div className="flex flex-col sm:flex-row justify-center gap-3 mb-12">
            {CATEGORIES.map((c) => (
              <button
                key={c.id}
                onClick={() => setCategory(c.id)}
                className={`px-6 py-3 rounded-full font-semibold text-sm uppercase tracking-wider transition-all duration-300 ${
                  category === c.id ? 'bg-gold-500 text-brand-black shadow-lg' : 'bg-brand-cream text-brand-textgrey hover:bg-gold-50'
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>

          {loading && <p className="text-center text-brand-textgrey">Loading photos...</p>}

          {!loading && photos.length === 0 && (
            <div className="text-center text-brand-textgrey py-16">
              <ImageIcon className="h-12 w-12 mx-auto mb-4 text-brand-softgrey" />
              <p>No photos in this category yet — check back soon.</p>
            </div>
          )}

          {!loading && photos.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {photos.map((photo, i) => (
                <div
                  key={photo.id}
                  className="group relative rounded-2xl overflow-hidden shadow-lg animate-slide-up"
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  {photo.image && (
                    <img
                      src={`data:image/png;base64,${photo.image}`}
                      alt={photo.title}
                      className="w-full h-64 object-cover group-hover:scale-110 transition-transform duration-500"
                    />
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/0 to-black/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-5">
                    <p className="text-white font-serif text-lg">{photo.title}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
