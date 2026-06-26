// Entrypoint for logged-in users.

import { Stack } from "expo-router";
import { FC, JSX } from "react";

import AnnotateHeader from "@/components/AnnotateHeader";
import ChartHeader from "@/components/ChartHeader";
import HomeHeader from "@/components/HomeHeader";
import GalleryHeader from "@/components/GalleryHeader";
import { StateProvider } from "@/context/StateContext";

// Navigation stack of the actual app content for logged-in users.
const LoggedInLayout: FC = (): JSX.Element => (
  <StateProvider>
    <Stack
      screenOptions={{
        contentStyle: {
          backgroundColor: "#f2f2f2",
          marginTop: 50,
        },
      }}
    >
      <Stack.Screen
        name="index"
        options={{
          header: () => <HomeHeader />,
        }}
      />
      <Stack.Screen
        name="annotate"
        options={{
          header: () => <AnnotateHeader />,
        }}
      />
      <Stack.Screen
        name="chart"
        options={{
          header: () => <ChartHeader />,
        }}
      />
      <Stack.Screen
        name="gallery"
        options={{
          header: () => <GalleryHeader />,
        }}
      />
    </Stack>
  </StateProvider>
);

export default LoggedInLayout;
