import { Star, Quote } from 'lucide-react';

export function TestimonialCard({ testimonial }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-charcoal/5 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4 mb-4">
        <div className="w-11 h-11 rounded-full gradient-saffron flex items-center justify-center text-white font-semibold text-sm shrink-0">
          {testimonial.avatar}
        </div>
        <div>
          <h4 className="font-semibold text-charcoal">{testimonial.name}</h4>
          <p className="text-xs text-charcoal/50">{testimonial.location}</p>
        </div>
        <Quote className="w-6 h-6 text-saffron/20 ml-auto shrink-0" />
      </div>
      <div className="flex items-center gap-0.5 mb-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Star
            key={i}
            className={`w-3.5 h-3.5 ${i < testimonial.rating ? 'fill-gold text-gold' : 'text-charcoal/20'}`}
          />
        ))}
      </div>
      <p className="text-sm text-charcoal/70 leading-relaxed mb-3">
        "{testimonial.text}"
      </p>
      <p className="text-xs text-saffron font-medium">{testimonial.package}</p>
    </div>
  );
}
