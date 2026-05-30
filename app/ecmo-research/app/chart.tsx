import { useGlobalSearchParams } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  View,
  Dimensions,
  useWindowDimensions,
  StyleSheet,
  Text,
} from "react-native";
import { LineChart } from "react-native-gifted-charts";
import moment from "moment";

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get("window");

const redData = [
  { value: 42, date: "Jan 3" },
  { value: 58, date: "Jan 17" },
  { value: 53, date: "Feb 1" },
  { value: 71, date: "Feb 14" },
  { value: 68, date: "Mar 2" },
  { value: 85, date: "Mar 19" },
  { value: 79, date: "Apr 4" },
  { value: 94, date: "Apr 22" },
];

const blueData = [
  { value: 30, date: "Jan 3" },
  { value: 38, date: "Jan 17" },
  { value: 44, date: "Feb 1" },
  { value: 40, date: "Feb 14" },
  { value: 55, date: "Mar 2" },
  { value: 60, date: "Mar 19" },
  { value: 58, date: "Apr 4" },
  { value: 72, date: "Apr 22" },
];

const blackData = [
  { value: 15, date: "Jan 3" },
  { value: 22, date: "Jan 17" },
  { value: 18, date: "Feb 1" },
  { value: 30, date: "Feb 14" },
  { value: 27, date: "Mar 2" },
  { value: 35, date: "Mar 19" },
  { value: 42, date: "Apr 4" },
  { value: 38, date: "Apr 22" },
];

const CHART_COLOR_RED = "#E05252";
const CHART_COLOR_BLUE = "#4A90D9";
const CHART_COLOR_BLACK = "#2C2C2C";
const AXIS_COLOR = "#9CA3AF";
const GRID_COLOR = "#F3F4F6";
const BG_COLOR = "#FAFAF9";
const CARD_BG = "#FFFFFF";
const Y_AXIS_LABEL_WIDTH = 16;
const CHART_WIDTH = SCREEN_WIDTH - 48;
const CHART_HEIGHT = SCREEN_HEIGHT * 0.52;

const LegendDot: React.FC = ({ color }) => {
  return <View style={[styles.legendDot, { backgroundColor: color }]} />;
};

