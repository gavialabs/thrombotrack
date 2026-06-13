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
  isLoading: boolean;
};

const AuthContext = createContext<AuthContextValue>({
  userId: null,
  isLoading: true,
});

export const AuthProvider: FC<PropsWithChildren> = ({
  children,
}): JSX.Element => {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [userId, setUserId] = useState<string | null>(null);

  /**
   * On app mount, fetches the current user ID.
   *
   * If logged in, user ID will be returned and stored in `user`. Otherwise, apiFetch will redirect
   * to the API to log in.
   */
  useEffect(() => {
    apiFetch("/auth/me")
      .then((data) => setUserId(data?.user_id ?? null))
      .catch(() => setUserId(null))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <AuthContext.Provider value={{ userId, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
