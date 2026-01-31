import { DISCIPLINES } from '../constants/uiData.js';

const DisciplineSelect = ({ id, name, includeKeepCurrent = false, defaultValue = 'gt' }) => (
  <select id={id} name={name} defaultValue={defaultValue}>
    {includeKeepCurrent && <option value="">Keep current</option>}
    {DISCIPLINES.map((discipline) => (
      <option key={discipline.value} value={discipline.value}>
        {discipline.label}
      </option>
    ))}
  </select>
);

export default DisciplineSelect;
