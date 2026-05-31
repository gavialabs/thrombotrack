import { router } from "expo-router";
import { Text, TouchableOpacity, View } from "react-native";

import { useSession } from "@/contexts/authContext";

export default function SignIn() {
  const { signIn, signInAsTestUser } = useSession();
  return (
    <View
      style={{
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
        gap: 20,
      }}
    >
      <TouchableOpacity
        style={{
          width: 200,
          backgroundColor: "rgb(0, 136, 255)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          paddingVertical: 12,
          borderRadius: 30,
          boxShadow: "0px 0px 10px 0px rgba(0, 136, 255, 0.1)",
        }}
        onPress={() => {
            signIn();
            // Navigate after signing in. You may want to tweak this to ensure sign-in is successful before navigating.
            router.replace("/");
          }}
      >
        <Text
          style={{
            color: "white",
            fontSize: 16,
            fontWeight: "600",
          }}
        >
          Sign In
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={{
          width: 200,
          backgroundColor: "rgb(209, 209, 214)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          paddingVertical: 12,
          borderRadius: 30,
        }}
        onPress={() => {
          signInAsTestUser();
          router.replace("/");
        }}
      >
        <Text
          style={{
            color: "rgb(142, 142, 147)",
            fontSize: 16,
            fontWeight: "600",
          }}
        >
          Test User
        </Text>
      </TouchableOpacity>
    </View>
  );
}
