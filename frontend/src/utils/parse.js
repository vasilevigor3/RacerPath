export const parseOptionalInt = (value) => {
  if (value === '' || value === null || value === undefined) return null;
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? null : parsed;
};

export const parseOptionalFloat = (value) => {
  if (value === '' || value === null || value === undefined) return null;
  const parsed = Number.parseFloat(value);
  return Number.isNaN(parsed) ? null : parsed;
};

export const parseJsonField = (value) => {
  if (!value) return {};
  try {
    return JSON.parse(value);
  } catch (err) {
    return null;
  }
};

export const parseDateTime = (value) => (value ? new Date(value).toISOString() : null);
