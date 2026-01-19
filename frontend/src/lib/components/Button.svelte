<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    onclick?: () => void;
    children: Snippet;
  }

  let {
    variant = 'primary',
    size = 'md',
    disabled = false,
    onclick,
    children
  }: Props = $props();
</script>

<button
  class="btn btn-{variant} btn-{size}"
  {disabled}
  {onclick}
>
  {@render children()}
</button>

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    white-space: nowrap;
    font-weight: 500;
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
    outline: none;
    border: none;
    cursor: pointer;
    font-family: inherit;
  }

  .btn:focus-visible {
    outline: 2px solid hsl(var(--ring));
    outline-offset: 2px;
  }

  .btn:disabled {
    pointer-events: none;
    opacity: 0.5;
  }

  /* Sizes */
  .btn-sm {
    height: 2rem;
    padding: 0 0.75rem;
    font-size: 0.8125rem;
  }

  .btn-md {
    height: 2.5rem;
    padding: 0 1rem;
    font-size: 0.875rem;
  }

  .btn-lg {
    height: 3rem;
    padding: 0 2rem;
    font-size: 1rem;
  }

  /* Variants */
  .btn-primary {
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
  }

  .btn-primary:hover {
    background: hsl(0 0% 85%);
    box-shadow: var(--shadow-glow);
  }

  .btn-secondary {
    background: hsl(var(--secondary));
    color: hsl(var(--secondary-foreground));
  }

  .btn-secondary:hover {
    background: hsl(0 0% 20%);
  }

  .btn-outline {
    background: transparent;
    border: 1px solid hsl(var(--border));
    color: hsl(var(--foreground));
  }

  .btn-outline:hover {
    background: hsl(var(--accent));
    color: hsl(var(--accent-foreground));
  }

  .btn-ghost {
    background: transparent;
    color: hsl(var(--foreground));
  }

  .btn-ghost:hover {
    background: hsl(var(--accent));
    color: hsl(var(--accent-foreground));
  }

  .btn-destructive {
    background: hsl(var(--destructive));
    color: hsl(var(--destructive-foreground));
  }

  .btn-destructive:hover {
    background: hsl(0 62.8% 40%);
  }
</style>
