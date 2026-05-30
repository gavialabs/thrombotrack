import React from "react";
import { TouchableOpacity, View, Text } from "react-native";
import Entypo from "@expo/vector-icons/Entypo";
import { useRouter } from "expo-router";

const INSTRUCTION_TEXT =
  '• Use two fingers to zoom or pan.\n• Make sure to set the annotation type to "Clot" or "Fibrin" at the top.\n• Use one finger to tap on a clot or fibrin, or draw a circle around an area. You can circle multiple clots/fibrin strands at once.\n• Use the eraser tool to refine results, or use the undo/redo/clear buttons to remove annotations.\n• Press "Save" when finished to calculate results.';

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
            fontWeight: 500,
            marginLeft: 28,
          }}
        >
          Annotate Image
        </Text>
        <TouchableOpacity
          onPress={() => window.alert(INSTRUCTION_TEXT)}
          style={{
            backgroundColor: "rgb(199, 199, 204)",
            width: 20,
            height: 20,
            borderRadius: 10,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Text
            style={{ fontWeight: "800", color: "white", textAlign: "center" }}
          >
            ?
          </Text>
        </TouchableOpacity>
      </View>
      <TouchableOpacity
        style={{
          backgroundColor: "rgb(0, 136, 255)",
          padding: 10,
          paddingHorizontal: 15,
          borderRadius: 20,
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0px 0px 10px 0px rgba(0,136,255,0.1)",
        }}
        onPress={() => {
          if (onFinish !== undefined) {
            onFinish();
          }
        }}
      >
        <Text style={{ color: "white", fontWeight: 600 }}>Save</Text>
      </TouchableOpacity>
    </View>
  );
};

export default AnnotateHeader;
