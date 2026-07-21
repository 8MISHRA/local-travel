import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Mail, Lock, User, Phone, MapPin } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { PageTransition } from '../components/layout/PageTransition';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', phone: '', password: '', confirmPassword: '' });
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState('');
  const { register, loading } = useAuth();
  const navigate = useNavigate();

  const update = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const validate = () => {
    const newErrors = {};
    if (!form.name.trim()) newErrors.name = 'Name is required';
    if (!form.email) newErrors.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(form.email)) newErrors.email = 'Invalid email address';
    if (!form.phone) newErrors.phone = 'Phone number is required';
    else if (!/^\d{10}$/.test(form.phone)) newErrors.phone = 'Enter a valid 10-digit number';
    if (!form.password) newErrors.password = 'Password is required';
    else if (form.password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    if (form.password !== form.confirmPassword) newErrors.confirmPassword = 'Passwords do not match';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError('');
    if (validate()) {
      try {
        await register(form.email, form.password, form.name, form.phone);
        navigate('/dashboard');
      } catch (err) {
        setApiError(err.message || 'Registration failed. Please try again.');
      }
    }
  };

  return (
    <PageTransition>
      <section className="min-h-screen flex items-center justify-center bg-cream pt-20 pb-8 px-4">
        <motion.div
          className="w-full max-w-md"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Header */}
          <div className="text-center mb-8">
            <Link to="/" className="inline-flex items-center gap-2 mb-6">
              <div className="w-10 h-10 rounded-xl gradient-saffron flex items-center justify-center">
                <MapPin className="w-5 h-5 text-white" />
              </div>
              <span className="font-display text-2xl font-bold text-charcoal">YatraFlow</span>
            </Link>
            <h1 className="font-display text-2xl font-bold text-charcoal mb-1">Create Your Account</h1>
            <p className="text-sm text-charcoal/60">Join YatraFlow and start exploring incredible destinations</p>
          </div>

          {/* Form */}
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-charcoal/5">
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              <div>
                <label htmlFor="name" className="text-sm font-medium text-charcoal/70 block mb-1.5">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-charcoal/30" />
                  <Input
                    id="name"
                    placeholder="John Doe"
                    className="pl-10"
                    value={form.name}
                    onChange={(e) => update('name', e.target.value)}
                    aria-invalid={!!errors.name}
                  />
                </div>
                {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name}</p>}
              </div>

              <div>
                <label htmlFor="reg-email" className="text-sm font-medium text-charcoal/70 block mb-1.5">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-charcoal/30" />
                  <Input
                    id="reg-email"
                    type="email"
                    placeholder="you@example.com"
                    className="pl-10"
                    value={form.email}
                    onChange={(e) => update('email', e.target.value)}
                    aria-invalid={!!errors.email}
                  />
                </div>
                {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email}</p>}
              </div>

              <div>
                <label htmlFor="phone" className="text-sm font-medium text-charcoal/70 block mb-1.5">Phone Number</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-charcoal/30" />
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="9876543210"
                    className="pl-10"
                    value={form.phone}
                    onChange={(e) => update('phone', e.target.value)}
                    aria-invalid={!!errors.phone}
                  />
                </div>
                {errors.phone && <p className="text-xs text-red-500 mt-1">{errors.phone}</p>}
              </div>

              <div>
                <label htmlFor="reg-password" className="text-sm font-medium text-charcoal/70 block mb-1.5">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-charcoal/30" />
                  <Input
                    id="reg-password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    className="pl-10 pr-10"
                    value={form.password}
                    onChange={(e) => update('password', e.target.value)}
                    aria-invalid={!!errors.password}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-charcoal/30 hover:text-charcoal/60"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password}</p>}
              </div>

              <div>
                <label htmlFor="confirm-password" className="text-sm font-medium text-charcoal/70 block mb-1.5">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-charcoal/30" />
                  <Input
                    id="confirm-password"
                    type="password"
                    placeholder="••••••••"
                    className="pl-10"
                    value={form.confirmPassword}
                    onChange={(e) => update('confirmPassword', e.target.value)}
                    aria-invalid={!!errors.confirmPassword}
                  />
                </div>
                {errors.confirmPassword && <p className="text-xs text-red-500 mt-1">{errors.confirmPassword}</p>}
              </div>

              <div className="pt-2">
                <label className="flex items-start gap-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 rounded accent-saffron mt-0.5" />
                  <span className="text-xs text-charcoal/60">
                    I agree to the <a href="#" className="text-saffron hover:underline">Terms of Service</a> and <a href="#" className="text-saffron hover:underline">Privacy Policy</a>
                  </span>
                </label>
              </div>

              <Button type="submit" size="lg" className="w-full" disabled={loading}>
                {loading ? 'Creating Account...' : 'Create Account'}
              </Button>

              {apiError && (
                <p className="text-sm text-red-500 text-center bg-red-50 p-2 rounded-lg">{apiError}</p>
              )}
            </form>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-charcoal/10" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-white px-3 text-charcoal/40">or continue with</span>
              </div>
            </div>

            {/* Google Sign Up */}
            <button
              type="button"
              onClick={() => alert('Google OAuth coming soon! You need to configure GOOGLE_CLIENT_ID in .env')}
              className="w-full flex items-center justify-center gap-3 h-11 px-4 rounded-lg border-2 border-charcoal/10 bg-white text-charcoal font-medium text-sm hover:border-charcoal/20 hover:bg-charcoal/[0.02] transition-all duration-200"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Sign up with Google
            </button>

            <div className="mt-6 text-center">
              <p className="text-sm text-charcoal/60">
                Already have an account?{' '}
                <Link to="/login" className="text-saffron font-medium hover:underline">
                  Log in
                </Link>
              </p>
            </div>
          </div>
        </motion.div>
      </section>
    </PageTransition>
  );
}
