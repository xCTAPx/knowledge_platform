import "./SearchBox.css";

export function SearchBox({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <form
      className="search"
      onSubmit={(event) => {
        event.preventDefault();
        event.stopPropagation();
      }}
    >
      <label>
        Search
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Name, note content, or attached file"
        />
      </label>
    </form>
  );
}
