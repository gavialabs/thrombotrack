// React Context for maintaining authentication state

import { apiFetch } from "@/api";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  FC,
  JSX,
  PropsWithChildren,
} from "react";

type AuthContextValue = {
  userId: string | null;
};

const AuthContext = createContext<AuthContextValue>({ userId: null });

export const AuthProvider: FC<PropsWithChildren> = ({
  children,
}): JSX.Element => {
  const [userId, setUserId] = useState<string | null>(null);

  /**
   * On app mount, fetches the current user ID.
   *
   * If logged in, user ID will be returned and stored in `user`. Otherwise, apiFetch will redirect
   * to the API to log in.
   */
  useEffect(() => {
    apiFetch("/auth/me")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setUserId(data?.user_id ?? null))
      .catch(() => setUserId(null));
  }, []);

  return (
    <AuthContext.Provider value={{ userId }}>{children}</AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
