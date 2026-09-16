import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../services/api";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const age = form.get("age");
    try {
      await register(
        String(form.get("nickname")),
        String(form.get("email")),
        String(form.get("password")),
        age ? Number(age) : null
      );
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  }

  return (
    <main className="shell">
      <Link to="/" className="brand">
        <span className="mark">K</span>
        <span className="brand-name">Knowledge</span>
      </Link>
      <section className="card">
        <h1>Create your library</h1>
        <p className="lede">A few details and you can start collecting knowledge.</p>
        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            Nickname
            <input name="nickname" autoComplete="nickname" required />
          </label>
          <label>
            Email
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Password
            <input name="password" type="password" autoComplete="new-password" minLength={8} required />
          </label>
          <label>
            Age (optional)
            <input name="age" type="number" min={1} max={150} />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button type="submit">Create account</button>
        </form>
        <p className="muted">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </section>
    </main>
  );
}
