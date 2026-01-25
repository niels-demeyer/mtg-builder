<script lang="ts">
  import { authStore } from '../../stores/authStore';
  import { deckStore } from '../../stores/deckStore';

  interface Props {
    onNavigate: (view: string) => void;
  }

  let { onNavigate }: Props = $props();

  let username = $state('');
  let password = $state('');
  let error = $state('');
  let loading = $state(false);

  async function handleSubmit(event: Event): Promise<void> {
    event.preventDefault();
    if (!username.trim() || !password) return;

    loading = true;
    error = '';

    const result = await authStore.login(username.trim(), password);

    loading = false;

    if (result.success) {
      await deckStore.loadDecks();
      onNavigate('home');
    } else {
      error = result.error || 'Login failed';
    }
  }
</script>

<div class="auth-container">
  <div class="auth-card">
    <div class="auth-header">
      <div class="logo-icon">✦</div>
      <h1>Welcome Back</h1>
      <p>Sign in to your MTG Builder account</p>
    </div>

    <form onsubmit={handleSubmit}>
      {#if error}
        <div class="error-message">{error}</div>
      {/if}

      <div class="form-group">
        <label for="username">Username</label>
        <input
          id="username"
          type="text"
          placeholder="Enter your username"
          bind:value={username}
          disabled={loading}
          required
        />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
          id="password"
          type="password"
          placeholder="Enter your password"
          bind:value={password}
          disabled={loading}
          required
        />
      </div>

      <button type="submit" class="submit-btn" disabled={loading || !username.trim() || !password}>
        {#if loading}
          Signing in...
        {:else}
          Sign In
        {/if}
      </button>
    </form>

    <div class="auth-footer">
      <p>Don't have an account? <button class="link-btn" onclick={() => onNavigate('register')}>Create one</button></p>
    </div>
  </div>
</div>

<style>
  .auth-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background: var(--color-bg);
  }

  .auth-card {
    width: 100%;
    max-width: 400px;
    background: var(--color-bg-tertiary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    padding: 2rem;
    box-shadow: var(--shadow-lg);
  }

  .auth-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .logo-icon {
    width: 48px;
    height: 48px;
    background: hsl(var(--foreground));
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    color: hsl(var(--background));
    margin: 0 auto 1rem;
  }

  .auth-header h1 {
    margin: 0 0 0.5rem;
    color: var(--color-text);
    font-size: 1.5rem;
    font-weight: 600;
  }

  .auth-header p {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
  }

  .error-message {
    background: hsl(var(--destructive) / 0.1);
    border: 1px solid hsl(var(--destructive) / 0.3);
    color: hsl(var(--destructive));
    padding: 0.75rem 1rem;
    border-radius: var(--radius-md);
    margin-bottom: 1.5rem;
    font-size: 0.875rem;
  }

  .form-group {
    margin-bottom: 1.25rem;
  }

  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    font-size: 0.9rem;
    color: var(--color-text-secondary);
  }

  .form-group input {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: 0.95rem;
    font-family: inherit;
    background: var(--color-bg-secondary);
    color: var(--color-text);
  }

  .form-group input::placeholder {
    color: var(--color-text-muted);
  }

  .form-group input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px var(--color-primary-muted);
  }

  .form-group input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .submit-btn {
    width: 100%;
    padding: 0.875rem;
    background: var(--color-primary);
    color: var(--color-bg);
    border: none;
    border-radius: var(--radius-md);
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all var(--transition-fast);
    margin-top: 0.5rem;
  }

  .submit-btn:hover:not(:disabled) {
    background: var(--color-primary-hover);
    box-shadow: var(--shadow-glow);
  }

  .submit-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .auth-footer {
    text-align: center;
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--color-border-subtle);
  }

  .auth-footer p {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
  }

  .link-btn {
    background: none;
    border: none;
    color: var(--color-primary);
    font-size: inherit;
    font-weight: 500;
    cursor: pointer;
    padding: 0;
    text-decoration: underline;
  }

  .link-btn:hover {
    color: var(--color-primary-hover);
  }
</style>
