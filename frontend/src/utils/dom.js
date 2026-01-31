export const setList = (listEl, items, emptyText) => {
  if (!listEl) return;
  if (!items || items.length === 0) {
    listEl.innerHTML = `<li>${emptyText}</li>`;
    return;
  }
  listEl.innerHTML = items.map((item) => `<li>${item}</li>`).join('');
};

export const getFormValue = (formEl, selector) => {
  const input = formEl ? formEl.querySelector(selector) : null;
  return input ? input.value.trim() : '';
};
