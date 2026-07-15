import { MapPin } from 'lucide-react';

export function DestinationCard({ destination, size = 'default' }) {
  return (
    <div className={`group relative overflow-hidden rounded-xl cursor-pointer ${size === 'large' ? 'h-72 md:h-96' : 'h-48 md:h-60'}`}>
      <img
        src={destination.image}
        alt={destination.name}
        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
        loading="lazy"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-charcoal/80 via-charcoal/20 to-transparent" />
      <div className="absolute bottom-0 left-0 right-0 p-5">
        <div className="flex items-center gap-1.5 mb-1">
          <MapPin className="w-3.5 h-3.5 text-saffron" />
          <span className="text-xs text-white/70 font-medium">
            {destination.spots} {destination.spots === 1 ? 'spot' : 'spots'}
          </span>
        </div>
        <h3 className="font-display text-lg font-semibold text-white mb-1">
          {destination.name}
        </h3>
        <p className="text-sm text-white/70 line-clamp-2">
          {destination.description}
        </p>
      </div>
    </div>
  );
}
