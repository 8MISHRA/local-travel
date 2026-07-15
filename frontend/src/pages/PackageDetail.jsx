import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Star, Clock, MapPin, Users, Check, X, ArrowLeft, Calendar } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '../components/ui/Accordion';
import { PageTransition } from '../components/layout/PageTransition';
import { packages } from '../data/mockData';

export default function PackageDetail() {
  const { id } = useParams();
  const pkg = packages.find((p) => p.id === parseInt(id));

  if (!pkg) {
    return (
      <PageTransition>
        <div className="pt-24 pb-20 text-center container-custom">
          <h1 className="font-display text-3xl font-bold mb-4">Package Not Found</h1>
          <p className="text-charcoal/60 mb-6">The package you're looking for doesn't exist.</p>
          <Link to="/packages"><Button>Back to Packages</Button></Link>
        </div>
      </PageTransition>
    );
  }

  const discount = Math.round(((pkg.originalPrice - pkg.price) / pkg.originalPrice) * 100);

  return (
    <PageTransition>
      {/* Hero */}
      <section className="relative h-[50vh] md:h-[60vh]">
        <img
          src={pkg.image}
          alt={pkg.title}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-charcoal/70 via-charcoal/20 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 p-8">
          <div className="container-custom">
            <Link to="/packages" className="inline-flex items-center gap-1 text-white/70 hover:text-white text-sm mb-4 transition-colors">
              <ArrowLeft className="w-4 h-4" /> Back to Packages
            </Link>
            <div className="flex flex-wrap items-center gap-3 mb-3">
              <Badge className="bg-saffron text-white">{discount}% OFF</Badge>
              <Badge className="bg-white/20 text-white backdrop-blur-sm">
                <Clock className="w-3 h-3 mr-1" />
                {pkg.duration}
              </Badge>
              <Badge className="bg-white/20 text-white backdrop-blur-sm">
                <MapPin className="w-3 h-3 mr-1" />
                {pkg.destination}
              </Badge>
            </div>
            <h1 className="font-display text-3xl md:text-5xl font-bold text-white mb-3">
              {pkg.title}
            </h1>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <Star className="w-5 h-5 fill-gold text-gold" />
                <span className="text-white font-semibold">{pkg.rating}</span>
                <span className="text-white/60 text-sm">({pkg.reviews} reviews)</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="py-12 bg-cream">
        <div className="container-custom">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-8">
              {/* Description */}
              <motion.div
                className="bg-white rounded-xl p-6 shadow-sm"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <h2 className="font-display text-xl font-semibold mb-3">About This Package</h2>
                <p className="text-charcoal/70 leading-relaxed">{pkg.description}</p>
              </motion.div>

              {/* Itinerary */}
              <motion.div
                className="bg-white rounded-xl p-6 shadow-sm"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <h2 className="font-display text-xl font-semibold mb-4">Day-wise Itinerary</h2>
                <Accordion type="single" collapsible defaultValue="day-1">
                  {pkg.itinerary.map((day) => (
                    <AccordionItem key={day.day} value={`day-${day.day}`}>
                      <AccordionTrigger className="text-left">
                        <div className="flex items-center gap-3">
                          <span className="w-8 h-8 rounded-full bg-saffron/10 flex items-center justify-center text-saffron text-sm font-bold shrink-0">
                            {day.day}
                          </span>
                          <div>
                            <span className="font-semibold">{day.title}</span>
                            <span className="text-xs text-charcoal/40 ml-2">Day {day.day}</span>
                          </div>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <ul className="ml-11 space-y-2">
                          {day.activities.map((activity, i) => (
                            <li key={i} className="flex items-start gap-2 text-charcoal/70">
                              <div className="w-1.5 h-1.5 rounded-full bg-saffron shrink-0 mt-2" />
                              {activity}
                            </li>
                          ))}
                        </ul>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </motion.div>

              {/* Inclusions / Exclusions */}
              <motion.div
                className="grid grid-cols-1 md:grid-cols-2 gap-6"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="bg-white rounded-xl p-6 shadow-sm">
                  <h3 className="font-display font-semibold text-lg mb-4 text-green-700 flex items-center gap-2">
                    <Check className="w-5 h-5" /> Inclusions
                  </h3>
                  <ul className="space-y-2.5">
                    {pkg.inclusions.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-charcoal/70">
                        <Check className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="bg-white rounded-xl p-6 shadow-sm">
                  <h3 className="font-display font-semibold text-lg mb-4 text-red-600 flex items-center gap-2">
                    <X className="w-5 h-5" /> Exclusions
                  </h3>
                  <ul className="space-y-2.5">
                    {pkg.exclusions.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-charcoal/70">
                        <X className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </motion.div>
            </div>

            {/* Pricing Sidebar */}
            <div className="space-y-6">
              {/* Price Card */}
              <motion.div
                className="bg-white rounded-xl p-6 shadow-sm border-2 border-saffron/20 sticky top-24"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
              >
                <div className="mb-4">
                  <span className="text-sm text-charcoal/40 line-through">₹{pkg.originalPrice.toLocaleString()}</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-charcoal">₹{pkg.price.toLocaleString()}</span>
                    <span className="text-sm text-charcoal/50">/person</span>
                  </div>
                  <Badge variant="success" className="mt-1">Save ₹{(pkg.originalPrice - pkg.price).toLocaleString()}</Badge>
                </div>

                <h3 className="font-display font-semibold mb-3">Choose Your Tier</h3>
                <div className="space-y-3 mb-6">
                  {pkg.tiers.map((tier, i) => (
                    <div
                      key={tier.name}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${i === 0 ? 'border-saffron bg-saffron/5' : 'border-charcoal/10 hover:border-saffron/50'}`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-sm">{tier.name}</span>
                        <span className="text-sm font-bold">₹{tier.price.toLocaleString()}</span>
                      </div>
                      <p className="text-xs text-charcoal/50">{tier.hotel} • {tier.transport}</p>
                    </div>
                  ))}
                </div>

                <Link to={`/book/${pkg.id}`} className="block">
                  <Button size="lg" className="w-full gap-2">
                    <Calendar className="w-4 h-4" />
                    Book Now
                  </Button>
                </Link>
                <p className="text-xs text-charcoal/40 text-center mt-3">No payment required until confirmation</p>
              </motion.div>
            </div>
          </div>
        </div>
      </section>
    </PageTransition>
  );
}
