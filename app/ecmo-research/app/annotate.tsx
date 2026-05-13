import { ReactNativeZoomableView } from "@openspacelabs/react-native-zoomable-view";
import { Image } from "expo-image";
import {
  View,
  Text,
  Alert,
  ActivityIndicator,
  TouchableOpacity,
} from "react-native";
import { CanvasProvider } from "../components/CanvasContext";
import { Canvas } from "../components/Canvas";
import { useStateContext } from "@/components/StateContext";
import { useEffect, useRef, useState } from "react";
import { Redirect, useGlobalSearchParams, useRouter } from "expo-router";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";

/**
 * The annotation page for circling/tapping on thrombi. Only compatible on web since it uses <canvas> component.
 */
export default function Annotate() {
  const { state, dispatch } = useStateContext();
  const router = useRouter();
  const { ecmoId } = useGlobalSearchParams<{ ecmoId: string }>();
  const [loading, setLoading] = useState(true);
  const [image, setImage] = useState(null);
  const [mask, setMask] = useState<ImageBitmap>(null);
  const [scaleOffset, setScaleOffset] = useState(0);

  const imageIdRef = useRef(null);
  const annotationSessionIdRef = useRef(null);

  // useEffect(() => {
  //   return () => masks.forEach((bitmap) => bitmap.close());
  // }, [masks]);

  useEffect(() => {
    const uploadImage = (file: File): void => {
      const formData = new FormData();
      formData.append("image", file);

      fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmo/${ecmoId}/images`, {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then(async (json) => {
          imageIdRef.current = json.id;
          annotationSessionIdRef.current = json.current_annotation_session_id;

          const blob = await fetch(
            `data:${json.mimetype};base64,${json.cropped}`,
          ).then((r) => r.blob());

          setImage(blob);
          setLoading(false);
        })
        .catch((error) => {
          console.error(error);
          window.alert("Failed to process image");
          router.back();
        });
    };

    if (state.file === null) {
      window.alert("Selected image was not found, please try again");
      return;
    }

    uploadImage(state.file);
  }, [state.file, router, ecmoId]);

  const detectThrombus = (
    x1: number,
    y1: number,
    x2?: number,
    y2?: number,
  ): void => {
    fetch(
      `${process.env.EXPO_PUBLIC_API_URL}/api/ecmo/${ecmoId}/images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}/segmentations`,
      {
        method: "POST",
        body: JSON.stringify({ x1, y1, x2, y2 }),
        headers: {
          "Content-Type": "application/json",
        },
      },
    )
      .then((response) => response.json())
      .then(async (json) => {
        const blob = await fetch(`data:image/png;base64,${json.mask}`).then(
          (r) => r.blob(),
        );
        const bitmap = await createImageBitmap(blob);
        setMask(bitmap);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  if (state.file === null) {
    return <Redirect href="/" />;
  }

  if (loading || image === null) {
    return (
      <View
        style={{
          display: "flex",
          alignItems: "center",
          gap: 15,
          height: "100%",
          justifyContent: "center",
        }}
      >
        <ActivityIndicator size="large" />
        <Text style={{ color: "gray", fontSize: 16 }}>Processing image...</Text>
      </View>
    );
  }

  return (
    <View style={{ height: "100%", display: "flex", justifyContent: "center" }}>
      <View
        style={{
          position: "absolute",
          top: 15,
          backgroundColor: "white",
          display: "flex",
          flexDirection: "row",
          // paddingVertical: 5,
          // paddingHorizontal: 20,
          gap: 30,
          borderRadius: 20,
          alignSelf: "center",
          boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
        }}
      >
        <View
          style={{
            display: "flex",
            flex: 1,
            backgroundColor: "rgb(229,229,234)",
            flexDirection: "row",
            gap: 30,
            // paddingHorizontal: 15,
            borderRadius: 15,
            // paddingVertical: 5,
            marginVertical: 3,
            marginLeft: 3,
            alignItems: "center",
          }}
        >
          <View
            style={{
              backgroundColor: "white",
              borderRadius: 15,
              paddingHorizontal: 15,
              paddingVertical: 5,
              marginVertical: 3,
              marginLeft: 3,
            }}
          >
            <Text style={{ fontWeight: 500 }}>Clot</Text>
          </View>
          <Text>Fibrin</Text>
        </View>
        <MaterialCommunityIcons name="undo" size={18} color="black" />
        <MaterialCommunityIcons name="redo" size={18} color="black" />
        <MaterialCommunityIcons name="trash-can" size={18} color="black" />
      </View>

      <View
        style={{
          position: "absolute",
          bottom: 15,
          right: 15,
          backgroundColor: "white",
          borderRadius: 5,
          gap: 15,
          paddingVertical: 10,
          paddingHorizontal: 5,
          boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
        }}
      >
        <TouchableOpacity onPress={() => setScaleOffset((prev) => prev + 0.05)}>
          <MaterialCommunityIcons name="plus" size={18} color="black" />
        </TouchableOpacity>
        <View style={{ height: 1, backgroundColor: "rgb(209, 209, 214)" }} />
        <TouchableOpacity onPress={() => setScaleOffset((prev) => prev - 0.05)}>
          <MaterialCommunityIcons name="minus" size={18} color="black" />
        </TouchableOpacity>
      </View>

      <CanvasProvider
        ecmoImage={image}
        detectThrombus={detectThrombus}
        mask={mask}
      >
        <Canvas scaleOffset={scaleOffset} />
      </CanvasProvider>
    </View>
  );
}
