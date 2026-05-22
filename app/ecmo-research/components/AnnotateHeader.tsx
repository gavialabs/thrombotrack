import React from "react";
import { TouchableOpacity, View, Text } from "react-native";
import Entypo from "@expo/vector-icons/Entypo";
import { useRouter } from "expo-router";

type AnnotateHeaderProps = {
  onFinish?: () => void;
};

const AnnotateHeader: React.FC<AnnotateHeaderProps> = ({
  onFinish,
}): React.JSX.Element => {
  const router = useRouter();

  return (
    <View
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: 64,
        backgroundColor: "white",
        flexDirection: "row",
        paddingHorizontal: 20,
        borderBottomColor: "lightgray",
        borderBottomWidth: 0.5,
      }}
    >
      <TouchableOpacity
        style={{
          backgroundColor: "rgb(199, 199, 204)",
          height: 35,
          width: 35,
          borderRadius: 20,
          alignItems: "center",
          justifyContent: "center",
        }}
        onPress={() => router.back()}
      >
        <Entypo name="chevron-left" size={18} color="black" />
      </TouchableOpacity>
      <Text style={{ fontSize: 16, textAlign: "center", fontWeight: 500 }}>
        Annotate Image
      </Text>
      <TouchableOpacity
        style={{
          backgroundColor: "rgb(0, 136, 255)",
          height: 35,
          width: 35,
          borderRadius: 20,
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
        }}
        onPress={() => {
          if (onFinish !== undefined) {
            onFinish();
          }
        }}
      >
        <Entypo name="check" size={18} color="white" />
      </TouchableOpacity>
    </View>
  );
};

export default AnnotateHeader;
