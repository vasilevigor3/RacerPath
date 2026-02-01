export const DISCIPLINES = [
  { value: 'gt', label: 'GT / Touring' },
  { value: 'formula', label: 'Formula' },
  { value: 'rally', label: 'Rally' },
  { value: 'karting', label: 'Karting' },
  { value: 'historic', label: 'Historic' }
];

export const SIM_GAMES = [
  { value: 'Assetto Corsa', label: 'Assetto Corsa' },
  { value: 'Assetto Corsa Competizione', label: 'ACC' },
  { value: 'iRacing', label: 'iRacing' },
  { value: 'rFactor 2', label: 'rFactor 2' },
  { value: 'AMS2', label: 'AMS2' },
  { value: 'RBR', label: 'RBR' }
];

/** Legacy rig checkboxes (profile.rig) — kept for backward compatibility if used elsewhere. */
export const RIG_OPTIONS = [
  { value: 'Wheel + pedals', label: 'Wheel + pedals' },
  { value: 'Handbrake', label: 'Handbrake' },
  { value: 'Full motion rig', label: 'Full motion rig' }
];

/** Driver rig: wheel type (legacy belt/gear vs direct drive with Nm). */
export const WHEEL_TYPES = [
  { value: '', label: 'Not set' },
  { value: 'legacy', label: 'Legacy (belt/gear)' },
  { value: 'force_feedback_nm', label: 'Force feedback (Nm)' }
];

/** Driver rig: pedals class. */
export const PEDALS_CLASSES = [
  { value: '', label: 'Not set' },
  { value: 'basic', label: 'Basic' },
  { value: 'spring', label: 'Spring' },
  { value: 'premium', label: 'Premium' }
];
