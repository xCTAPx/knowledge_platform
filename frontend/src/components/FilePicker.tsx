import { FILE_ACCEPT, pickFiles } from "../lib/files";
import { stopFileEnter } from "../lib/forms";

export function FilePicker({ disabled, onPick }: { disabled?: boolean; onPick: (files: File[]) => void }) {
  return (
    <label>
      Files
      <input
        type="file"
        accept={FILE_ACCEPT}
        multiple
        disabled={disabled}
        onKeyDown={stopFileEnter}
        onChange={(event) => {
          onPick(pickFiles(event.target.files));
          event.target.value = "";
        }}
      />
    </label>
  );
}
