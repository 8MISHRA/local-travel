import { motion } from 'framer-motion';
import { MapPin, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { DestinationCard } from '../components/shared/DestinationCard';
import { PageTransition } from '../components/layout/PageTransition';
import { destinations } from '../data/mockData';

export default function Destinations() {
  return (
    <PageTransition>
      {/* Header */}
      <section className="pt-24 pb-12 bg-gradient-to-b from-river/5 to-cream">
        <div className="container-custom text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h1 className="font-display text-3xl md:text-5xl font-bold text-charcoal mb-3">
              Our Destinations
            </h1>
            <p className="text-charcoal/60 max-w-lg mx-auto">
              Explore the timeless beauty of Varanasi and the hidden wonders of Mirzapur
            </p>
          </motion.div>
        </div>
      </section>

      {/* Destinations */}
      <section className="py-12 bg-cream">
        <div className="container-custom space-y-20">
          {destinations.map((dest, destIndex) => (
            <motion.div
              key={dest.id}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              {/* Destination Header */}
              <div className="relative rounded-2xl overflow-hidden h-64 md:h-80 mb-8">
                <img
                  src={dest.image}
                  alt={dest.name}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-r from-charcoal/70 via-charcoal/30 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-8">
                  <div className="flex items-center gap-2 mb-2">
                    <MapPin className="w-5 h-5 text-saffron" />
                    <span className="text-sm text-white/70">Uttar Pradesh, India</span>
                  </div>
                  <h2 className="font-display text-3xl md:text-4xl font-bold text-white mb-2">
                    {dest.name}
                  </h2>
                  <p className="text-white/70 text-lg">{dest.tagline}</p>
                  <p className="text-white/50 text-sm mt-2 max-w-xl">{dest.description}</p>
                </div>
              </div>

              {/* Sub-Destinations Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {dest.subDestinations.map((sub, i) => (
                  <motion.div
                    key={sub.id}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.08 }}
                  >
                    <DestinationCard destination={sub} />
                  </motion.div>
                ))}
              </div>

              {/* CTA */}
              <div className="text-center mt-8">
                <Link to="/packages">
                  <Button variant="outline" className="gap-2">
                    Explore {dest.name} Packages <ArrowRight className="w-4 h-4" />
                  </Button>
                </Link>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="py-16 bg-white">
        <div className="container-custom text-center">
          <h2 className="font-display text-2xl md:text-3xl font-bold text-charcoal mb-3">
            Can't Decide? Let Us Help!
          </h2>
          <p className="text-charcoal/60 max-w-md mx-auto mb-6">
            Tell us your preferences and we'll craft a personalized itinerary just for you.
          </p>
          <Link to="/support">
            <Button size="lg" className="gap-2">
              Get Custom Itinerary <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </section>
    </PageTransition>
  );
}
