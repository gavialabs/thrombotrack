import Entypo from "@expo/vector-icons/Entypo";
import { Stack } from "expo-router";
import { TouchableOpacity } from "react-native";

export default function RootLayout() {
  return (
    <Stack>
      <Stack.Screen
        name="index"
        options={{ title: "ECMO Thrombosis Tracker" }}
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
              }}
            >
              <Entypo name="check" size={18} color="white" />
            </TouchableOpacity>
          ),
        }}
      />
    </Stack>
  );
}
