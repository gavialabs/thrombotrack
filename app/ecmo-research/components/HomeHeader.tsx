// Header for home screen

import { Image } from "expo-image";
import { Text, StyleSheet, View } from "react-native";
import { FC, JSX } from "react";

// @ts-ignore
import uwLogo from "@/assets/images/uw-logo.png";
// @ts-ignore
import gaviaLabsLogo from "@/assets/images/gavia-labs-logo.svg";
import * as Colors from "@/constants/colors";

const HomeHeader: FC = (): JSX.Element => {
  return (
    <View style={styles.container}>
      <Image source={uwLogo} style={styles.uwLogo} />
      <Text style={styles.title}>ThromboTrack</Text>
      <Image source={gaviaLabsLogo} style={styles.gaviaLabsLogo} />
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
  uwLogo: {
    width: 40,
    aspectRatio: 1280 / 865,
    marginRight: 40,
  },
  title: {
    fontSize: 16,
    textAlign: "center",
    fontWeight: 600,
  },
  gaviaLabsLogo: { width: 80, aspectRatio: 1526 / 486 },
});

export default HomeHeader;
