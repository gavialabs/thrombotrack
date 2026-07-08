// Entrypoint into Expo web app

import { Stack } from "expo-router";
import { FC, JSX } from "react";

import { AuthProvider, useAuth } from "@/context/AuthContext";
import HomeHeader from "@/components/HomeHeader";
import ScrollToTop from "@/components/ScrollToTop";

/**
 * Entrypoint to app.
 *
 * @returns RootNavigator wrapped in AuthProvider so it has access to `user`.
 */
const Root: FC = (): JSX.Element => {
  return (
    <AuthProvider>
      <ScrollToTop />
      <RootNavigator />
    </AuthProvider>
  );
};

/**
 * Top-level navigation stack to protect routes requiring authentication.
 *
 * @returns Expo Navigation Stack containing logged out page and nested stack of real app pages.
 */
const RootNavigator: FC = (): JSX.Element | null => {
  const { userId, isLoading } = useAuth();

  if (isLoading) {
    // return null while we are loading the auth state in useAuth. this fixes an issue where we
    // always redirect to the homepage when refreshing since userId is set to null while loading
    return null;
  }

  return (
    <Stack
      screenOptions={{
        contentStyle: {
          backgroundColor: "transparent",
        },
      }}
    >
      {/* logged out users (when `userId` is not set) will be shown a dummy page */}
      <Stack.Protected guard={userId === null}>
        <Stack.Screen
          name="sign-in"
          options={{ header: () => <HomeHeader /> }}
        />
      </Stack.Protected>

      {/* logged in users (when `userId` is set) will have access to the app pages */}
      <Stack.Protected guard={userId !== null}>
        <Stack.Screen name="(logged-in)" options={{ headerShown: false }} />
      </Stack.Protected>
    </Stack>
  );
};

export default Root;