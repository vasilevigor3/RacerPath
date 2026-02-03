const tabButtons = document.querySelectorAll('[data-tab-button]');
const tabPanels = document.querySelectorAll('[data-tab-panel]');
const tabJumpButtons = document.querySelectorAll('[data-tab-jump]');
const scrollButtons = document.querySelectorAll('[data-scroll-target]');
const statCards = document.querySelectorAll('[data-stat-target]');

export const setupTabs = () => {
  if (!tabButtons.length || !tabPanels.length) return;
  tabButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.getAttribute('data-tab-button');
      tabButtons.forEach((item) => item.classList.remove('active'));
      tabPanels.forEach((panel) => panel.classList.remove('active'));
      button.classList.add('active');
      const panel = document.querySelector(`[data-tab-panel="${target}"]`);
      if (panel) panel.classList.add('active');
      window.dispatchEvent(new CustomEvent('cabinet-tab-change', { detail: { tab: target } }));
    });
  });
  tabJumpButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.getAttribute('data-tab-jump');
      const tab = document.querySelector(`[data-tab-button="${target}"]`);
      if (tab) tab.click();
    });
  });
  scrollButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.getAttribute('data-scroll-target');
      if (!target) return;
      const element = document.querySelector(target);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
};

const highlightFocusTarget = (targetId) => {
  if (!targetId) return;
  const element = document.querySelector(`[data-focus-id="${targetId}"]`);
  if (!element) return;
  element.classList.add('focus-highlight');
  window.setTimeout(() => {
    element.classList.remove('focus-highlight');
  }, 1400);
};

export const setupStatCardNavigation = () => {
  if (!statCards.length) return;
  statCards.forEach((card) => {
    const activate = () => {
      const tabTarget = card.getAttribute('data-tab-target');
      if (tabTarget) {
        const tab = document.querySelector(`[data-tab-button="${tabTarget}"]`);
        if (tab) tab.click();
      }
      const scrollTarget = card.getAttribute('data-scroll-target');
      if (scrollTarget) {
        const section = document.querySelector(scrollTarget);
        if (section) {
          section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
      const focusTarget = card.getAttribute('data-focus-target');
      if (focusTarget) {
        highlightFocusTarget(focusTarget);
      }
    };

    card.addEventListener('click', activate);
    card.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        activate();
      }
    });
  });
};
