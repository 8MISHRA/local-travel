import { Link } from 'react-router-dom';
import { MapPin, Phone, Mail, Globe, MessageCircle, Heart } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-charcoal text-white">
      <div className="container-custom py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg gradient-saffron flex items-center justify-center">
                <MapPin className="w-4 h-4 text-white" />
              </div>
              <span className="font-display text-xl font-bold">YatraFlow</span>
            </div>
            <p className="text-sm text-white/60 leading-relaxed">
              Just reach Varanasi or Mirzapur. We take care of everything else. Premium curated travel experiences.
            </p>
            <div className="flex gap-3">
              <a href="#" className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center hover:bg-saffron transition-colors" aria-label="Website">
                <Globe className="w-4 h-4" />
              </a>
              <a href="#" className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center hover:bg-saffron transition-colors" aria-label="Chat">
                <MessageCircle className="w-4 h-4" />
              </a>
              <a href="#" className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center hover:bg-saffron transition-colors" aria-label="Love">
                <Heart className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-display font-semibold text-lg mb-4">Quick Links</h4>
            <ul className="space-y-2.5">
              {[
                { name: 'All Packages', path: '/packages' },
                { name: 'Destinations', path: '/destinations' },
                { name: 'About Us', path: '/' },
                { name: 'Support', path: '/support' },
              ].map((link) => (
                <li key={link.path + link.name}>
                  <Link to={link.path} className="text-sm text-white/60 hover:text-saffron transition-colors">
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Destinations */}
          <div>
            <h4 className="font-display font-semibold text-lg mb-4">Destinations</h4>
            <ul className="space-y-2.5">
              {['Varanasi Ghats', 'Sarnath', 'Vindhyachal', 'Chunar Fort', 'Tanda Falls', 'Mirzapur'].map((dest) => (
                <li key={dest}>
                  <Link to="/destinations" className="text-sm text-white/60 hover:text-saffron transition-colors">
                    {dest}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-display font-semibold text-lg mb-4">Contact Us</h4>
            <ul className="space-y-3">
              <li className="flex items-center gap-2 text-sm text-white/60">
                <Phone className="w-4 h-4 text-saffron" />
                +91 9876 543 210
              </li>
              <li className="flex items-center gap-2 text-sm text-white/60">
                <Mail className="w-4 h-4 text-saffron" />
                hello@yatraflow.com
              </li>
              <li className="flex items-start gap-2 text-sm text-white/60">
                <MapPin className="w-4 h-4 text-saffron shrink-0 mt-0.5" />
                Assi Ghat, Varanasi, Uttar Pradesh 221005
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-white/40">
            © 2025 YatraFlow. All rights reserved.
          </p>
          <div className="flex gap-6">
            <a href="#" className="text-xs text-white/40 hover:text-white/60 transition-colors">Privacy Policy</a>
            <a href="#" className="text-xs text-white/40 hover:text-white/60 transition-colors">Terms of Service</a>
            <a href="#" className="text-xs text-white/40 hover:text-white/60 transition-colors">Refund Policy</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
