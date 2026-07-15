import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Calendar, MapPin, Users, CreditCard, TrendingUp, Clock, CheckCircle, XCircle, Loader } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { PageTransition } from '../components/layout/PageTransition';
import { bookings, stats } from '../data/mockData';

const statusConfig = {
  draft: { label: 'Draft', variant: 'warning', icon: Clock },
  confirmed: { label: 'Confirmed', variant: 'success', icon: CheckCircle },
  in_progress: { label: 'In Progress', variant: 'default', icon: Loader },
  completed: { label: 'Completed', variant: 'secondary', icon: CheckCircle },
  cancelled: { label: 'Cancelled', variant: 'danger', icon: XCircle },
};

export default function Dashboard() {
  return (
    <PageTransition>
      <section className="pt-24 pb-8 bg-gradient-to-b from-river/5 to-cream">
        <div className="container-custom">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h1 className="font-display text-3xl md:text-4xl font-bold text-charcoal mb-1">
              My Dashboard
            </h1>
            <p className="text-charcoal/60">Welcome back! Here's your travel overview.</p>
          </motion.div>
        </div>
      </section>

      <section className="py-8 bg-cream">
        <div className="container-custom">
          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { icon: Calendar, label: 'Total Bookings', value: stats.totalBookings, color: 'bg-saffron/10 text-saffron' },
              { icon: TrendingUp, label: 'Upcoming Trips', value: stats.upcomingTrips, color: 'bg-green-100 text-green-600' },
              { icon: CheckCircle, label: 'Completed', value: stats.completedTrips, color: 'bg-river/10 text-river' },
              { icon: CreditCard, label: 'Total Spent', value: `₹${(stats.totalSpent / 1000).toFixed(0)}K`, color: 'bg-gold/10 text-gold-700' },
            ].map((stat, i) => (
              <motion.div
                key={stat.label}
                className="bg-white rounded-xl p-5 shadow-sm border border-charcoal/5"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
              >
                <div className={`w-10 h-10 rounded-lg ${stat.color} flex items-center justify-center mb-3`}>
                  <stat.icon className="w-5 h-5" />
                </div>
                <p className="text-2xl font-bold text-charcoal">{stat.value}</p>
                <p className="text-xs text-charcoal/50">{stat.label}</p>
              </motion.div>
            ))}
          </div>

          {/* Bookings */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-display text-xl font-semibold text-charcoal">My Bookings</h2>
            <Link to="/packages">
              <Button variant="outline" size="sm">Book New Trip</Button>
            </Link>
          </div>

          <div className="space-y-4">
            {bookings.map((booking, i) => {
              const config = statusConfig[booking.status];
              const StatusIcon = config.icon;
              return (
                <motion.div
                  key={booking.id}
                  className="bg-white rounded-xl p-5 shadow-sm border border-charcoal/5 hover:shadow-md transition-shadow"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-charcoal">{booking.package}</h3>
                        <Badge variant={config.variant} className="gap-1">
                          <StatusIcon className="w-3 h-3" />
                          {config.label}
                        </Badge>
                      </div>
                      <div className="flex flex-wrap items-center gap-4 text-sm text-charcoal/60">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5" /> {booking.destination}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5" /> {booking.dates}
                        </span>
                        <span className="flex items-center gap-1">
                          <Users className="w-3.5 h-3.5" /> {booking.travellers} travellers
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-lg font-bold text-charcoal">₹{booking.amount.toLocaleString()}</p>
                        <p className="text-xs text-charcoal/40">{booking.tier} tier</p>
                      </div>
                      <Button variant="ghost" size="sm">View</Button>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-charcoal/5 flex items-center justify-between">
                    <span className="text-xs text-charcoal/40">Booking ID: {booking.id}</span>
                    {booking.status === 'draft' && (
                      <Button size="sm" variant="default">Complete Booking</Button>
                    )}
                    {booking.status === 'confirmed' && (
                      <Button size="sm" variant="outline">View Details</Button>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>
    </PageTransition>
  );
}
