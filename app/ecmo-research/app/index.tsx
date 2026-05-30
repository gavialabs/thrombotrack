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
} from "react-native";
import { Picker } from "@react-native-picker/picker";
import * as ImagePicker from "expo-image-picker";
import { Image } from "expo-image";
import { useContext, useEffect, useState } from "react";
import Entypo from "@expo/vector-icons/Entypo";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { Ecmo } from "../constants/types";
import { useRouter } from "expo-router";
import { useStateContext } from "@/components/StateContext";
import { useAzureAuth } from "../hooks/useAzureAuth";

export default function Home() {
  const router = useRouter();
  const [ecmoList, setEcmoList] = useState<Ecmo[]>([]);
  const [filteredEcmoList, setFilteredEcmoList] = useState<Ecmo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [search, setSearch] = useState("");
  const [editingEcmoId, setEditingEcmoId] = useState(null);
  const { dispatch } = useStateContext();
  const [thumbnails, setThumbnails] = useState({});
  const { login, user, ready } = useAzureAuth();

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
    // login();
    // fetchEcmoList();
    console.log("nothing");
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

  return (
    <View style={{ backgroundColor: "white", height: "100%" }}>
      {isLoading ? (
        <ActivityIndicator size="large" style={{ marginTop: 20 }} />
      ) : (
        <>
          <TextInput
            style={{
              backgroundColor: "rgb(229, 229, 234)",
              marginHorizontal: 20,
              borderRadius: 8,
              marginVertical: 10,
              fontSize: 14,
              padding: 10,
              boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
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
                <>
                  <View
                    style={{
                      padding: 20,
                      display: "flex",
                      flexDirection: "row",
                      gap: 10,
                    }}
                  >
                    {Object.keys(thumbnails).includes(item.id) ? (
                      <Image
                        source={thumbnails[item.id]}
                        style={{
                          height: 100,
                          width: 100,
                          borderRadius: 50,
                          boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
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
                    <View
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        flex: 1,
                      }}
                    >
                      <View>
                        <View
                          style={{
                            display: "flex",
                            flexDirection: "row",
                            justifyContent: "space-between",
                            alignItems: "center",
                          }}
                        >
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
                              }}
                            />
                          ) : (
                            <Text style={{ fontWeight: 500 }}>
                              {item.name}
                              <TouchableOpacity
                                onPress={() => setEditingEcmoId(item.id)}
                              >
                                <MaterialCommunityIcons
                                  name="pencil"
                                  size={15}
                                  color="gray"
                                  style={{ marginLeft: 5 }}
                                />
                              </TouchableOpacity>
                            </Text>
                          )}
                          <TouchableOpacity
                            onPress={() => handleDeleteEcmo(item.id)}
                          >
                            <MaterialCommunityIcons
                              name="trash-can"
                              size={20}
                              color="rgba(255, 56, 60, 0.7)"
                            />
                          </TouchableOpacity>
                          {/* <Text style={{ color: "gray" }}>Last updated 7:03pm</Text> */}
                        </View>
                        <Picker
                          onValueChange={(itemValue) =>
                            handleEditEcmo(item.id, { type: itemValue })
                          }
                          selectedValue={item.type}
                          style={{ marginTop: 10 }}
                        >
                          <Picker.Item label="Getinge" value="getinge" />
                          <Picker.Item label="Nautilus" value="nautilus" />
                        </Picker>

                        <View
                          style={{
                            flexDirection: "row",
                            alignItems: "flex-start",
                          }}
                        >
                          <Text style={{ fontSize: 20, lineHeight: 30 }}>
                            {item.total_area?.toFixed(2) ?? 0} mm
                          </Text>
                          <Text style={{ fontSize: 11, lineHeight: 18 }}>
                            2
                          </Text>
                        </View>
                      </View>
                      {!isPending ? (
                        <View
                          style={{
                            display: "flex",
                            flexDirection: "row",
                            justifyContent: "space-between",
                            gap: 10,
                          }}
                        >
                          <TouchableOpacity
                            style={{
                              backgroundColor: "lightgray",
                              paddingVertical: 5,
                              width: 100,
                              alignItems: "center",
                              borderRadius: 20,
                            }}
                            onPress={() =>
                              router.navigate({
                                pathname: "/chart",
                                params: { ecmoId: item.id },
                              })
                            }
                          >
                            <Text>View chart</Text>
                          </TouchableOpacity>
                          <TouchableOpacity
                            onPress={() => pickImage(item.id)}
                            style={{
                              backgroundColor: "lavender",
                              paddingVertical: 5,
                              width: 100,
                              alignItems: "center",
                              borderRadius: 20,
                            }}
                          >
                            <Text>Log image</Text>
                          </TouchableOpacity>
                        </View>
                      ) : null}
                    </View>
                  </View>
                </>
              );
            }}
            keyExtractor={(item) => item.id}
            ItemSeparatorComponent={
              <View
                style={{
                  height: 1,
                  backgroundColor: "#e6e6e6",
                  marginHorizontal: 16,
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
        // onPress={() => setEcmoList([{ id: "pending", name: "" }, ...ecmoList])}
        onPress={login}
      >
        <Entypo name="plus" size={24} color="white" />
      </TouchableOpacity>
    </View>
  );
}
