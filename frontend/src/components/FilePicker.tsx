import { FILE_ACCEPT, pickFiles } from "../lib/files";

export function FilePicker({ disabled, onPick }: { disabled?: boolean; onPick: (files: File[]) => void }) {
  return (
    <label>
      Files
      <input
        type="file"
        accept={FILE_ACCEPT}
        multiple
        disabled={disabled}
        onChange={(event) => {
          onPick(pickFiles(event.target.files));
          event.target.value = "";
        }}
      />
    </label>
  );
}
