// Entrypoint into Expo web app

import { Stack } from "expo-router";

import { AuthProvider, useAuth } from "@/context/AuthContext";
import HomeHeader from "@/components/HomeHeader";
import { FC, JSX } from "react";

/**
 * Entrypoint to app.
 *
 * @returns RootNavigator wrapped in AuthProvider so it has access to `user`.
 */
const Root: FC = (): JSX.Element => {
  return (
    <AuthProvider>
      <RootNavigator />
    </AuthProvider>
  );
};

/**
 * Top-level navigation stack to protect routes requiring authentication.
 *
 * @returns Expo Navigation Stack containing logged out page and nested stack of real app pages.
 */
const RootNavigator: FC = (): JSX.Element => {
  const { userId } = useAuth();

  return (
    <Stack>
      {/* logged out users (when `userId` is not set) will be shown a dummy page */}
      <Stack.Protected guard={userId === null}>
        <Stack.Screen
          name="sign-in"
          options={{ header: () => <HomeHeader /> }}
        />
      </Stack.Protected>

      {/* logged in users (when `userId` is set) will have access to the app pages */}
      <Stack.Protected guard={userId !== null}>
        <Stack.Screen name="(app)" options={{ headerShown: false }} />
      </Stack.Protected>
    </Stack>
  );
};

export default Root;
