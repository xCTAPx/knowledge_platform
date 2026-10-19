import { useEffect, useState } from "react";
import { getMe, logout, type User } from "../services/api";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  async function onLogout() {
    await logout().catch(() => undefined);
    setUser(null);
  }

  return { user, onLogout };
}
