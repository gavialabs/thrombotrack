import {
  TextInput,
  View,
  StyleSheet,
  FlatList,
  Text,
  TouchableOpacity,
  Alert,
  Modal,
  Button,
  ActivityIndicator,
  Dimensions,
} from "react-native";
import { Picker } from "@react-native-picker/picker";
import * as ImagePicker from "expo-image-picker";
import { Image } from "expo-image";
import { useContext, useEffect, useState } from "react";
import Entypo from "@expo/vector-icons/Entypo";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { Ecmo } from "../../constants/types";
import { useRouter } from "expo-router";
import { useStateContext } from "@/context/StateContext";

export default function Home() {
  const router = useRouter();
  const [ecmoList, setEcmoList] = useState<Ecmo[]>([]);
  const [filteredEcmoList, setFilteredEcmoList] = useState<Ecmo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [search, setSearch] = useState("");
  const [editingEcmoId, setEditingEcmoId] = useState(null);
  const { dispatch } = useStateContext();
  const [thumbnails, setThumbnails] = useState<Record<string, string>>({});

  const [name, setName] = useState<string>("");

  const fetchEcmoList = (): void => {
    fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmos`)
      .then((response) => response.json())
      .then((json) => {
        setEcmoList(json);

        json.forEach((data) => {
          if (data.thumbnail !== null) {
            fetch(`data:image/jpeg;base64,${data.thumbnail}`).then((r) =>
              r.blob().then((blob) => {
                setThumbnails((prev) => ({
                  ...prev,
                  [data.id]: URL.createObjectURL(blob),
                }));
              }),
            );
          }
        });

        setIsLoading(false);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  useEffect(() => {
    fetchEcmoList();
  }, []);

  useEffect(() => {
    setFilteredEcmoList(
      ecmoList.filter((ecmo) =>
        ecmo.name.toLowerCase().includes(search.toLowerCase()),
      ),
    );
  }, [ecmoList, search]);

  const handleAddEcmo = (): void => {
    fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmos`, {
      method: "POST",
      body: JSON.stringify({
        name,
      }),
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((json) => {
        setEcmoList(
          [...ecmoList.filter((ecmo) => ecmo.id !== "pending"), json].sort(
            (a, b) => a.name.localeCompare(b.name),
          ),
        );
        setIsLoading(false);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  const handleEditEcmo = (ecmoId: string, payload): void => {
    fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmos/${ecmoId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then(() => {
        setEcmoList(
          ecmoList.map((ecmo) => {
            if (ecmo.id === ecmoId) {
              return {
                ...ecmo,
                ...payload,
              };
            } else {
              return ecmo;
            }
          }),
        );
        setName("");
        setEditingEcmoId(null);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  const handleDeleteEcmo = (ecmoId: string): void => {
    fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmos/${ecmoId}`, {
      method: "DELETE",
    })
      .then((response) => response.json())
      .then(() => {
        setEcmoList(ecmoList.filter((ecmo) => ecmo.id !== ecmoId));
      })
      .catch((error) => {
        console.error(error);
      });
  };

  const pickImage = async (ecmoId: string) => {
    ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      allowsEditing: true,
      quality: 1,
    }).then((result) => {
      if (result.canceled) {
        return;
      }

      const { file } = result.assets[0];

      if (file === undefined) {
        Alert.alert("Please try again");
        return;
      }

      dispatch({ type: "SET_FILE", payload: file });
      router.navigate({
        pathname: "/annotate",
        params: { ecmoId },
      });
    });
  };

  const renderArea = (area: number | null): string => {
    if (area === null || area === 0) {
      return "0";
    }

    if (area > 10) {
      return (area / 100).toFixed(2);
    }

    return area.toFixed(2);
  };

  const getAreaLabel = (area: number | null): string => {
    if (area === null || area === 0) {
      return "mm²";
    }

    if (area > 10) {
      return "cm²";
    }

    return "mm²";
  };

  return (
    <View style={{ height: "100%" }}>
      {isLoading ? (
        <ActivityIndicator size="large" style={{ marginTop: 20 }} />
      ) : (
        <>
          <TextInput
            style={{
              backgroundColor: "rgba(255, 255, 255, 1)",
              marginHorizontal: 20,
              borderRadius: 8,
              borderWidth: 1,
              borderColor: "rgba(0, 0, 0, 0.1)",
              marginVertical: 10,
              fontSize: 14,
              padding: 10,
              // boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
              // -webkit-box-shadow: 0px -1px 20px -1px rgba(0,0,0,0.75);
              // -moz-box-shadow: 0px -1px 20px -1px rgba(0,0,0,0.75);
            }}
            placeholder="Search..."
            placeholderTextColor="rgb(142, 142, 147)"
            onChangeText={(search) => setSearch(search)}
          />
          <FlatList
            data={filteredEcmoList}
            onRefresh={fetchEcmoList}
            ListEmptyComponent={
              <View
                style={{
                  alignItems: "center",
                  justifyContent: "center",
                  marginTop: 15,
                  paddingHorizontal: 20,
                }}
              >
                <Text style={{ textAlign: "center" }}>
                  No ECMOs found. Use the &quot;+&quot; button to add a new
                  ECMO, or swipe down to refresh.
                </Text>
              </View>
            }
            refreshing={isLoading}
            renderItem={({ item, index }) => {
              const isPending = item.id === "pending";
              const isEditing = item.id === editingEcmoId;

              return (
                <View
                  style={{
                    backgroundColor: "white",
                    borderRadius: 15,
                    marginHorizontal: 20,
                    padding: 10,
                    boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.05)",
                  }}
                >
                  <View
                    style={{
                      display: "flex",
                      flexDirection: "row",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: 10,
                    }}
                  >
                    {/* Name */}
                    {isPending || isEditing ? (
                      <TextInput
                        defaultValue={item.name}
                        placeholder="Enter name..."
                        placeholderTextColor="lightgray"
                        autoFocus
                        onBlur={() => {
                          if (name.length === 0) {
                            if (isPending) {
                              setEcmoList(ecmoList.slice(1));
                            } else {
                              setEditingEcmoId(null);
                            }
                          } else if (isPending) {
                            handleAddEcmo();
                          } else {
                            handleEditEcmo(item.id, { name });
                          }
                        }}
                        onChangeText={(newValue) => setName(newValue)}
                        style={{
                          borderRadius: 8,
                          padding: 5,
                          width: "100%",
                          fontWeight: 500,
                          fontSize: 23,
                          marginRight: 10,
                          marginLeft: -5,
                        }}
                      />
                    ) : (
                      <TouchableOpacity
                        onPress={() => setEditingEcmoId(item.id)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          flexDirection: "row",
                          flex: 1,
                        }}
                      >
                        <Text
                          style={{
                            fontWeight: 500,
                            fontSize: 23,
                            borderWidth: 5,
                            borderColor: "transparent",
                            marginLeft: -5,
                          }}
                        >
                          {item.name}
                        </Text>
                        <MaterialCommunityIcons
                          name="pencil"
                          size={18}
                          color="gray"
                          style={{ marginLeft: 5 }}
                        />
                      </TouchableOpacity>
                    )}

                    {/* Type */}
                    <Picker
                      onValueChange={(itemValue) =>
                        handleEditEcmo(item.id, { type: itemValue })
                      }
                      selectedValue={item.type}
                      style={{
                        height: 30,
                        fontWeight: 500,
                        fontSize: 12,
                        paddingHorizontal: 10,
                        borderRadius: 12,
                      }}
                    >
                      <Picker.Item label="HLS" value="getinge" />
                      <Picker.Item label="Nautilus" value="nautilus" />
                    </Picker>
                  </View>

                  <View
                    style={{
                      display: "flex",
                      flexDirection: "row",
                      alignItems: "center",
                      gap: 10,
                    }}
                  >
                    {/* Current area */}
                    <View
                      style={{
                        display: "flex",
                        flex: 1,
                      }}
                    >
                      <View style={styles.totalRow}>
                        <Text style={styles.totalValue}>
                          {renderArea(item.clot_area + item.fibrin_area)}
                        </Text>
                        <Text style={styles.totalUnit}>
                          {getAreaLabel(item.clot_area + item.fibrin_area)}
                        </Text>
                        <Text style={styles.totalLabel}>total burden</Text>
                      </View>

                      {/* Stacked bar */}
                      <BurdenBar
                        fibrin={item.fibrin_area}
                        clotting={item.clot_area}
                      />

                      {/* Breakdown */}
                      <View style={styles.breakdown}>
                        <View style={styles.breakdownItem}>
                          <Text
                            style={[
                              styles.breakdownValue,
                              { color: CLOT_COLOR },
                            ]}
                          >
                            {renderArea(item.clot_area)}{" "}
                            {getAreaLabel(item.clot_area)}
                          </Text>
                          <View
                            style={{
                              display: "flex",
                              flexDirection: "row",
                              alignItems: "center",
                              gap: 5,
                            }}
                          >
                            <View
                              style={[
                                styles.breakdownDot,
                                { backgroundColor: CLOT_COLOR },
                              ]}
                            />
                            <Text style={styles.breakdownLabel}>Clotting</Text>
                          </View>
                        </View>
                        <View style={styles.breakdownDivider} />
                        <View style={styles.breakdownItem}>
                          <Text
                            style={[
                              styles.breakdownValue,
                              { color: FIBRIN_COLOR },
                            ]}
                          >
                            {renderArea(item.fibrin_area)}{" "}
                            {getAreaLabel(item.fibrin_area)}
                          </Text>
                          <View
                            style={{
                              display: "flex",
                              flexDirection: "row",
                              alignItems: "center",
                              gap: 5,
                            }}
                          >
                            <View
                              style={[
                                styles.breakdownDot,
                                { backgroundColor: FIBRIN_COLOR },
                              ]}
                            />
                            <Text style={styles.breakdownLabel}>Fibrin</Text>
                          </View>
                        </View>
                      </View>

                      <Text style={{ color: "gray", fontSize: 12 }}>
                        5/31/26 14:00 by Luca Palermo
                      </Text>
                    </View>

                    {/* Thumbnail */}
                    {Object.keys(thumbnails).includes(item.id) ? (
                      <Image
                        source={thumbnails[item.id]}
                        style={{
                          height: 140,
                          width: 140,
                          borderRadius: item.type === "nautilus" ? 70 : 10,
                          marginTop: 10,
                        }}
                      />
                    ) : (
                      <View
                        style={{
                          height: 100,
                          width: 100,
                          backgroundColor: "gray",
                          borderRadius: 15,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
                        }}
                      >
                        {!isPending ? (
                          <Entypo name="camera" size={24} color="white" />
                        ) : null}
                      </View>
                    )}
                  </View>

                  {/* Actions */}
                  {!isPending ? (
                    <View
                      style={{
                        display: "flex",
                        flexDirection: "row",
                        justifyContent: "space-between",
                        alignItems: "flex-end",
                        flex: 1,
                        marginTop: 15,
                        gap: 10,
                      }}
                    >
                      <TouchableOpacity
                        style={{
                          backgroundColor: "rgba(97, 85, 245, 0.3)",
                          padding: 10,
                          borderRadius: 30,
                          boxShadow: "0px 0px 10px 0px rgba(97, 85, 245, 0.1)",
                          display: "flex",
                          flex: 1,
                          flexDirection: "row",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: 5,
                        }}
                        onPress={() =>
                          router.navigate({
                            pathname: "/gallery",
                            params: { ecmoId: item.id },
                          })
                        }
                      >
                        <MaterialCommunityIcons
                          name="image-multiple"
                          size={20}
                          color="rgb(97, 85, 245)"
                        />
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={{
                          backgroundColor: "rgba(52, 199, 89, 0.3)",
                          padding: 10,
                          borderRadius: 30,
                          boxShadow: "0px 0px 10px 0px rgba(52, 199, 89, 0.1)",
                          display: "flex",
                          flex: 1,
                          flexDirection: "row",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: 5,
                        }}
                        onPress={() =>
                          router.navigate({
                            pathname: "/chart",
                            params: { ecmoId: item.id },
                          })
                        }
                      >
                        <MaterialCommunityIcons
                          name="chart-line"
                          size={20}
                          color="rgb(52, 199, 89)"
                        />
                      </TouchableOpacity>
                      <TouchableOpacity
                        onPress={() => pickImage(item.id)}
                        style={{
                          backgroundColor: "rgba(0, 136, 255, 0.3)",
                          padding: 10,
                          borderRadius: 30,
                          boxShadow: "0px 0px 10px 0px rgba(0, 136, 255, 0.1)",
                          display: "flex",
                          flex: 1,
                          flexDirection: "row",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: 5,
                        }}
                      >
                        <MaterialCommunityIcons
                          name="camera"
                          size={20}
                          color="rgb(0, 136, 255)"
                        />
                      </TouchableOpacity>
                      <TouchableOpacity
                        onPress={() => handleDeleteEcmo(item.id)}
                        style={{
                          backgroundColor: "rgba(255, 56, 60, 0.3)",
                          padding: 10,
                          borderRadius: 30,
                          boxShadow: "0px 0px 10px 0px rgba(255, 56, 60, 0.1)",
                          display: "flex",
                          flex: 1,
                          flexDirection: "row",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: 5,
                        }}
                      >
                        <MaterialCommunityIcons
                          name="trash-can"
                          size={20}
                          color="rgb(255, 56, 60)"
                        />
                      </TouchableOpacity>
                    </View>
                  ) : null}
                </View>
              );
            }}
            keyExtractor={(item) => item.id}
            ItemSeparatorComponent={
              <View
                style={{
                  height: 1,
                  backgroundColor: "#e6e6e6",
                  marginHorizontal: 16,
                  marginVertical: 10,
                }}
              />
            }
          />
        </>
      )}

      <TouchableOpacity
        style={{
          position: "absolute",
          bottom: 20,
          right: 20,
          height: 70,
          width: 70,
          backgroundColor: "#4b2e83",
          borderRadius: 35,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.3)",
        }}
        onPress={() => setEcmoList([{ id: "pending", name: "" }, ...ecmoList])}
      >
        <Entypo name="plus" size={24} color="white" />
      </TouchableOpacity>
    </View>
  );
}

const { width: SCREEN_WIDTH } = Dimensions.get("window");

// // ─── Design tokens ────────────────────────────────────────────────────────────
const BG = "#F0F2F5";
const CARD_BG = "#FFFFFF";
const ACCENT = "#1D3557";
const FIBRIN_COLOR = "#377eb8";
const CLOT_COLOR = "#e41a1c";
const DANGER = "#DC2626";
const MUTED = "#9CA3AF";
const TEXT_PRIMARY = "#111827";
const TEXT_SEC = "#6B7280";

// ─── Mini stacked bar ─────────────────────────────────────────────────────────
function BurdenBar({ fibrin, clotting }) {
  const total = fibrin + clotting;
  // Bar spans card content width (card padding 16 each side = 32, container h-pad 20 each = 40)
  const barWidth = SCREEN_WIDTH - 72;
  const filled = barWidth;
  const fibrinW = (fibrin / Math.max(total, 1)) * filled;
  const clotW = (clotting / Math.max(total, 1)) * filled;

  return (
    <View style={burdenBar.track}>
      <View style={[burdenBar.fibrin, { width: fibrinW }]} />
      <View style={[burdenBar.clotting, { width: clotW }]} />
    </View>
  );
}

const burdenBar = StyleSheet.create({
  track: {
    flexDirection: "row",
    height: 5,
    borderRadius: 3,
    backgroundColor: "#E5E7EB",
    overflow: "hidden",
    marginTop: 8,
    marginBottom: 2,
  },
  fibrin: { height: 5, backgroundColor: FIBRIN_COLOR },
  clotting: { height: 5, backgroundColor: CLOT_COLOR },
});

// ─── Styles ───────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: BG,
  },

  // Header
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 14,
  },
  headerEyebrow: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 2.5,
    color: MUTED,
    marginBottom: 2,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: "700",
    color: TEXT_PRIMARY,
    letterSpacing: -0.5,
  },
  headerStat: {
    alignItems: "center",
    backgroundColor: ACCENT,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 12,
  },
  headerStatValue: {
    fontSize: 20,
    fontWeight: "700",
    color: "#FFFFFF",
    lineHeight: 22,
  },
  headerStatLabel: {
    fontSize: 10,
    fontWeight: "600",
    color: "#93C5FD",
    letterSpacing: 0.5,
  },

  // Summary strip
  summaryStrip: {
    flexDirection: "row",
    backgroundColor: CARD_BG,
    marginHorizontal: 20,
    borderRadius: 14,
    paddingVertical: 12,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  summaryItem: {
    flex: 1,
    alignItems: "center",
  },
  summaryValue: {
    fontSize: 18,
    fontWeight: "700",
    color: TEXT_PRIMARY,
    letterSpacing: -0.3,
  },
  summaryLabel: {
    fontSize: 10,
    color: MUTED,
    fontWeight: "500",
    marginTop: 2,
    letterSpacing: 0.2,
  },
  summaryDivider: {
    width: 1,
    backgroundColor: "#E5E7EB",
    marginVertical: 4,
  },

  // List
  list: {
    paddingHorizontal: 20,
    paddingBottom: 24,
  },

  // Card
  card: {
    backgroundColor: CARD_BG,
    borderRadius: 16,
    overflow: "hidden", // clips the image to rounded corners
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 10,
    elevation: 3,
  },

  // Image section
  imageContainer: {
    height: 140,
    width: "100%",
    backgroundColor: "#E5E7EB",
  },
  cardImage: {
    width: "100%",
    height: 140,
  },
  imagePlaceholder: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    backgroundColor: "#F3F4F6",
  },
  imagePlaceholderIcon: {
    fontSize: 28,
  },
  imagePlaceholderText: {
    fontSize: 12,
    color: MUTED,
    fontWeight: "500",
  },
  // Dark scrim at bottom of image so overlaid text is readable
  imageScrim: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    height: 140 * 0.55,
    // Simulate a gradient using a semi-transparent dark overlay
    backgroundColor: "rgba(0,0,0,0.45)",
  },
  imageOverlay: {
    position: "absolute",
    left: 14,
    right: 14,
    bottom: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  cardTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
  },
  cardIndicator: {
    width: 3,
    height: 16,
    borderRadius: 2,
    backgroundColor: "#FFFFFF",
  },
  cardNameOverlay: {
    fontSize: 15,
    fontWeight: "700",
    color: "#FFFFFF",
    letterSpacing: -0.2,
  },
  badge: {
    paddingHorizontal: 9,
    paddingVertical: 3,
    borderRadius: 20,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1,
  },

  // Card body (below image)
  cardBody: {
    padding: 14,
  },

  // Total reading
  totalRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 4,
  },
  totalValue: {
    fontSize: 26,
    fontWeight: "700",
    color: TEXT_PRIMARY,
    letterSpacing: -0.5,
  },
  totalUnit: {
    fontSize: 13,
    fontWeight: "600",
    color: TEXT_SEC,
  },
  totalLabel: {
    fontSize: 12,
    color: MUTED,
    marginLeft: 4,
  },

  // Breakdown
  breakdown: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 8,
    marginBottom: 12,
  },
  breakdownItem: {
    flex: 1,
  },
  breakdownDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  breakdownLabel: {
    fontSize: 12,
    color: TEXT_SEC,
    fontWeight: "500",
  },
  breakdownValue: {
    fontSize: 12,
    fontWeight: "700",
  },
  breakdownDivider: {
    width: 1,
    height: 16,
    backgroundColor: "#E5E7EB",
    marginHorizontal: 12,
  },

  // Actions
  actions: {
    flexDirection: "row",
    gap: 8,
  },
});
