import "./UploadStatus.css";

export function UploadStatus({ text }: { text: string }) {
  return (
    <p className="upload-status" role="status">
      <span className="spinner" aria-hidden />
      {text}
    </p>
  );
}
