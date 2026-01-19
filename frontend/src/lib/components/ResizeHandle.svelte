<script lang="ts">
  interface Props {
    direction: 'horizontal' | 'vertical';
    onResize: (delta: number) => void;
  }

  let { direction, onResize }: Props = $props();

  let isResizing = $state(false);
  let startPos = $state(0);

  function handleMouseDown(e: MouseEvent): void {
    e.preventDefault();
    isResizing = true;
    startPos = direction === 'horizontal' ? e.clientX : e.clientY;
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize';
    document.body.style.userSelect = 'none';
  }

  function handleMouseMove(e: MouseEvent): void {
    if (!isResizing) return;
    
    const currentPos = direction === 'horizontal' ? e.clientX : e.clientY;
    const delta = currentPos - startPos;
    startPos = currentPos;
    
    onResize(delta);
  }

  function handleMouseUp(): void {
    isResizing = false;
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions a11y_no_noninteractive_tabindex -->
<div 
  class="resize-handle {direction}"
  class:resizing={isResizing}
  onmousedown={handleMouseDown}
  role="separator"
  aria-orientation={direction}
  aria-label="Resize panel"
></div>

<style>
  .resize-handle {
    background: transparent;
    transition: background var(--transition-fast);
    flex-shrink: 0;
    position: relative;
  }

  .resize-handle::after {
    content: '';
    position: absolute;
    background: hsl(var(--border));
    transition: background var(--transition-fast);
  }

  .resize-handle.horizontal {
    width: 6px;
    cursor: col-resize;
  }

  .resize-handle.horizontal::after {
    top: 0;
    bottom: 0;
    left: 50%;
    width: 1px;
    transform: translateX(-50%);
  }

  .resize-handle.vertical {
    height: 6px;
    cursor: row-resize;
  }

  .resize-handle.vertical::after {
    left: 0;
    right: 0;
    top: 50%;
    height: 1px;
    transform: translateY(-50%);
  }

  .resize-handle:hover::after,
  .resize-handle.resizing::after {
    background: hsl(var(--primary));
  }

  .resize-handle:hover,
  .resize-handle.resizing {
    background: hsl(var(--primary) / 0.1);
  }

  .resize-handle.horizontal:hover::after,
  .resize-handle.horizontal.resizing::after {
    width: 3px;
  }

  .resize-handle.vertical:hover::after,
  .resize-handle.vertical.resizing::after {
    height: 3px;
  }
</style>
