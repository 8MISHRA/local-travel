import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Users, Hotel, Car, CreditCard, Check, ArrowLeft, ArrowRight, MapPin } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { PageTransition } from '../components/layout/PageTransition';
import { packages } from '../data/mockData';

const steps = [
  { id: 1, title: 'Dates & Travellers', icon: Calendar },
  { id: 2, title: 'Hotel & Transport', icon: Hotel },
  { id: 3, title: 'Review & Pay', icon: CreditCard },
];

export default function BookingFlow() {
  const { packageId } = useParams();
  const pkg = packages.find((p) => p.id === parseInt(packageId));
  const [currentStep, setCurrentStep] = useState(1);
  const [bookingData, setBookingData] = useState({
    startDate: '',
    travellers: 2,
    tier: 0,
    specialRequests: '',
  });

  if (!pkg) {
    return (
      <PageTransition>
        <div className="pt-24 pb-20 text-center container-custom">
          <h1 className="font-display text-3xl font-bold mb-4">Package Not Found</h1>
          <Link to="/packages"><Button>Back to Packages</Button></Link>
        </div>
      </PageTransition>
    );
  }

  const selectedTier = pkg.tiers[bookingData.tier];
  const totalPrice = selectedTier.price * bookingData.travellers;

  const nextStep = () => setCurrentStep((prev) => Math.min(prev + 1, 3));
  const prevStep = () => setCurrentStep((prev) => Math.max(prev - 1, 1));

  return (
    <PageTransition>
      <section className="pt-24 pb-8 bg-gradient-to-b from-river/5 to-cream">
        <div className="container-custom">
          <Link to={`/packages/${pkg.id}`} className="inline-flex items-center gap-1 text-charcoal/60 hover:text-saffron text-sm mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to {pkg.title}
          </Link>
          <h1 className="font-display text-2xl md:text-3xl font-bold text-charcoal mb-2">
            Book: {pkg.title}
          </h1>
          <div className="flex items-center gap-2 text-sm text-charcoal/60">
            <MapPin className="w-4 h-4 text-saffron" /> {pkg.destination} • {pkg.duration}
          </div>
        </div>
      </section>

      <section className="py-8 bg-cream">
        <div className="container-custom">
          {/* Step Indicator */}
          <div className="flex items-center justify-center mb-10">
            {steps.map((step, i) => (
              <div key={step.id} className="flex items-center">
                <div className={`flex items-center gap-2 ${currentStep >= step.id ? 'text-saffron' : 'text-charcoal/30'}`}>
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                    currentStep > step.id ? 'bg-saffron text-white' :
                    currentStep === step.id ? 'bg-saffron/10 border-2 border-saffron text-saffron' :
                    'bg-charcoal/5 text-charcoal/30'
                  }`}>
                    {currentStep > step.id ? <Check className="w-4 h-4" /> : step.id}
                  </div>
                  <span className="hidden sm:block text-sm font-medium">{step.title}</span>
                </div>
                {i < steps.length - 1 && (
                  <div className={`w-12 sm:w-20 h-0.5 mx-2 sm:mx-4 ${currentStep > step.id ? 'bg-saffron' : 'bg-charcoal/10'}`} />
                )}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Form Area */}
            <div className="lg:col-span-2">
              <AnimatePresence mode="wait">
                {currentStep === 1 && (
                  <motion.div
                    key="step1"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="bg-white rounded-xl p-6 shadow-sm"
                  >
                    <h2 className="font-display text-xl font-semibold mb-6 flex items-center gap-2">
                      <Calendar className="w-5 h-5 text-saffron" />
                      Select Dates & Travellers
                    </h2>
                    <div className="space-y-5">
                      <div>
                        <label htmlFor="start-date" className="text-sm font-medium text-charcoal/70 block mb-1.5">
                          Travel Start Date
                        </label>
                        <Input
                          id="start-date"
                          type="date"
                          value={bookingData.startDate}
                          onChange={(e) => setBookingData({ ...bookingData, startDate: e.target.value })}
                          min={new Date().toISOString().split('T')[0]}
                        />
                      </div>
                      <div>
                        <label htmlFor="travellers" className="text-sm font-medium text-charcoal/70 block mb-1.5">
                          Number of Travellers
                        </label>
                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() => setBookingData({ ...bookingData, travellers: Math.max(1, bookingData.travellers - 1) })}
                            className="w-10 h-10 rounded-lg border border-charcoal/20 flex items-center justify-center hover:border-saffron hover:text-saffron transition-colors"
                            aria-label="Decrease travellers"
                          >
                            -
                          </button>
                          <span className="text-xl font-bold w-12 text-center">{bookingData.travellers}</span>
                          <button
                            type="button"
                            onClick={() => setBookingData({ ...bookingData, travellers: Math.min(10, bookingData.travellers + 1) })}
                            className="w-10 h-10 rounded-lg border border-charcoal/20 flex items-center justify-center hover:border-saffron hover:text-saffron transition-colors"
                            aria-label="Increase travellers"
                          >
                            +
                          </button>
                        </div>
                      </div>
                      <div>
                        <label htmlFor="special-requests" className="text-sm font-medium text-charcoal/70 block mb-1.5">
                          Special Requests (Optional)
                        </label>
                        <textarea
                          id="special-requests"
                          className="flex min-h-[80px] w-full rounded-lg border border-charcoal/20 bg-white px-3 py-2 text-sm placeholder:text-charcoal/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-saffron/50"
                          placeholder="Any dietary needs, accessibility requirements, or special preferences..."
                          value={bookingData.specialRequests}
                          onChange={(e) => setBookingData({ ...bookingData, specialRequests: e.target.value })}
                        />
                      </div>
                    </div>
                  </motion.div>
                )}

                {currentStep === 2 && (
                  <motion.div
                    key="step2"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="bg-white rounded-xl p-6 shadow-sm"
                  >
                    <h2 className="font-display text-xl font-semibold mb-6 flex items-center gap-2">
                      <Hotel className="w-5 h-5 text-saffron" />
                      Choose Hotel & Transport
                    </h2>
                    <div className="space-y-4">
                      {pkg.tiers.map((tier, i) => (
                        <div
                          key={tier.name}
                          onClick={() => setBookingData({ ...bookingData, tier: i })}
                          className={`p-5 rounded-xl border-2 cursor-pointer transition-all ${
                            bookingData.tier === i
                              ? 'border-saffron bg-saffron/5 shadow-sm'
                              : 'border-charcoal/10 hover:border-saffron/30'
                          }`}
                          role="radio"
                          aria-checked={bookingData.tier === i}
                          tabIndex={0}
                          onKeyDown={(e) => e.key === 'Enter' && setBookingData({ ...bookingData, tier: i })}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                                bookingData.tier === i ? 'border-saffron' : 'border-charcoal/20'
                              }`}>
                                {bookingData.tier === i && <div className="w-2.5 h-2.5 rounded-full bg-saffron" />}
                              </div>
                              <h3 className="font-semibold text-lg">{tier.name}</h3>
                              {i === 1 && <Badge variant="gold">Popular</Badge>}
                            </div>
                            <span className="text-xl font-bold text-charcoal">₹{tier.price.toLocaleString()}<span className="text-sm font-normal text-charcoal/50">/person</span></span>
                          </div>
                          <div className="ml-8 flex flex-wrap gap-4 text-sm text-charcoal/60">
                            <span className="flex items-center gap-1"><Hotel className="w-3.5 h-3.5" /> {tier.hotel}</span>
                            <span className="flex items-center gap-1"><Car className="w-3.5 h-3.5" /> {tier.transport}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {currentStep === 3 && (
                  <motion.div
                    key="step3"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="bg-white rounded-xl p-6 shadow-sm"
                  >
                    <h2 className="font-display text-xl font-semibold mb-6 flex items-center gap-2">
                      <CreditCard className="w-5 h-5 text-saffron" />
                      Review & Payment
                    </h2>
                    <div className="space-y-4">
                      <div className="bg-cream rounded-lg p-4 space-y-3">
                        <div className="flex justify-between text-sm">
                          <span className="text-charcoal/60">Package</span>
                          <span className="font-medium">{pkg.title}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-charcoal/60">Destination</span>
                          <span className="font-medium">{pkg.destination}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-charcoal/60">Duration</span>
                          <span className="font-medium">{pkg.duration}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-charcoal/60">Start Date</span>
                          <span className="font-medium">{bookingData.startDate || 'Not selected'}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-charcoal/60">Travellers</span>
                          <span className="font-medium">{bookingData.travellers}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-charcoal/60">Tier</span>
                          <span className="font-medium">{selectedTier.name}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-charcoal/60">Hotel</span>
                          <span className="font-medium">{selectedTier.hotel}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-charcoal/60">Transport</span>
                          <span className="font-medium">{selectedTier.transport}</span>
                        </div>
                        {bookingData.specialRequests && (
                          <div className="flex justify-between text-sm">
                            <span className="text-charcoal/60">Special Requests</span>
                            <span className="font-medium text-right max-w-[200px]">{bookingData.specialRequests}</span>
                          </div>
                        )}
                      </div>

                      <div className="border-t border-charcoal/10 pt-4 space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-charcoal/60">Price per person</span>
                          <span>₹{selectedTier.price.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-charcoal/60">Travellers</span>
                          <span>× {bookingData.travellers}</span>
                        </div>
                        <div className="flex justify-between text-lg font-bold pt-2 border-t border-charcoal/10">
                          <span>Total Amount</span>
                          <span className="text-saffron">₹{totalPrice.toLocaleString()}</span>
                        </div>
                      </div>

                      <Button
                        size="lg"
                        className="w-full gap-2 mt-4"
                        onClick={() => alert('Payment gateway integration coming soon! Booking saved as draft.')}
                      >
                        <CreditCard className="w-4 h-4" />
                        Pay ₹{totalPrice.toLocaleString()}
                      </Button>
                      <p className="text-xs text-charcoal/40 text-center">
                        Secure payment powered by Razorpay. 100% refundable before confirmation.
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Navigation */}
              <div className="flex items-center justify-between mt-6">
                <Button
                  variant="ghost"
                  onClick={prevStep}
                  disabled={currentStep === 1}
                  className="gap-1"
                >
                  <ArrowLeft className="w-4 h-4" /> Previous
                </Button>
                {currentStep < 3 && (
                  <Button onClick={nextStep} className="gap-1">
                    Next <ArrowRight className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>

            {/* Sidebar Summary */}
            <div>
              <div className="bg-white rounded-xl p-5 shadow-sm border border-charcoal/5 sticky top-24">
                <img src={pkg.image} alt={pkg.title} className="w-full h-32 object-cover rounded-lg mb-4" />
                <h3 className="font-display font-semibold mb-1">{pkg.title}</h3>
                <p className="text-sm text-charcoal/50 mb-4">{pkg.destination} • {pkg.duration}</p>
                <div className="space-y-2 text-sm border-t border-charcoal/5 pt-3">
                  <div className="flex justify-between">
                    <span className="text-charcoal/60">Tier</span>
                    <span className="font-medium">{selectedTier.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-charcoal/60">Travellers</span>
                    <span className="font-medium">{bookingData.travellers}</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-charcoal/5 text-base font-bold">
                    <span>Total</span>
                    <span className="text-saffron">₹{totalPrice.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </PageTransition>
  );
}
