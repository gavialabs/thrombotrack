import React from "react";
import { TouchableOpacity, View, Text } from "react-native";
import Entypo from "@expo/vector-icons/Entypo";
import { useRouter } from "expo-router";

type ChartHeaderProps = {
  onFinish?: () => void;
};

const ChartHeader: React.FC<ChartHeaderProps> = ({
  onFinish,
}): React.JSX.Element => {
  const router = useRouter();

  return (
    <View
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: 50,
        // backgroundColor: "white",
        flexDirection: "row",
        paddingHorizontal: 20,
        // borderBottomColor: "lightgray",
        // borderBottomWidth: 0.5,
      }}
    >
      <TouchableOpacity
        style={{
          backgroundColor: "white",
          height: 35,
          width: 35,
          borderRadius: 20,
          shadowOpacity: 0.1,
          shadowRadius: 10,
          alignItems: "center",
          justifyContent: "center",
        }}
        onPress={() => router.back()}
      >
        <Entypo name="chevron-left" size={18} color="black" />
      </TouchableOpacity>
      <View
        style={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          gap: 8,
        }}
      >
        <Text
          style={{
            fontSize: 16,
            textAlign: "center",
            fontWeight: 600,
          }}
        >
          Chart
        </Text>
      </View>
      <TouchableOpacity
        style={{
          backgroundColor: "rgb(199, 199, 204)",
          height: 35,
          width: 35,
          borderRadius: 20,
          alignItems: "center",
          justifyContent: "center",
          opacity: 0,
        }}
        onPress={() => router.back()}
      >
        <Entypo name="chevron-left" size={18} color="black" />
      </TouchableOpacity>
    </View>
  );
};

export default ChartHeader;
