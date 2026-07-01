// Header for annotate screen

import Entypo from "@expo/vector-icons/Entypo";
import { useGlobalSearchParams, useRouter } from "expo-router";
import { FC, JSX } from "react";
import { TouchableOpacity, View, Text, StyleSheet } from "react-native";

import * as Colors from "@/constants/colors";

const INSTRUCTION_TEXT =
  '• Use two fingers to zoom or pan.\n• Make sure to set the annotation type to "Clot" or "Fibrin" at the top.\n• Use one finger to tap on a clot or fibrin, or draw a circle around an area. You can circle multiple clots/fibrin strands at once.\n• Use the eraser tool to refine results, or use the undo/redo/clear buttons to remove annotations.\n• Press "Save" when finished to calculate results.';

type AnnotateHeaderProps = {
  disabled?: boolean;
  onFinish?: () => void;
  isCroppingImage: boolean;
};

const AnnotateHeader: FC<AnnotateHeaderProps> = ({
  disabled,
  onFinish,
  isCroppingImage,
}): JSX.Element => {
  const router = useRouter();
  const { oxygenatorId } = useGlobalSearchParams<{ oxygenatorId: string }>();

  // Go back.
  const doPressBack = (): void => {
    router.navigate({
      pathname: "/gallery",
      params: { oxygenatorId },
    });
  };

  const doPressSave = (): void => {
    if (onFinish !== undefined && (isCroppingImage || !disabled)) {
      onFinish();
    }
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity onPress={doPressBack} style={styles.backButton}>
        <Entypo name="chevron-left" size={18} color={Colors.GRAY} />
      </TouchableOpacity>

      <View style={styles.titleContainer}>
        <Text style={styles.title}>
          {isCroppingImage ? "Crop" : disabled ? "View" : "Annotate"} Image
        </Text>
        {!disabled ? (
          <TouchableOpacity
            onPress={() => window.alert(INSTRUCTION_TEXT)}
            style={styles.helpButton}
          >
            <Text style={styles.help}>?</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      <TouchableOpacity
        onPress={doPressSave}
        style={[
          styles.saveButton,
          { opacity: isCroppingImage ? 1 : disabled ? 0 : 1 },
        ]}
      >
        <Text style={styles.save}>Save</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.BG,
    position: "fixed",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    height: 50,
    width: "100%",
    flexDirection: "row",
    paddingHorizontal: 20,
  },
  backButton: {
    backgroundColor: Colors.GRAY_4,
    height: 35,
    width: 35,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    boxShadow: `0 0 10px 0 ${Colors.BLACK}1a`,
  },
  titleContainer: {
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginLeft: 35,
  },
  title: {
    fontSize: 16,
    textAlign: "center",
    fontWeight: 600,
  },
  helpButton: {
    backgroundColor: Colors.GRAY_4,
    width: 20,
    height: 20,
    borderRadius: 10,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  help: { fontWeight: "800", color: Colors.GRAY, textAlign: "center" },
  saveButton: {
    backgroundColor: Colors.BLUE,
    padding: 10,
    paddingHorizontal: 15,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    boxShadow: `0 0 10px 0 ${Colors.BLUE}1a`,
  },
  save: { color: "white", fontWeight: 600 },
});

export default AnnotateHeader;
