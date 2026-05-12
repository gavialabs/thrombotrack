import { StateProvider } from "@/components/StateContext";
import Entypo from "@expo/vector-icons/Entypo";
import { Stack, useRouter } from "expo-router";
import { createContext } from "react";
import { TouchableOpacity, View, Text } from "react-native";
import { Image } from "expo-image";

export default function RootLayout() {
  const router = useRouter();

  return (
    <StateProvider>
      <Stack>
        <Stack.Screen
          name="index"
          options={{
            title: "ECMO Thrombosis Tracker",
            header: (props) => (
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
            headerStyle: { textAlign: "center" },
            headerTitle: "Annotate Image",
            headerLeft: () => (
              <TouchableOpacity
                style={{
                  backgroundColor: "rgb(199, 199, 204)",
                  height: 35,
                  width: 35,
                  borderRadius: 20,
                  alignItems: "center",
                  justifyContent: "center",
                  marginHorizontal: 10,
                }}
                onPress={() => router.back()}
              >
                <Entypo name="chevron-left" size={18} color="black" />
              </TouchableOpacity>
            ),
            headerRight: () => (
              <TouchableOpacity
                style={{
                  backgroundColor: "rgb(0, 136, 255)",
                  height: 35,
                  width: 35,
                  borderRadius: 20,
                  alignItems: "center",
                  justifyContent: "center",
                  marginRight: 10,
                  // boxShadow:
                  //   "0 0 40px -10px rgba(0,0,0,.3), 0 0 25px -15px rgba(0,0,0,.2);",
                  boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
                }}
              >
                <Entypo name="check" size={18} color="white" />
              </TouchableOpacity>
            ),
          }}
        />
      </Stack>
    </StateProvider>
  );
}
