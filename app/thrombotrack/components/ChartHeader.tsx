// Header for annotate screen

import Entypo from "@expo/vector-icons/Entypo";
import { useRouter } from "expo-router";
import { FC, JSX } from "react";
import { TouchableOpacity, View, Text, StyleSheet } from "react-native";

import * as Colors from "@/constants/colors";

const ChartHeader: FC = (): JSX.Element => {
  const router = useRouter();

  // Go back.
  const doPressBack = (): void => {
    router.back();
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity onPress={doPressBack} style={styles.backButton}>
        <Entypo name="chevron-left" size={18} color={Colors.GRAY} />
      </TouchableOpacity>

      <View style={styles.titleContainer}>
        <Text style={styles.title}>Annotation History</Text>
      </View>

      {/* hidden view of same width to center title */}
      <View style={[styles.backButton, { opacity: 0 }]} />
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
  },
  title: {
    fontSize: 16,
    textAlign: "center",
    fontWeight: 600,
  },
});

export default ChartHeader;
