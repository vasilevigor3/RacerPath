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

/** Returns "Starts in: Xd Xh Xm" or "Starts in: Xh Xm Xs" or "Register now — starts soon!" (past = "Started") */
export const formatCountdown = (startTimeUtc) => {
  if (!startTimeUtc) return '';
  const start = new Date(startTimeUtc);
  if (Number.isNaN(start.getTime())) return '';
  const now = new Date();
  const ms = start.getTime() - now.getTime();
  if (ms <= 0) return 'Started';
  const sec = Math.floor(ms / 1000) % 60;
  const min = Math.floor(ms / 60000) % 60;
  const hours = Math.floor(ms / 3600000) % 24;
  const days = Math.floor(ms / 86400000);
  if (days > 0) return `Starts in: ${days}d ${hours}h ${min}m`;
  if (hours > 0) return `Starts in: ${hours}h ${min}m ${sec}s`;
  if (min > 0) return `Starts in: ${min}m ${sec}s`;
  return 'Register now — starts soon!';
};
