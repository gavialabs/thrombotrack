import { StateProvider } from "@/components/StateContext";
import Entypo from "@expo/vector-icons/Entypo";
import { Stack, useRouter } from "expo-router";
import { createContext } from "react";
import { TouchableOpacity, View, Text } from "react-native";
import { Image } from "expo-image";

import AnnotateHeader from "@/components/AnnotateHeader";

export default function RootLayout() {
  return (
    <StateProvider>
      <Stack>
        <Stack.Screen
          name="index"
          options={{
            title: "ECMO Thrombosis Tracker",
            header: () => (
              <View
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  height: 64,
                  backgroundColor: "white",
                  flexDirection: "row",
                  paddingHorizontal: 10,
                  borderBottomColor: "lightgray",
                  borderBottomWidth: 0.5,
                }}
              >
                <Image
                  source={require("../assets/images/uw-logo.png")}
                  style={{
                    width: 40,
                    aspectRatio: 1280 / 865,
                    marginRight: 40,
                  }}
                />
                <Text
                  style={{ fontSize: 16, textAlign: "center", fontWeight: 500 }}
                >
                  ECMO Thrombosis Tracker
                </Text>
                <Image
                  source={require("../assets/images/gavia-labs-logo.svg")}
                  style={{ width: 80, aspectRatio: 1526 / 486 }}
                />
              </View>
            ),
          }}
        />
        <Stack.Screen
          name="annotate"
          options={{
            title: "Annotate Image",
            header: () => <AnnotateHeader />,
          }}
        />
        <Stack.Screen
          name="chart"
          options={{
            title: "Chart",
          }}
        />
      </Stack>
    </StateProvider>
  );
}
