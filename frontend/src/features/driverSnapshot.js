import { fmt } from '../utils/format.js';

const pillCrs = document.querySelector('[data-driver-snapshot-pill-crs]');

export const updateDriverSnapshotMeta = ({ crsScore }) => {
  if (pillCrs) {
    const value = crsScore !== null && crsScore !== undefined ? fmt(crsScore) : '--';
    pillCrs.textContent = `CRS ${value}`;
  }
};

export const resetDriverSnapshot = () => {
  if (pillCrs) pillCrs.textContent = 'CRS --';
};
