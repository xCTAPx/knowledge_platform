import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMe, logout, type User } from "../services/api";

export default function HomePage() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    getMe().then(setUser).catch(() => setUser(null));
  }, []);

  async function onLogout() {
    await logout().catch(() => undefined);
    setUser(null);
  }

  return (
    <main className="shell">
      <div className="brand">
        <span className="mark">K</span>
        <span className="brand-name">Knowledge</span>
      </div>
      <h1>A quiet place for what you know.</h1>
      {user ? (
        <>
          <p className="lede">
            Signed in as <strong>{user.nickname}</strong> · {user.email}
          </p>
          <div className="actions">
            <button type="button" className="ghost" onClick={onLogout}>
              Log out
            </button>
          </div>
        </>
      ) : (
        <>
          <p className="lede">Keep notes, ideas, and references in one calm library.</p>
          <div className="actions">
            <Link className="button" to="/login">
              Log in
            </Link>
            <Link className="button ghost" to="/register">
              Create account
            </Link>
          </div>
        </>
      )}
    </main>
  );
}
