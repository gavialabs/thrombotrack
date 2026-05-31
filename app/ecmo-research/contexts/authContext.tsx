import { use, createContext, type PropsWithChildren } from "react";

import { useStorageState } from "@/hooks/useStorageState";
import { useAzureAuth } from "@/hooks/useAzureAuth";

const AuthContext = createContext<{
  signIn: () => void;
  signInAsTestUser: () => void;
  signOut: () => void;
  session?: string | null;
  isLoading: boolean;
} | null>(null);

// Use this hook to access the user info.
export function useSession() {
  const value = use(AuthContext);
  if (!value) {
    throw new Error("useSession must be wrapped in a <SessionProvider />");
  }

  return value;
}

export function SessionProvider({ children }: PropsWithChildren) {
  const [[isLoading, session], setSession] = useStorageState("session");
  const { login, loginTest } = useAzureAuth();

  return (
    <AuthContext.Provider
      value={{
        signIn: async () => {
          const accessToken = await login();

          if (accessToken !== null) {
            setSession(accessToken);
          } else {
            window.alert("There was a problem signing in");
          }
        },
        signInAsTestUser: async () => {
          const accessToken = await loginTest();
          setSession(accessToken);
        },
        signOut: () => {
          setSession(null);
        },
        session,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
