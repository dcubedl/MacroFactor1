const BASE_URL = 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Token — held in module scope so it survives re-renders but is cleared on
// a hard page refresh (intentional; add localStorage persistence if needed).
// ---------------------------------------------------------------------------
let _token = null;

// ---------------------------------------------------------------------------
// Core request helper
// ---------------------------------------------------------------------------
async function request(path, options = {}) {
  const headers = { ...options.headers };
  if (_token) {
    headers['Authorization'] = `Bearer ${_token}`;
  }

  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  } catch {
    // Network-level failure (backend down, no internet, CORS preflight blocked)
    const err = new Error(
      'Cannot reach the server. Make sure the backend is running on port 8000.'
    );
    err.status = 0;
    throw err;
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch { /* ignore parse errors */ }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Public API surface
// ---------------------------------------------------------------------------
export const api = {
  /** True if a token is currently held. */
  isAuthenticated: () => _token !== null,

  /** Return the raw token (e.g. to read claims). */
  getToken: () => _token,

  /** Clear token — call after a 401 or explicit logout. */
  clearToken: () => { _token = null; },

  // ---- Auth ----------------------------------------------------------------

  /**
   * Create a new account.
   * Returns AuthResponse from the backend.
   * Sets the in-memory token if a session was issued immediately.
   * `requires_confirmation` will be true if Supabase email confirmation is on.
   */
  async signup(email, password) {
    const data = await request('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (data.access_token) _token = data.access_token;
    return data;
  },

  /**
   * Sign in with email + password.
   * Returns AuthResponse and sets the in-memory token.
   */
  async login(email, password) {
    const data = await request('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (data.access_token) _token = data.access_token;
    return data;
  },

  /** Sign out — clears local token. */
  async logout() {
    try {
      await request('/api/auth/logout', { method: 'POST' });
    } finally {
      _token = null;
    }
  },

  // ---- Profile -------------------------------------------------------------

  /** Fetch the current user's public profile (requires auth). */
  async getUserProfile() {
    return request('/api/auth/me');
  },

  /**
   * Save onboarding answers and other profile fields.
   * All fields are optional — only provided fields are written.
   * Called right after signup to persist the user's onboarding data.
   */
  async updateProfile(data) {
    return request('/api/auth/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },

  // ---- Food scan -----------------------------------------------------------

  /**
   * Upload a food photo and get back a full analysis.
   * Returns FoodScanResponse: food_name, score, meal_rank, explanation,
   * calories, protein_g, carbs_g, fat_g, fiber_g, xp_change.
   */
  async scanFood(photoFile) {
    const form = new FormData();
    form.append('photo', photoFile);
    // Do NOT set Content-Type — the browser must set multipart/form-data
    // with the correct boundary automatically.
    return request('/api/food/scan', {
      method: 'POST',
      body: form,
    });
  },
};
