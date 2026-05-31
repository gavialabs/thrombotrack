import { View, Text } from "react-native";
import { Image } from "expo-image";

const HomeHeader = () => {
  return (
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
        source={require("@/assets/images/uw-logo.png")}
        style={{
          width: 40,
          aspectRatio: 1280 / 865,
          marginRight: 40,
        }}
      />
      <Text style={{ fontSize: 16, textAlign: "center", fontWeight: 500 }}>
        ECMO Thrombosis Tracker
      </Text>
      <Image
        source={require("@/assets/images/gavia-labs-logo.svg")}
        style={{ width: 80, aspectRatio: 1526 / 486 }}
      />
    </View>
  );
};

export default HomeHeader;
