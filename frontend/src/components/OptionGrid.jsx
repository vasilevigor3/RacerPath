const OptionGrid = ({ name, options }) => (
  <div className="option-grid">
    {options.map((option) => (
      <label className="option-pill" key={option.value}>
        <input type="checkbox" name={name} value={option.value} />
        {option.label}
      </label>
    ))}
  </div>
);

export default OptionGrid;
