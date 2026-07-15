import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Star, Shield, Clock, Heart, MapPin, Users } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { PackageCard } from '../components/shared/PackageCard';
import { TestimonialCard } from '../components/shared/TestimonialCard';
import { PageTransition } from '../components/layout/PageTransition';
import { packages, destinations, testimonials } from '../data/mockData';

const fadeInUp = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6 },
};

const stagger = {
  animate: {
    transition: { staggerChildren: 0.1 },
  },
};

export default function Home() {
  const featuredPackages = packages.filter((p) => p.featured);

  return (
    <PageTransition>
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1561361513-2d000a50f0dc?w=1600&q=80"
            alt="Varanasi Ghats at sunrise"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-charcoal/70 via-charcoal/40 to-transparent" />
        </div>
        <div className="container-custom relative z-10 py-20">
          <motion.div
            className="max-w-2xl"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
              className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md px-4 py-2 rounded-full text-white/90 text-sm mb-6"
            >
              <MapPin className="w-4 h-4 text-saffron" />
              Varanasi & Mirzapur, India
            </motion.div>
            <h1 className="font-display text-4xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight">
              Experience the Soul of
              <span className="text-gradient block"> Ancient Bharat</span>
            </h1>
            <p className="text-lg md:text-xl text-white/80 mb-8 leading-relaxed">
              Just reach Varanasi or Mirzapur. We take care of everything else.
              Curated experiences, local guides, premium stays.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/packages">
                <Button size="xl" className="gap-2 w-full sm:w-auto">
                  Explore Packages <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
              <Link to="/destinations">
                <Button variant="outline" size="xl" className="border-white text-white hover:bg-white hover:text-charcoal w-full sm:w-auto">
                  View Destinations
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>

        {/* Stats bar */}
        <motion.div
          className="absolute bottom-0 left-0 right-0 bg-white/10 backdrop-blur-md border-t border-white/10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1, duration: 0.6 }}
        >
          <div className="container-custom py-4 flex items-center justify-between overflow-x-auto gap-8 scrollbar-hide">
            {[
              { label: 'Happy Travellers', value: '2500+' },
              { label: 'Curated Packages', value: '25+' },
              { label: 'Destinations', value: '50+' },
              { label: 'Avg. Rating', value: '4.8★' },
            ].map((stat) => (
              <div key={stat.label} className="text-center shrink-0">
                <p className="text-lg md:text-xl font-bold text-white">{stat.value}</p>
                <p className="text-xs text-white/60">{stat.label}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="py-16 bg-white">
        <div className="container-custom">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { icon: Shield, title: 'Safe & Trusted', desc: 'Verified local guides & services' },
              { icon: Clock, title: 'Hassle-Free', desc: 'Everything planned for you' },
              { icon: Heart, title: 'Curated with Love', desc: 'Handpicked experiences only' },
              { icon: Users, title: 'Local Experts', desc: 'Born & raised in the region' },
            ].map((feature) => (
              <motion.div
                key={feature.title}
                className="text-center p-4"
                {...fadeInUp}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
              >
                <div className="w-12 h-12 rounded-xl bg-saffron/10 flex items-center justify-center mx-auto mb-3">
                  <feature.icon className="w-6 h-6 text-saffron" />
                </div>
                <h4 className="font-semibold text-sm mb-1">{feature.title}</h4>
                <p className="text-xs text-charcoal/50">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Packages */}
      <section className="py-20 bg-cream">
        <div className="container-custom">
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-display text-3xl md:text-4xl font-bold text-charcoal mb-3">
              Featured Packages
            </h2>
            <p className="text-charcoal/60 max-w-lg mx-auto">
              Our most loved travel experiences, handpicked for unforgettable memories
            </p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {featuredPackages.map((pkg, i) => (
              <motion.div
                key={pkg.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <PackageCard pkg={pkg} />
              </motion.div>
            ))}
          </div>
          <div className="text-center mt-10">
            <Link to="/packages">
              <Button variant="outline" size="lg" className="gap-2">
                View All Packages <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Destination Highlights */}
      <section className="py-20 bg-white">
        <div className="container-custom">
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-display text-3xl md:text-4xl font-bold text-charcoal mb-3">
              Our Destinations
            </h2>
            <p className="text-charcoal/60 max-w-lg mx-auto">
              Two incredible cities, infinite experiences
            </p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {destinations.map((dest, i) => (
              <motion.div
                key={dest.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
              >
                <Link to="/destinations" className="group block relative h-72 md:h-80 rounded-2xl overflow-hidden">
                  <img
                    src={dest.image}
                    alt={dest.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-charcoal/80 via-charcoal/20 to-transparent" />
                  <div className="absolute bottom-0 left-0 right-0 p-8">
                    <h3 className="font-display text-2xl md:text-3xl font-bold text-white mb-2">
                      {dest.name}
                    </h3>
                    <p className="text-white/70 text-sm mb-1">{dest.tagline}</p>
                    <p className="text-white/50 text-xs">{dest.subDestinations.length} experiences</p>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 bg-cream">
        <div className="container-custom">
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-display text-3xl md:text-4xl font-bold text-charcoal mb-3">
              What Travellers Say
            </h2>
            <p className="text-charcoal/60 max-w-lg mx-auto">
              Real stories from real travellers who chose YatraFlow
            </p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {testimonials.slice(0, 3).map((t, i) => (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
              >
                <TestimonialCard testimonial={t} />
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 gradient-river relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-40 h-40 rounded-full bg-saffron blur-3xl" />
          <div className="absolute bottom-10 right-10 w-60 h-60 rounded-full bg-gold blur-3xl" />
        </div>
        <div className="container-custom relative z-10 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="font-display text-3xl md:text-5xl font-bold text-white mb-4">
              Ready for Your Next Adventure?
            </h2>
            <p className="text-white/70 max-w-md mx-auto mb-8 text-lg">
              Let us craft the perfect journey for you. No hassle, just memories.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/packages">
                <Button size="xl" variant="gold" className="gap-2 w-full sm:w-auto">
                  Browse Packages <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
              <Link to="/support">
                <Button size="xl" variant="outline" className="border-white/30 text-white hover:bg-white/10 w-full sm:w-auto">
                  Talk to Us
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </PageTransition>
  );
}
