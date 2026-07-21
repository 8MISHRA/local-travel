const API_URL = import.meta.env.VITE_API_URL || 'https://yatraflow-api.onrender.com/api/v1';

class ApiService {
  constructor() {
    this.baseUrl = API_URL;
  }

  getToken() {
    return localStorage.getItem('access_token');
  }

  setTokens(accessToken, refreshToken) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle token expiry — try refresh
    if (response.status === 401 && token) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.getToken()}`;
        const retryResponse = await fetch(url, { ...options, headers });
        return this.handleResponse(retryResponse);
      } else {
        this.clearTokens();
        window.location.hash = '#/login';
        throw new Error('Session expired. Please log in again.');
      }
    }

    return this.handleResponse(response);
  }

  async handleResponse(response) {
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(data.error?.message || 'Something went wrong');
      error.status = response.status;
      error.code = data.error?.code;
      error.details = data.error?.details;
      throw error;
    }
    return data;
  }

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) return false;

      const data = await response.json();
      this.setTokens(data.data.access_token, data.data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  // Auth
  async register(email, password, fullName, phone) {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName, phone }),
    });
    this.setTokens(data.data.access_token, data.data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.data.user));
    return data.data;
  }

  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setTokens(data.data.access_token, data.data.refresh_token);
    localStorage.setItem('user', JSON.stringify(data.data.user));
    return data.data;
  }

  async logout() {
    const refreshToken = localStorage.getItem('refresh_token');
    try {
      await this.request('/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
      // Ignore errors on logout
    }
    this.clearTokens();
  }

  async getMe() {
    return this.request('/auth/me');
  }

  // Packages
  async getPackages(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/packages${query ? '?' + query : ''}`);
  }

  async getPackage(id) {
    return this.request(`/packages/${id}`);
  }

  // Destinations
  async getDestinations() {
    return this.request('/destinations');
  }

  // Bookings
  async getBookings(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/bookings${query ? '?' + query : ''}`);
  }

  async createBooking(bookingData) {
    return this.request('/bookings', {
      method: 'POST',
      body: JSON.stringify(bookingData),
    });
  }

  async submitBooking(bookingId) {
    return this.request(`/bookings/${bookingId}/submit`, { method: 'POST' });
  }

  async cancelBooking(bookingId, notes) {
    return this.request(`/bookings/${bookingId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  }

  // Support
  async createTicket(ticketData) {
    return this.request('/support-tickets', {
      method: 'POST',
      body: JSON.stringify(ticketData),
    });
  }

  async getTickets() {
    return this.request('/support-tickets');
  }
}

export const api = new ApiService();
