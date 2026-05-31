import { Stack } from "expo-router";

import { SessionProvider, useSession } from "@/contexts/authContext";
import HomeHeader from "@/components/HomeHeader";

export default function Root() {
  // Set up the auth context and render your layout inside of it.
  return (
    <SessionProvider>
      <RootNavigator />
    </SessionProvider>
  );
}

// Create a new component that can access the SessionProvider context later.
function RootNavigator() {
  const { session } = useSession();

  return (
    <Stack>
      <Stack.Protected guard={!!session}>
        <Stack.Screen name="(app)" options={{ headerShown: false }} />
      </Stack.Protected>

      <Stack.Protected guard={!session}>
        <Stack.Screen
          name="sign-in"
          options={{ header: () => <HomeHeader /> }}
        />
      </Stack.Protected>
    </Stack>
  );
}
