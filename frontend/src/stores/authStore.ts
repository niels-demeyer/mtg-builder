import { writable, derived } from "svelte/store";

const API_BASE = "http://localhost:8000/api/v1";

export interface User {
  id: string;
  username: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

function createAuthStore() {
  const initialState: AuthState = {
    user: null,
    token: null,
    loading: false,
    error: null,
  };

  const { subscribe, update, set } = writable<AuthState>(initialState);

  return {
    subscribe,

    // Initialize auth state from localStorage
    init: async (): Promise<void> => {
      const token = localStorage.getItem("auth-token");
      if (!token) return;

      update((state) => ({ ...state, loading: true }));

      try {
        const response = await fetch(`${API_BASE}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const user = await response.json();
          update((state) => ({
            ...state,
            user,
            token,
            loading: false,
            error: null,
          }));
        } else {
          // Token is invalid, clear it
          localStorage.removeItem("auth-token");
          update((state) => ({ ...state, loading: false }));
        }
      } catch {
        localStorage.removeItem("auth-token");
        update((state) => ({ ...state, loading: false }));
      }
    },

    // Login
    login: async (
      username: string,
      password: string
    ): Promise<{ success: boolean; error?: string }> => {
      update((state) => ({ ...state, loading: true, error: null }));

      try {
        const response = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ username, password }),
        });

        if (response.ok) {
          const data = await response.json();
          const token = data.access_token;

          // Fetch user info
          const userResponse = await fetch(`${API_BASE}/auth/me`, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (userResponse.ok) {
            const user = await userResponse.json();
            localStorage.setItem("auth-token", token);
            update((state) => ({
              ...state,
              user,
              token,
              loading: false,
              error: null,
            }));
            return { success: true };
          }
        }

        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || "Invalid username or password";
        update((state) => ({
          ...state,
          loading: false,
          error: errorMessage,
        }));
        return { success: false, error: errorMessage };
      } catch {
        const errorMessage = "Failed to connect to server";
        update((state) => ({
          ...state,
          loading: false,
          error: errorMessage,
        }));
        return { success: false, error: errorMessage };
      }
    },

    // Register
    register: async (
      username: string,
      password: string
    ): Promise<{ success: boolean; error?: string }> => {
      update((state) => ({ ...state, loading: true, error: null }));

      try {
        const response = await fetch(`${API_BASE}/auth/register`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ username, password }),
        });

        if (response.ok) {
          update((state) => ({ ...state, loading: false, error: null }));
          return { success: true };
        }

        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || "Registration failed";
        update((state) => ({
          ...state,
          loading: false,
          error: errorMessage,
        }));
        return { success: false, error: errorMessage };
      } catch {
        const errorMessage = "Failed to connect to server";
        update((state) => ({
          ...state,
          loading: false,
          error: errorMessage,
        }));
        return { success: false, error: errorMessage };
      }
    },

    // Logout
    logout: (): void => {
      localStorage.removeItem("auth-token");
      set(initialState);
    },

    // Clear error
    clearError: (): void => {
      update((state) => ({ ...state, error: null }));
    },

    // Get auth header for API calls
    getAuthHeader: (): Record<string, string> => {
      const token = localStorage.getItem("auth-token");
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
  };
}

export const authStore = createAuthStore();

// Derived stores for convenience
export const isAuthenticated = derived(
  authStore,
  ($auth) => $auth.user !== null
);

export const currentUser = derived(authStore, ($auth) => $auth.user);
