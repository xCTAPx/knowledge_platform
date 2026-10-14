import { Link } from "react-router-dom";
import { Brand } from "../components/Brand";

export function Landing() {
  return (
    <main className="shell">
      <Brand />
      <h1>A quiet place for what you know.</h1>
      <p className="lede">Keep notes, ideas, and references in one calm library.</p>
      <div className="actions">
        <Link className="button" to="/login">
          Log in
        </Link>
        <Link className="button ghost" to="/register">
          Create account
        </Link>
      </div>
    </main>
  );
}
