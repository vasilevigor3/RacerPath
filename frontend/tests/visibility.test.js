import { beforeEach, describe, expect, it } from 'vitest';

describe('visibility helpers', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <section id="dashboards" class="section reveal is-hidden" data-admin-only></section>
    `;
  });

  it('reveals admin sections when enabled', async () => {
    const { setAdminVisibility } = await import('../src/ui/visibility.js');
    const section = document.querySelector('[data-admin-only]');
    expect(section).toBeTruthy();
    expect(section.classList.contains('is-hidden')).toBe(true);

    setAdminVisibility(true);
    expect(section.classList.contains('is-hidden')).toBe(false);

    setAdminVisibility(false);
    expect(section.classList.contains('is-hidden')).toBe(true);
  });
});
