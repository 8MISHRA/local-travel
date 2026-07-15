import { Link } from 'react-router-dom';
import { Star, Clock, MapPin, Users } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export function PackageCard({ pkg }) {
  const discount = Math.round(((pkg.originalPrice - pkg.price) / pkg.originalPrice) * 100);

  return (
    <div className="group bg-white rounded-xl overflow-hidden shadow-sm border border-charcoal/5 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
      {/* Image */}
      <div className="relative h-48 overflow-hidden">
        <img
          src={pkg.image}
          alt={pkg.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
        <div className="absolute top-3 left-3 flex gap-2">
          <Badge variant="default" className="bg-saffron text-white">
            {discount}% OFF
          </Badge>
          {pkg.featured && (
            <Badge variant="gold" className="bg-gold text-charcoal">
              Featured
            </Badge>
          )}
        </div>
        <div className="absolute bottom-3 right-3">
          <Badge variant="secondary" className="bg-white/90 text-charcoal backdrop-blur-sm">
            <Clock className="w-3 h-3 mr-1" />
            {pkg.duration}
          </Badge>
        </div>
      </div>

      {/* Content */}
      <div className="p-5">
        <div className="flex items-center gap-2 mb-2">
          <MapPin className="w-3.5 h-3.5 text-saffron" />
          <span className="text-xs font-medium text-saffron">{pkg.destination}</span>
        </div>
        <h3 className="font-display text-lg font-semibold text-charcoal mb-2 line-clamp-1 group-hover:text-saffron transition-colors">
          {pkg.title}
        </h3>
        <p className="text-sm text-charcoal/60 mb-4 line-clamp-2">
          {pkg.description}
        </p>

        {/* Rating */}
        <div className="flex items-center gap-2 mb-4">
          <div className="flex items-center gap-1">
            <Star className="w-4 h-4 fill-gold text-gold" />
            <span className="text-sm font-semibold">{pkg.rating}</span>
          </div>
          <span className="text-xs text-charcoal/40">({pkg.reviews} reviews)</span>
        </div>

        {/* Price & CTA */}
        <div className="flex items-center justify-between pt-3 border-t border-charcoal/5">
          <div>
            <span className="text-xs text-charcoal/40 line-through">₹{pkg.originalPrice.toLocaleString()}</span>
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-bold text-charcoal">₹{pkg.price.toLocaleString()}</span>
              <span className="text-xs text-charcoal/50">/person</span>
            </div>
          </div>
          <Link to={`/packages/${pkg.id}`}>
            <Button size="sm">View Details</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
