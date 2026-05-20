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

enum AnnotationType {
  CLOT = "clot",
  FIBRIN = "fibrin",
}

/**
 * The annotation page for circling/tapping on thrombi. Only compatible on web since it uses <canvas> component.
 */
export default function Annotate() {
  const { state, dispatch } = useStateContext();
  const router = useRouter();
  const { ecmoId } = useGlobalSearchParams<{ ecmoId: string }>();
  const [loading, setLoading] = useState(true);
  const [image, setImage] = useState(null);
  const [mask, setMask] = useState<ImageBitmap | null>(null);
  const [annotationType, setAnnotationType] = useState<AnnotationType>(
    AnnotationType.CLOT,
  );

  const imageIdRef = useRef(null);
  const annotationSessionIdRef = useRef(null);

  // useEffect(() => {
  //   return () => masks.forEach((bitmap) => bitmap.close());
  // }, [masks]);

  useEffect(() => {
    const uploadImage = (file: File): void => {
      const formData = new FormData();
      formData.append("image", file);

      fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmos/${ecmoId}/images`, {
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
      `${process.env.EXPO_PUBLIC_API_URL}/api/ecmos/${ecmoId}/images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}/segmentations`,
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

  const doUndo = () => {
    fetch(
      `${process.env.EXPO_PUBLIC_API_URL}/api/ecmos/${ecmoId}/images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}/undo`,
      {
        method: "POST",
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

  const doRedo = () => {
    fetch(
      `${process.env.EXPO_PUBLIC_API_URL}/api/ecmos/${ecmoId}/images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}/redo`,
      {
        method: "POST",
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

  const doClear = () => {
    fetch(
      `${process.env.EXPO_PUBLIC_API_URL}/api/ecmos/${ecmoId}/images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}/clear`,
      {
        method: "POST",
      },
    )
      .then(() => setMask(null))
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
      <CanvasProvider
        ecmoImage={image}
        detectThrombus={detectThrombus}
        mask={mask}
      >
        <Canvas />
      </CanvasProvider>

      <View
        style={{
          position: "absolute",
          top: 10,
          display: "flex",
          alignItems: "center",
          flexDirection: "row",
          gap: 10,
          alignSelf: "center",
        }}
      >
        <View
          style={{
            display: "flex",
            flex: 1,
            backgroundColor: "rgb(229,229,234)",
            boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
            flexDirection: "row",
            borderRadius: 20,
            marginVertical: 3,
            marginLeft: 3,
            alignItems: "center",
            borderColor: "white",
            borderWidth: 3,
          }}
        >
          <TouchableOpacity
            style={{
              backgroundColor:
                annotationType === AnnotationType.CLOT ? "white" : undefined,
              borderRadius: 15,
              paddingHorizontal: 15,
              paddingVertical: 5,
              marginVertical: 3,
              marginLeft: 3,
              transitionDuration: "0.5s",
              transitionProperty: "background-color",
            }}
            onPress={() => setAnnotationType(AnnotationType.CLOT)}
          >
            <Text
              style={{
                fontWeight:
                  annotationType === AnnotationType.CLOT ? 500 : undefined,
                transitionDuration: "0.5s",
                transitionProperty: "font-weight",
              }}
            >
              Clot
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={{
              backgroundColor:
                annotationType === AnnotationType.FIBRIN ? "white" : undefined,
              borderRadius: 15,
              paddingHorizontal: 15,
              paddingVertical: 5,
              marginVertical: 3,
              marginRight: 3,
              transitionDuration: "0.5s",
              transitionProperty: "background-color",
            }}
            onPress={() => setAnnotationType(AnnotationType.FIBRIN)}
          >
            <Text
              style={{
                fontWeight:
                  annotationType === AnnotationType.FIBRIN ? 500 : undefined,
                transitionDuration: "0.5s",
                transitionProperty: "font-weight",
              }}
            >
              Fibrin
            </Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={{
            backgroundColor: "white",
            borderRadius: 20,
            padding: 10,
            boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
          }}
          onPress={doUndo}
        >
          <MaterialCommunityIcons name="undo" size={18} color="black" />
        </TouchableOpacity>
        <TouchableOpacity
          style={{
            backgroundColor: "white",
            borderRadius: 20,
            padding: 10,
            boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
          }}
          onPress={doRedo}
        >
          <MaterialCommunityIcons name="redo" size={18} color="black" />
        </TouchableOpacity>
        <TouchableOpacity
          style={{
            backgroundColor: "white",
            borderRadius: 20,
            padding: 10,
            boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
          }}
          onPress={doClear}
        >
          <MaterialCommunityIcons
            name="trash-can"
            size={18}
            color="rgba(255, 56, 60, 0.7)"
          />
        </TouchableOpacity>
      </View>
    </View>
  );
}
