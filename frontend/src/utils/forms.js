export const getSessionList = () =>
  Array.from(document.querySelectorAll('input[name="sessionList"]:checked')).map((input) => input.value);

export const getSimGames = (formEl) =>
  Array.from(formEl.querySelectorAll('input[name="simGames"]:checked')).map((input) => input.value);

export const getCheckedValues = (formEl, name) =>
  Array.from(formEl.querySelectorAll(`input[name="${name}"]:checked`)).map((input) => input.value);

export const setCheckedValues = (formEl, name, values) => {
  const valueSet = new Set(values || []);
  formEl.querySelectorAll(`input[name="${name}"]`).forEach((input) => {
    input.checked = valueSet.has(input.value);
  });
};