export default function Chart() {
  const { ecmoId } = useGlobalSearchParams<{ ecmoId: string }>();
  const [data, setData] = useState([]);
  const { height, width } = useWindowDimensions();

  const chartWidth = width - 48;
  const chartHeight = height * 0.52;

  const formattedRed = redData.map((d, i) => ({
    value: d.value,
    dataPointColor: CHART_COLOR_RED,
    dataPointRadius: 5,
    customDataPoint: undefined,
    label: d.date,
    // labelTextStyle: styles.xLabel,
    hideDataPoint: false,
  }));

  const formattedBlue = blueData.map((d) => ({
    value: d.value,
    dataPointColor: CHART_COLOR_BLUE,
    dataPointRadius: 5,
  }));

  const formattedBlack = blackData.map((d) => ({
    value: d.value,
    dataPointColor: CHART_COLOR_BLACK,
    dataPointRadius: 5,
  }));

  // useEffect(() => {
  //   fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmos/${ecmoId}/history`)
  //     .then((response) => response.json())
  //     .then((json) => {
  //       console.log(json);
  //       setData(
  //         json.map((item) => ({
  //           label: moment(item.created_at).local().format("M/D/YY"),
  //           value: item.total_area,
  //         })),
  //       );
  //     })
  //     .catch((error) => console.error(error));
  // }, [ecmoId]);

  // return (
  //   <View style={{ padding: 20 }}>
  //     <LineChart
  //       data={data}
  //       width={290}
  //       color1="red"
  //       xAxisLabelTextStyle={{
  //         fontSize: 12,
  //         transform: "rotate(45deg)",
  //         marginTop: 10,
  //         marginLeft: 20,
  //         overflow: "visible",
  //         color: "gray",
  //       }}
  //     />
  //   </View>
  // );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerLabel}>LONGITUDINAL ASSESSMENT</Text>
        <Text style={styles.title}>Thrombosis Burden</Text>
        <Text style={styles.subtitle}>Multi-cohort tracking over time</Text>
      </View>

      {/* Chart card */}
      <View style={styles.card}>
        {/* Y-axis rotated label */}
        <View style={styles.yAxisLabelContainer}>
          <Text style={styles.yAxisLabel}>Thrombosis Burden (mm²)</Text>
        </View>

        {/* Chart area */}
        <View style={styles.chartArea}>
          <LineChart
            data={formattedRed}
            data2={formattedBlue}
            data3={formattedBlack}
            width={chartWidth - Y_AXIS_LABEL_WIDTH - 32}
            height={chartHeight}
            // Colors
            color1={CHART_COLOR_RED}
            color2={CHART_COLOR_BLUE}
            color3={CHART_COLOR_BLACK}
            // Line thickness
            thickness1={2.5}
            thickness2={2.5}
            thickness3={2.5}
            // Data points
            dataPointsColor1={CHART_COLOR_RED}
            dataPointsColor2={CHART_COLOR_BLUE}
            dataPointsColor3={CHART_COLOR_BLACK}
            dataPointsRadius1={5}
            dataPointsRadius2={5}
            dataPointsRadius3={5}
            dataPointsWidth={2}
            // Axes
            xAxisColor={AXIS_COLOR}
            yAxisColor={AXIS_COLOR}
            yAxisTextStyle={styles.yAxisText}
            xAxisLabelTextStyle={styles.xLabel}
            // Grid
            rulesColor={GRID_COLOR}
            rulesType="solid"
            noOfSections={5}
            // Spacing
            spacing={Math.floor(
              (chartWidth - Y_AXIS_LABEL_WIDTH - 80) / (redData.length - 1),
            )}
            initialSpacing={20}
            endSpacing={20}
            // Y axis
            yAxisOffset={0}
            maxValue={110}
            stepValue={20}
            yAxisLabelWidth={36}
            // Background
            backgroundColor={CARD_BG}
            // Curve style — straight lines connecting dots
            curved={false}
            // Hide the area fill under lines
            areaChart={false}
            // Pointer config
            hideDataPoints1={false}
            hideDataPoints2={false}
            hideDataPoints3={false}
            // Dot inner circle (white center for visibility)
            dataPointsShape="circular"
            focusEnabled
            showStripOnFocus
          />
        </View>
      </View>

      {/* Legend */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <LegendDot color={CHART_COLOR_RED} />
          <Text style={styles.legendText}>Cohort A</Text>
        </View>
        <View style={styles.legendSep} />
        <View style={styles.legendItem}>
          <LegendDot color={CHART_COLOR_BLUE} />
          <Text style={styles.legendText}>Cohort B</Text>
        </View>
        <View style={styles.legendSep} />
        <View style={styles.legendItem}>
          <LegendDot color={CHART_COLOR_BLACK} />
          <Text style={styles.legendText}>Cohort C</Text>
        </View>
      </View>

      {/* Footer note */}
      <Text style={styles.footerNote}>
        Data points represent mean burden per imaging session
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: BG_COLOR,
  },
  container: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 12,
    backgroundColor: BG_COLOR,
  },

  // Header
  header: {
    marginBottom: 20,
  },
  headerLabel: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 2.5,
    color: AXIS_COLOR,
    marginBottom: 4,
  },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: "#111827",
    letterSpacing: -0.5,
    marginBottom: 2,
  },
  subtitle: {
    fontSize: 13,
    color: AXIS_COLOR,
    fontWeight: "400",
  },

  // Card
  card: {
    backgroundColor: CARD_BG,
    borderRadius: 16,
    paddingTop: 20,
    paddingBottom: 12,
    paddingRight: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 12,
    elevation: 3,
    flexDirection: "row",
    alignItems: "center",
  },

  // Y-axis rotated label
  yAxisLabelContainer: {
    width: 20,
    height: CHART_HEIGHT,
    justifyContent: "center",
    alignItems: "center",
  },
  yAxisLabel: {
    fontSize: 10,
    fontWeight: "600",
    color: AXIS_COLOR,
    letterSpacing: 0.4,
    transform: [{ rotate: "-90deg" }],
    width: CHART_HEIGHT,
    textAlign: "center",
  },

  chartArea: {
    flex: 1,
    overflow: "hidden",
  },

  // Axis labels
  yAxisText: {
    fontSize: 11,
    color: AXIS_COLOR,
    fontWeight: "500",
  },
  xLabel: {
    fontSize: 10,
    color: AXIS_COLOR,
    fontWeight: "500",
    marginTop: 4,
  },

  // Legend
  legend: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    marginTop: 18,
    marginBottom: 8,
    backgroundColor: CARD_BG,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 1,
  },
  legendItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  legendText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#374151",
    letterSpacing: 0.2,
  },
  legendSep: {
    width: 1,
    height: 14,
    backgroundColor: GRID_COLOR,
    marginHorizontal: 16,
  },

  // Footer
  footerNote: {
    fontSize: 11,
    color: "#D1D5DB",
    textAlign: "center",
    marginTop: 4,
    letterSpacing: 0.2,
  },
});
