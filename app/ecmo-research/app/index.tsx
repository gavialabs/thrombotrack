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
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useEffect, useState } from "react";
import { Ecmo } from "./types";
import { useRouter } from "expo-router";

export default function Home() {
  const router = useRouter();
  const [ecmoList, setEcmoList] = useState<Ecmo[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isModalVisible, setModalVisible] = useState<boolean>(false);

  // current ecmo id that we are uploading an image for
  const [currentEcmoId, setCurrentEcmoId] = useState<string | null>(null);

  const [name, setName] = useState<string>("");

  const fetchEcmoList = (): void => {
    fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmos`)
      .then((response) => response.json())
      .then((json) => {
        setEcmoList(json);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  const uploadImage = (file: File): void => {
    const formData = new FormData();
    formData.append("image", file);

    fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmo/${currentEcmoId}`, {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((json) => {
        router.navigate({
          pathname: "/annotate",
          params: { image: json },
        });
      })
      .catch((error) => {
        console.error(error);
      });
  };

  useEffect(() => {
    fetchEcmoList();
  }, []);

  const handleAddEcmo = (): void => {
    setModalVisible(false);

    fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmo`, {
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
        setEcmoList([...ecmoList, json]);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  const pickImage = async (id: string) => {
    setCurrentEcmoId(id);
    ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      allowsEditing: true,
      quality: 1,
    }).then((result) => {
      if (!result.canceled) {
        const { file } = result.assets[0];

        if (file === undefined) {
          Alert.alert("Please try again");
          return;
        }

        uploadImage(file);
      }
    });
  };

  return (
    <View>
      <FlatList
        data={ecmoList}
        onRefresh={fetchEcmoList}
        ListEmptyComponent={
          <View
            style={{
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <TouchableOpacity onPress={() => setModalVisible(true)}>
              <Text style={{ fontSize: 18, color: "#32006e" }}>+ Add ECMO</Text>
            </TouchableOpacity>
          </View>
        }
        refreshing={isLoading}
        renderItem={({ item, index }) => {
          return (
            <>
              <View
                style={{
                  padding: 16,
                  display: "flex",
                  flexDirection: "row",
                  gap: 10,
                }}
              >
                <View
                  style={{
                    height: 100,
                    width: 100,
                    backgroundColor: "gray",
                    borderRadius: 15,
                  }}
                />
                <View
                  style={{ display: "flex", justifyContent: "space-between" }}
                >
                  <View>
                    <Text style={{ fontWeight: 500 }}>{item.name}</Text>
                    {/* <Text style={{ color: "gray" }}>Last updated 7:03pm</Text> */}
                  </View>
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
                      <Text>Take photo</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              </View>
              {index === ecmoList.length - 1 ? (
                <View
                  style={{
                    height: 132,
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <TouchableOpacity onPress={() => setModalVisible(true)}>
                    <Text style={{ fontSize: 18, color: "purple" }}>
                      + Add ECMO
                    </Text>
                  </TouchableOpacity>
                </View>
              ) : null}
            </>
          );
        }}
        keyExtractor={(item) => item.id}
        style={{ backgroundColor: "white", borderRadius: 26, margin: 20 }}
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

      <Modal visible={isModalVisible} transparent>
        <View
          style={{
            flex: 1,
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <View
            style={{
              margin: 20,
              backgroundColor: "white",
              borderRadius: 20,
              padding: 35,
              alignItems: "center",
              shadowColor: "#000",
              shadowOffset: {
                width: 0,
                height: 2,
              },
              shadowOpacity: 0.25,
              shadowRadius: 4,
              elevation: 5,
            }}
          >
            <TextInput
              placeholder="Enter ECMO ID"
              placeholderTextColor="gray"
              value={name}
              onChangeText={(value) => setName(value)}
            />
            <Button title="Save" onPress={handleAddEcmo} />
          </View>
        </View>
      </Modal>
    </View>
  );
}
