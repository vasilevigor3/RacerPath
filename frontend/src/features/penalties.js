import { apiFetch } from '../api/client.js';

const penaltyList = document.querySelector('[data-penalty-list]');
const penaltyScrollEl = document.querySelector('[data-penalty-scroll]');
const penaltiesTotalEls = document.querySelectorAll('[data-penalties-total], [data-penalties-total-card]');
const penaltiesListView = document.querySelector('[data-penalties-list-view]');
const penaltyDetailPanel = document.querySelector('[data-penalty-detail]');
const penaltyDetailType = document.querySelector('[data-penalty-detail-type]');
const penaltyDetailRace = document.querySelector('[data-penalty-detail-race]');
const penaltyDetailMeta = document.querySelector('[data-penalty-detail-meta]');
const penaltyDetailDesc = document.querySelector('[data-penalty-detail-desc]');
const penaltyDetailBack = document.querySelector('[data-penalty-detail-back]');

let penaltiesCache = [];
let penaltiesTotalCount = 0;
let penaltyLoadingMore = false;
let lastPenaltiesDriver = null;
const PENALTY_PAGE_SIZE = 3;
let penaltyDisplayLimit = PENALTY_PAGE_SIZE;

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

function showPenaltyDetail(item) {
  if (!penaltyDetailPanel || !penaltyDetailType || !penaltyDetailRace || !penaltyDetailMeta) return;
  const label = formatPenaltyLabel(item);
  penaltyDetailType.textContent = label;
  penaltyDetailRace.textContent = item.event_title ? `Race: ${item.event_title}` : '—';
  const metaParts = [];
  if (item.lap != null && item.lap !== undefined) metaParts.push(`Lap ${item.lap}`);
  if (item.event_start_time_utc) metaParts.push(formatDate(item.event_start_time_utc));
  if (item.created_at) metaParts.push(`Recorded: ${formatDate(item.created_at)}`);
  penaltyDetailMeta.textContent = metaParts.length ? metaParts.join(' · ') : '—';
  penaltyDetailDesc.textContent = item.description || '';
  penaltyDetailDesc.style.display = item.description ? '' : 'none';
  if (penaltiesListView) penaltiesListView.classList.add('is-hidden');
  penaltyDetailPanel.classList.remove('is-hidden');
}

function hidePenaltyDetail() {
  if (penaltyDetailPanel) penaltyDetailPanel.classList.add('is-hidden');
  if (penaltiesListView) penaltiesListView.classList.remove('is-hidden');
}

function renderPenaltyCard(item) {
  const label = formatPenaltyLabel(item);
  const race = item.event_title || '—';
  const lapHtml = item.lap != null && item.lap !== undefined
    ? `<span class="penalty-card__lap">Lap ${item.lap}</span>`
    : '';
  return `<button type="button" class="penalty-card" data-penalty-id="${item.id}" role="listitem">
    <span class="penalty-card__type">${label}</span>
    <span class="penalty-card__race">${race}</span>
    ${lapHtml}
  </button>`;
}

function renderPenaltiesSlice(from, to) {
  const slice = penaltiesCache.slice(from, to);
  return slice.map((item) => renderPenaltyCard(item)).join('');
}

async function resetPenaltiesToFirstPage() {
  penaltyDisplayLimit = PENALTY_PAGE_SIZE;
  if (!penaltyList || !lastPenaltiesDriver) return;
  try {
    const url = `/api/penalties?driver_id=${lastPenaltiesDriver.id}&limit=${PENALTY_PAGE_SIZE}&offset=0`;
    const res = await apiFetch(url);
    if (!res.ok) return;
    const page = await res.json();
    penaltiesCache = page;
    penaltyList.innerHTML = page.length ? page.map((item) => renderPenaltyCard(item)).join('') : '<div role="listitem">No penalties yet.</div>';
    if (penaltyScrollEl) penaltyScrollEl.scrollTop = 0;
  } catch (_) {}
}

async function fetchPenaltiesNextPage() {
  if (!lastPenaltiesDriver || penaltyLoadingMore || penaltiesCache.length >= penaltiesTotalCount) return;
  penaltyLoadingMore = true;
  const offset = penaltiesCache.length;
  try {
    const url = `/api/penalties?driver_id=${lastPenaltiesDriver.id}&limit=${PENALTY_PAGE_SIZE}&offset=${offset}`;
    const res = await apiFetch(url);
    if (!res.ok) return;
    const page = await res.json();
    penaltiesCache.push(...page);
    const html = page.map((item) => renderPenaltyCard(item)).join('');
    if (penaltyList && html) penaltyList.insertAdjacentHTML('beforeend', html);
    penaltyDisplayLimit = penaltiesCache.length;
  } finally {
    penaltyLoadingMore = false;
  }
}

function setupPenaltyScrollLoad() {
  if (!penaltyScrollEl || !penaltyList) return;
  penaltyScrollEl.addEventListener('scroll', () => {
    const { scrollTop, clientHeight, scrollHeight } = penaltyScrollEl;
    if (scrollHeight <= clientHeight) return;
    if (scrollTop + clientHeight < scrollHeight - 30) return;
    if (penaltiesCache.length >= penaltiesTotalCount) return;
    fetchPenaltiesNextPage();
  });
}
setupPenaltyScrollLoad();

window.addEventListener('cabinet-tab-change', (e) => {
  if (e.detail?.tab === 'risk-flags') resetPenaltiesToFirstPage();
});

function setupPenaltyDetailListeners() {
  if (penaltyList) {
    penaltyList.addEventListener('click', (e) => {
      const card = e.target.closest('[data-penalty-id]');
      if (!card) return;
      const id = card.getAttribute('data-penalty-id');
      const item = penaltiesCache.find((p) => p.id === id);
      if (item) showPenaltyDetail(item);
    });
  }
  if (penaltyDetailBack) {
    penaltyDetailBack.addEventListener('click', hidePenaltyDetail);
  }
}

setupPenaltyDetailListeners();

export const loadPenalties = async (driver) => {
  if (!penaltyList) return;
  penaltyList.innerHTML = '<div role="listitem" class="penalty-cards__loading">Loading...</div>';
  setPenaltiesTotal(0);
  penaltiesCache = [];
  penaltiesTotalCount = 0;
  lastPenaltiesDriver = driver || null;
  try {
    const countUrl = driver ? `/api/penalties/count?driver_id=${driver.id}` : '/api/penalties/count';
    const listUrl = driver ? `/api/penalties?driver_id=${driver.id}&limit=${PENALTY_PAGE_SIZE}&offset=0` : `/api/penalties?limit=${PENALTY_PAGE_SIZE}&offset=0`;
    const [countRes, listRes] = await Promise.all([apiFetch(countUrl), apiFetch(listUrl)]);
    if (!listRes.ok) throw new Error('failed');
    const penalties = await listRes.json();
    penaltiesCache = penalties;
    penaltyDisplayLimit = penalties.length;
    if (countRes.ok) {
      const { total } = await countRes.json();
      penaltiesTotalCount = total ?? 0;
      setPenaltiesTotal(penaltiesTotalCount);
    }
    if (!penalties.length) {
      penaltyList.innerHTML = '<div role="listitem">No penalties yet.</div>';
      return;
    }
    penaltyList.innerHTML = penalties.map((item) => renderPenaltyCard(item)).join('');
  } catch (err) {
    penaltyList.innerHTML = '<div role="listitem">Unable to load penalties.</div>';
  }
};
