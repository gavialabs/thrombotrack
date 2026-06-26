// Annotation history chart

import { useGlobalSearchParams } from "expo-router";
import moment from "moment";
import React, { FC, JSX, useEffect, useState } from "react";
import { View, useWindowDimensions, StyleSheet, Text } from "react-native";
import { LineChart } from "react-native-gifted-charts";

import { apiFetch } from "@/api";
import { AnnotationSession } from "@/constants/types";
import * as Colors from "@/constants/colors";

// Displays a line chart with annotation history of clot area, fibrin area, and total.
const ChartScreen: FC = (): JSX.Element => {
  const { oxygenatorId } = useGlobalSearchParams<{ oxygenatorId: string }>();
  const [data, setData] = useState<AnnotationSession[]>([]);
  const { height, width } = useWindowDimensions();

  const chartHeight = height * 0.5;
  const chartWidth = width - 80; // subtracts padding/y-axis label width

  const units = data.some((d) => d.clot_area > 10 || d.fibrin_area > 10)
    ? "cm"
    : "mm";
  const totalData = data.map((d) => {
    const value = (d.clot_area + d.fibrin_area) / (units === "cm" ? 100 : 1);
    return {
      value,
      label: moment(d.imaged_at).format("MMM D[\n]H:mm"),
      dataPointText: value.toFixed(2),
      dataPointLabelComponent: () => (
        <View>
          <Text style={styles.dataPointLabel}>{value}</Text>
        </View>
      ),
      dataPointLabelShiftY: -5,
      dataPointLabelShiftX: 5,
    };
  });
  const clotData = data.map((d) => ({
    value: d.clot_area / (units === "cm" ? 100 : 1),
  }));
  const fibrinData = data.map((d) => ({
    value: d.fibrin_area / (units === "cm" ? 100 : 1),
  }));

  const legendItems = [
    {
      key: "clotting",
      title: "Clotting",
      color: Colors.CHART_RED,
    },
    {
      key: "fibrin",
      title: "Fibrin",
      color: Colors.CHART_BLUE,
    },
    {
      key: "total",
      title: "Total",
      color: Colors.BLACK,
    },
  ];

  // Fetches the annotation history for this oxygenator.
  useEffect(() => {
    apiFetch(`/oxygenators/${oxygenatorId}/history`)
      .then((data: AnnotationSession[]) => setData(data))
      .catch((error) => console.error(error));
  }, [oxygenatorId]);

  return (
    <View style={styles.container}>
      {/* Chart card */}
      <View style={styles.card}>
        {/* Y-axis rotated label */}
        <View style={styles.yAxisLabelContainer}>
          <Text style={[styles.yAxisLabel, { width: chartHeight }]}>
            Thrombotic Burden ({units}²)
          </Text>
        </View>

        {/* Chart area */}
        <View style={styles.chartArea}>
          <LineChart
            data={totalData}
            data2={clotData}
            data3={fibrinData}
            width={chartWidth}
            height={chartHeight}
            color1={Colors.BLACK}
            color2={Colors.CHART_RED}
            color3={Colors.CHART_BLUE}
            dataPointsColor1={Colors.BLACK}
            dataPointsColor2={Colors.CHART_RED}
            dataPointsColor3={Colors.CHART_BLUE}
            dataPointsRadius1={3}
            dataPointsRadius2={3}
            dataPointsRadius3={3}
            spacing={chartWidth / totalData.length}
            xAxisColor={Colors.GRAY}
            yAxisColor={Colors.GRAY}
            yAxisTextStyle={styles.yAxisText}
            xAxisLabelTextStyle={styles.xLabel}
            xAxisTextNumberOfLines={2}
            rulesColor={Colors.GRAY_6}
            rulesType="solid"
          />
        </View>
      </View>

      {/* Legend */}
      <View style={styles.legend}>
        {legendItems.map((item, index) => (
          <View key={item.key} style={styles.legendItemContainer}>
            <View style={styles.legendItem}>
              <View
                style={[styles.legendDot, { backgroundColor: item.color }]}
              />
              <Text style={styles.legendText}>{item.title}</Text>
            </View>
            {index !== legendItems.length - 1 ? (
              <View style={styles.legendSep} />
            ) : null}
          </View>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  dataPointLabel: {
    fontSize: 9,
    fontWeight: 600,
  },
  container: {
    flex: 1,
    alignItems: "center",
    paddingTop: 15,
    paddingHorizontal: 20,
    backgroundColor: Colors.BG,
  },
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.WHITE,
    padding: 10,
    borderRadius: 15,
  },
  yAxisLabelContainer: {
    width: 15,
    height: "100%",
    justifyContent: "center",
    alignItems: "center",
  },
  yAxisLabel: {
    fontSize: 10,
    fontWeight: "600",
    color: Colors.GRAY,
    letterSpacing: 0.7,
    transform: [{ rotate: "-90deg" }],
    textAlign: "center",
  },

  chartArea: {
    flex: 1,
    overflow: "hidden",
  },
  yAxisText: {
    fontSize: 11,
    color: Colors.GRAY,
    fontWeight: "500",
  },
  xLabel: {
    fontSize: 10,
    color: Colors.GRAY,
    fontWeight: "500",
    marginTop: 4,
  },
  legend: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    marginTop: 18,
    marginBottom: 8,
    backgroundColor: Colors.WHITE,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 20,
    elevation: 1,
  },
  legendItemContainer: { display: "flex", flexDirection: "row" },
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
    color: Colors.TEXT_SEC,
    letterSpacing: 0.2,
  },
  legendSep: {
    width: 1,
    height: 14,
    backgroundColor: Colors.GRAY_6,
    marginHorizontal: 16,
  },
});

export default ChartScreen;
