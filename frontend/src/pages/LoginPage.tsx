import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../services/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await login(String(form.get("email")), String(form.get("password")));
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }

  return (
    <main className="shell">
      <Link to="/" className="brand">
        <span className="mark">K</span>
        <span className="brand-name">Knowledge</span>
      </Link>
      <section className="card">
        <h1>Welcome back</h1>
        <p className="lede">Sign in to open your library.</p>
        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            Email
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Password
            <input name="password" type="password" autoComplete="current-password" required />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button type="submit">Log in</button>
        </form>
        <p className="muted">
          No account? <Link to="/register">Create one</Link>
        </p>
      </section>
    </main>
  );
}
