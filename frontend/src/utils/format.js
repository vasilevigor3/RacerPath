export const fmt = (value) => Math.round(value || 0);

export const formatDiscipline = (value) => {
  if (!value) return '--';
  return value.toUpperCase();
};

export const toInitials = (value) => {
  if (!value) return 'RP';
  const parts = value.trim().split(' ').filter(Boolean);
  const initials = parts.slice(0, 2).map((part) => part[0].toUpperCase());
  return initials.join('') || 'RP';
};

export const formatDateTime = (value) => {
  if (!value) return 'TBD';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'TBD' : date.toLocaleString();
};
