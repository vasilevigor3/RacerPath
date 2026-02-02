import { apiFetch } from '../api/client.js';

const penaltyList = document.querySelector('[data-penalty-list]');
const penaltiesTotalEls = document.querySelectorAll('[data-penalties-total], [data-penalties-total-card]');

const PENALTY_TYPE_LABELS = {
  time_penalty: 'Time penalty',
  drive_through: 'Drive through',
  stop_and_go: 'Stop and go',
  dsq: 'DSQ'
};

function setPenaltiesTotal(total) {
  const value = total == null ? '0' : String(total);
  penaltiesTotalEls.forEach((el) => { el.textContent = value; });
}

function formatPenaltyLabel(item) {
  const typeLabel = PENALTY_TYPE_LABELS[item.penalty_type] ?? item.penalty_type;
  if (item.penalty_type === 'time_penalty' && item.time_seconds != null) {
    return `${typeLabel} +${item.time_seconds}s`;
  }
  if (item.penalty_type === 'stop_and_go' && item.time_seconds != null) {
    return `${typeLabel} (${item.time_seconds}s)`;
  }
  return typeLabel;
}

function formatDate(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { dateStyle: 'short' }) + ' ' + d.toLocaleTimeString(undefined, { timeStyle: 'short' });
  } catch (_) {
    return iso;
  }
}

export const loadPenalties = async (driver) => {
  if (!penaltyList) return;
  penaltyList.innerHTML = '<li>Loading...</li>';
  setPenaltiesTotal(0);
  try {
    const url = driver ? `/api/penalties?driver_id=${driver.id}&limit=200` : '/api/penalties?limit=200';
    const countUrl = driver ? `/api/penalties/count?driver_id=${driver.id}` : '/api/penalties/count';
    const [listRes, countRes] = await Promise.all([apiFetch(url), apiFetch(countUrl)]);
    if (!listRes.ok) throw new Error('failed');
    const penalties = await listRes.json();
    if (countRes.ok) {
      const { total } = await countRes.json();
      setPenaltiesTotal(total ?? 0);
    }
    if (!penalties.length) {
      penaltyList.innerHTML = '<li>No penalties yet.</li>';
      return;
    }
    penaltyList.innerHTML = penalties
      .map((item) => {
        const label = formatPenaltyLabel(item);
        const lapPart = item.lap != null && item.lap !== undefined ? ` · Lap ${item.lap}` : '';
        const descPart = item.description ? ` · ${item.description}` : '';
        const datePart = item.created_at ? ` · ${formatDate(item.created_at)}` : '';
        return `<li><strong>${label}</strong>${lapPart}${descPart}${datePart}</li>`;
      })
      .join('');
  } catch (err) {
    penaltyList.innerHTML = '<li>Unable to load penalties.</li>';
  }
};
