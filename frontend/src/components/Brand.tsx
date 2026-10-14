import { Link } from "react-router-dom";

export function Brand({ to }: { to?: string }) {
  const inner = (
    <>
      <span className="mark">K</span>
      <span className="brand-name">Knowledge</span>
    </>
  );
  return to ? (
    <Link to={to} className="brand">
      {inner}
    </Link>
  ) : (
    <div className="brand">{inner}</div>
  );
}
