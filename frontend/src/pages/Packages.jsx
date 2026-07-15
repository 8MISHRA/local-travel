import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { PackageCard } from '../components/shared/PackageCard';
import { PageTransition } from '../components/layout/PageTransition';
import { packages } from '../data/mockData';

export default function Packages() {
  const [search, setSearch] = useState('');
  const [destination, setDestination] = useState('all');
  const [duration, setDuration] = useState('all');
  const [travellerType, setTravellerType] = useState('all');
  const [priceRange, setPriceRange] = useState('all');
  const [showFilters, setShowFilters] = useState(false);

  const filteredPackages = useMemo(() => {
    return packages.filter((pkg) => {
      if (search && !pkg.title.toLowerCase().includes(search.toLowerCase()) && !pkg.description.toLowerCase().includes(search.toLowerCase())) return false;
      if (destination !== 'all' && pkg.destination.toLowerCase() !== destination) return false;
      if (travellerType !== 'all' && pkg.travellerType !== travellerType && pkg.travellerType !== 'all') return false;
      if (priceRange === 'budget' && pkg.price > 5000) return false;
      if (priceRange === 'mid' && (pkg.price < 5000 || pkg.price > 15000)) return false;
      if (priceRange === 'premium' && pkg.price < 15000) return false;
      if (duration === '1day' && !pkg.duration.includes('1 Day')) return false;
      if (duration === '2-3days' && !pkg.duration.match(/[23] Day/)) return false;
      if (duration === '5+days' && !pkg.duration.match(/[5-9] Day/)) return false;
      return true;
    });
  }, [search, destination, duration, travellerType, priceRange]);

  const clearFilters = () => {
    setSearch('');
    setDestination('all');
    setDuration('all');
    setTravellerType('all');
    setPriceRange('all');
  };

  const hasFilters = destination !== 'all' || duration !== 'all' || travellerType !== 'all' || priceRange !== 'all' || search;

  return (
    <PageTransition>
      {/* Header */}
      <section className="pt-24 pb-12 bg-gradient-to-b from-river/5 to-cream">
        <div className="container-custom">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <h1 className="font-display text-3xl md:text-5xl font-bold text-charcoal mb-3">
              Travel Packages
            </h1>
            <p className="text-charcoal/60 max-w-lg mx-auto">
              Choose from our curated collection of experiences in Varanasi & Mirzapur
            </p>
          </motion.div>

          {/* Search Bar */}
          <div className="mt-8 max-w-xl mx-auto relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-charcoal/30" />
            <Input
              placeholder="Search packages..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 h-12 text-base"
            />
          </div>
        </div>
      </section>

      <section className="py-8 bg-cream">
        <div className="container-custom">
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Filter Sidebar (Desktop) */}
            <aside className="hidden lg:block w-64 shrink-0">
              <div className="bg-white rounded-xl p-6 shadow-sm border border-charcoal/5 sticky top-24">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="font-display font-semibold text-lg">Filters</h3>
                  {hasFilters && (
                    <button onClick={clearFilters} className="text-xs text-saffron hover:underline">
                      Clear all
                    </button>
                  )}
                </div>

                {/* Destination */}
                <div className="mb-6">
                  <label className="text-sm font-medium text-charcoal/70 block mb-2">Destination</label>
                  <div className="space-y-2">
                    {[
                      { value: 'all', label: 'All Destinations' },
                      { value: 'varanasi', label: 'Varanasi' },
                      { value: 'mirzapur', label: 'Mirzapur' },
                    ].map((opt) => (
                      <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="destination"
                          value={opt.value}
                          checked={destination === opt.value}
                          onChange={(e) => setDestination(e.target.value)}
                          className="w-4 h-4 text-saffron accent-saffron"
                        />
                        <span className="text-sm text-charcoal/70">{opt.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Duration */}
                <div className="mb-6">
                  <label className="text-sm font-medium text-charcoal/70 block mb-2">Duration</label>
                  <div className="space-y-2">
                    {[
                      { value: 'all', label: 'Any Duration' },
                      { value: '1day', label: '1 Day Trip' },
                      { value: '2-3days', label: '2-3 Days' },
                      { value: '5+days', label: '5+ Days' },
                    ].map((opt) => (
                      <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="duration"
                          value={opt.value}
                          checked={duration === opt.value}
                          onChange={(e) => setDuration(e.target.value)}
                          className="w-4 h-4 text-saffron accent-saffron"
                        />
                        <span className="text-sm text-charcoal/70">{opt.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Traveller Type */}
                <div className="mb-6">
                  <label className="text-sm font-medium text-charcoal/70 block mb-2">Traveller Type</label>
                  <div className="space-y-2">
                    {[
                      { value: 'all', label: 'All Types' },
                      { value: 'solo', label: 'Solo' },
                      { value: 'couple', label: 'Couple' },
                      { value: 'family', label: 'Family' },
                      { value: 'friends', label: 'Friends' },
                    ].map((opt) => (
                      <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="travellerType"
                          value={opt.value}
                          checked={travellerType === opt.value}
                          onChange={(e) => setTravellerType(e.target.value)}
                          className="w-4 h-4 text-saffron accent-saffron"
                        />
                        <span className="text-sm text-charcoal/70">{opt.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Price Range */}
                <div>
                  <label className="text-sm font-medium text-charcoal/70 block mb-2">Price Range</label>
                  <div className="space-y-2">
                    {[
                      { value: 'all', label: 'Any Price' },
                      { value: 'budget', label: 'Under ₹5,000' },
                      { value: 'mid', label: '₹5,000 - ₹15,000' },
                      { value: 'premium', label: 'Above ₹15,000' },
                    ].map((opt) => (
                      <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="priceRange"
                          value={opt.value}
                          checked={priceRange === opt.value}
                          onChange={(e) => setPriceRange(e.target.value)}
                          className="w-4 h-4 text-saffron accent-saffron"
                        />
                        <span className="text-sm text-charcoal/70">{opt.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </aside>

            {/* Mobile Filter Toggle */}
            <div className="lg:hidden flex items-center gap-3 mb-4">
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => setShowFilters(!showFilters)}
              >
                <SlidersHorizontal className="w-4 h-4" />
                Filters
              </Button>
              {hasFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters} className="gap-1 text-saffron">
                  <X className="w-3 h-3" /> Clear
                </Button>
              )}
            </div>

            {/* Mobile Filters */}
            {showFilters && (
              <div className="lg:hidden bg-white rounded-xl p-4 shadow-sm border border-charcoal/5 mb-4">
                <div className="grid grid-cols-2 gap-4">
                  <select
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    className="text-sm rounded-lg border border-charcoal/20 px-3 py-2"
                    aria-label="Filter by destination"
                  >
                    <option value="all">All Destinations</option>
                    <option value="varanasi">Varanasi</option>
                    <option value="mirzapur">Mirzapur</option>
                  </select>
                  <select
                    value={priceRange}
                    onChange={(e) => setPriceRange(e.target.value)}
                    className="text-sm rounded-lg border border-charcoal/20 px-3 py-2"
                    aria-label="Filter by price range"
                  >
                    <option value="all">Any Price</option>
                    <option value="budget">Under ₹5,000</option>
                    <option value="mid">₹5K - ₹15K</option>
                    <option value="premium">Above ₹15K</option>
                  </select>
                  <select
                    value={travellerType}
                    onChange={(e) => setTravellerType(e.target.value)}
                    className="text-sm rounded-lg border border-charcoal/20 px-3 py-2"
                    aria-label="Filter by traveller type"
                  >
                    <option value="all">All Types</option>
                    <option value="solo">Solo</option>
                    <option value="couple">Couple</option>
                    <option value="family">Family</option>
                    <option value="friends">Friends</option>
                  </select>
                  <select
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    className="text-sm rounded-lg border border-charcoal/20 px-3 py-2"
                    aria-label="Filter by duration"
                  >
                    <option value="all">Any Duration</option>
                    <option value="1day">1 Day</option>
                    <option value="2-3days">2-3 Days</option>
                    <option value="5+days">5+ Days</option>
                  </select>
                </div>
              </div>
            )}

            {/* Package Grid */}
            <div className="flex-1">
              <div className="flex items-center justify-between mb-6">
                <p className="text-sm text-charcoal/60">
                  Showing <span className="font-semibold text-charcoal">{filteredPackages.length}</span> packages
                </p>
                {hasFilters && (
                  <div className="hidden lg:flex gap-2">
                    {destination !== 'all' && <Badge variant="default">{destination} <X className="w-3 h-3 ml-1 cursor-pointer" onClick={() => setDestination('all')} /></Badge>}
                    {priceRange !== 'all' && <Badge variant="default">{priceRange} <X className="w-3 h-3 ml-1 cursor-pointer" onClick={() => setPriceRange('all')} /></Badge>}
                  </div>
                )}
              </div>

              {filteredPackages.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {filteredPackages.map((pkg, i) => (
                    <motion.div
                      key={pkg.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <PackageCard pkg={pkg} />
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-20">
                  <p className="text-charcoal/50 text-lg mb-4">No packages found matching your filters</p>
                  <Button variant="outline" onClick={clearFilters}>Clear Filters</Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>
    </PageTransition>
  );
}
