import "./IndexStatus.css";

export function IndexStatus({ status }: { status: string }) {
  if (status === "ready") return null;
  const failed = status === "failed";
  return (
    <p className={failed ? "index-status failed" : "index-status"} role="status">
      {failed ? "Could not index" : "Indexing…"}
    </p>
  );
}
