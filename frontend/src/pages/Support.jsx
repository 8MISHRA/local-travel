import { useState } from 'react';
import { motion } from 'framer-motion';
import { Send, Phone, Mail, MapPin, MessageSquare, Clock } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { PageTransition } from '../components/layout/PageTransition';

export default function Support() {
  const [form, setForm] = useState({
    name: '',
    email: '',
    subject: '',
    priority: 'medium',
    description: '',
  });
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <PageTransition>
        <section className="py-20 min-h-[60vh] flex items-center">
          <div className="container-custom text-center">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: 'spring', duration: 0.6 }}
              className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6"
            >
              <Send className="w-8 h-8 text-green-600" />
            </motion.div>
            <h2 className="font-display text-3xl font-bold text-charcoal mb-3">
              Ticket Submitted!
            </h2>
            <p className="text-charcoal/60 max-w-md mx-auto mb-6">
              We've received your support request and will get back to you within 24 hours.
              Check your email for the ticket confirmation.
            </p>
            <Button onClick={() => setSubmitted(false)} variant="outline">
              Submit Another Ticket
            </Button>
          </div>
        </section>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      {/* Header */}
      <section className="py-16 bg-river text-white">
        <div className="container-custom text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h1 className="font-display text-4xl md:text-5xl font-bold mb-4">
              How Can We Help?
            </h1>
            <p className="text-white/70 max-w-lg mx-auto text-lg">
              Our team is here to assist you. Raise a support ticket and we'll respond within 24 hours.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Contact Info + Form */}
      <section className="py-16">
        <div className="container-custom">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            {/* Contact Info */}
            <div className="space-y-6">
              <h3 className="font-display text-2xl font-bold text-charcoal">
                Get in Touch
              </h3>
              <p className="text-charcoal/60">
                Have questions about your trip or need immediate assistance? Reach out through any of these channels.
              </p>

              <div className="space-y-4 pt-4">
                {[
                  { icon: Phone, label: 'Phone', value: '+91 9876 543 210', desc: 'Mon-Sat, 9am-8pm IST' },
                  { icon: Mail, label: 'Email', value: 'support@yatraflow.in', desc: 'We reply within 24 hrs' },
                  { icon: MapPin, label: 'Office', value: 'Assi Ghat, Varanasi', desc: 'Uttar Pradesh, India' },
                  { icon: Clock, label: 'Hours', value: '9:00 AM - 8:00 PM', desc: 'Monday to Saturday' },
                ].map((item) => (
                  <div key={item.label} className="flex items-start gap-4 p-4 rounded-xl bg-white shadow-sm">
                    <div className="w-10 h-10 rounded-lg bg-saffron/10 flex items-center justify-center shrink-0">
                      <item.icon className="w-5 h-5 text-saffron" />
                    </div>
                    <div>
                      <p className="font-medium text-charcoal">{item.value}</p>
                      <p className="text-xs text-charcoal/50">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Form */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-2xl p-8 shadow-lg">
                <div className="flex items-center gap-3 mb-6">
                  <MessageSquare className="w-6 h-6 text-saffron" />
                  <h3 className="font-display text-xl font-bold text-charcoal">
                    Raise a Support Ticket
                  </h3>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-sm font-medium text-charcoal/70 mb-1.5">
                        Full Name
                      </label>
                      <Input
                        name="name"
                        value={form.name}
                        onChange={handleChange}
                        placeholder="Your name"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-charcoal/70 mb-1.5">
                        Email
                      </label>
                      <Input
                        name="email"
                        type="email"
                        value={form.email}
                        onChange={handleChange}
                        placeholder="you@example.com"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div>
                      <label className="block text-sm font-medium text-charcoal/70 mb-1.5">
                        Subject
                      </label>
                      <Input
                        name="subject"
                        value={form.subject}
                        onChange={handleChange}
                        placeholder="Brief description of your issue"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-charcoal/70 mb-1.5">
                        Priority
                      </label>
                      <select
                        name="priority"
                        value={form.priority}
                        onChange={handleChange}
                        className="w-full px-4 py-2.5 rounded-lg border border-charcoal/10 bg-cream/50 text-charcoal focus:outline-none focus:ring-2 focus:ring-saffron/30 focus:border-saffron transition-colors"
                      >
                        <option value="low">Low — General inquiry</option>
                        <option value="medium">Medium — Need help soon</option>
                        <option value="high">High — Urgent issue</option>
                        <option value="urgent">Urgent — Trip in progress</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-charcoal/70 mb-1.5">
                      Description
                    </label>
                    <textarea
                      name="description"
                      value={form.description}
                      onChange={handleChange}
                      rows={5}
                      placeholder="Please describe your issue in detail. Include booking ID if applicable..."
                      required
                      className="w-full px-4 py-3 rounded-lg border border-charcoal/10 bg-cream/50 text-charcoal placeholder:text-charcoal/30 focus:outline-none focus:ring-2 focus:ring-saffron/30 focus:border-saffron transition-colors resize-none"
                    />
                  </div>

                  <Button type="submit" size="lg" className="w-full gap-2">
                    <Send className="w-4 h-4" />
                    Submit Ticket
                  </Button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </section>
    </PageTransition>
  );
}
