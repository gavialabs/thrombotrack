import { ReactNativeZoomableView } from "@openspacelabs/react-native-zoomable-view";
import { Image } from "expo-image";
import {
  View,
  Text,
  Alert,
  ActivityIndicator,
  TouchableOpacity,
} from "react-native";
import Canvas from "@/components/NewCanvas";
import { useStateContext } from "@/context/StateContext";
import { useEffect, useRef, useState } from "react";
import {
  Redirect,
  useGlobalSearchParams,
  useNavigation,
  useRouter,
} from "expo-router";
import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import AnnotateHeader from "@/components/AnnotateHeader";

enum AnnotationType {
  CLOT = "clot",
  FIBRIN = "fibrin",
  ERASE = "erase",
}

/**
 * The annotation page for circling/tapping on thrombi. Only compatible on web since it uses <canvas> component.
 */
export default function Annotate() {
  const { state, dispatch } = useStateContext();
  const navigation = useNavigation();
  const router = useRouter();
  const { ecmoId } = useGlobalSearchParams<{ ecmoId: string }>();
  const [loadingImage, setLoadingImage] = useState(true);
  const [image, setImage] = useState<ImageBitmap | null>(null);
  const [mask, setMask] = useState<ImageBitmap | null>(null);
  const [thrombusType, setAnnotationType] = useState<AnnotationType>(
    AnnotationType.CLOT,
  );
  const [loadingMask, setLoadingMask] = useState(false);
  const [hideMask, setHideMask] = useState(false);

  const imageIdRef = useRef(null);
  const annotationSessionIdRef = useRef(null);

  // useEffect(() => {
  //   return () => masks.forEach((bitmap) => bitmap.close());
  // }, [masks]);

  useEffect(() => {
    const doFinish = () => {
      fetch(
        `${process.env.EXPO_PUBLIC_API_URL}/api/ecmos/${ecmoId}/images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}/end`,
        {
          method: "POST",
        },
      )
        .then(() => router.push("/"))
        .catch((error) => {
          console.error(error);
        });
    };

    navigation.setOptions({
      header: () => <AnnotateHeader onFinish={doFinish} />,
    });
  }, [navigation, ecmoId, router]);

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
          const bitmap = await createImageBitmap(blob);

          setImage(bitmap);
          setLoadingImage(false);
        })
        .catch((error) => {
          console.error(error);
          window.alert("Failed to process image");
          router.back();
        });
    };

    if (ecmoId === undefined) {
      return;
    }

    if (state.file === null) {
      // window.alert("Selected image was not found, please try again");
      return;
    }

    uploadImage(state.file);
  }, [state.file, router, ecmoId, dispatch]);

  const annotateImage = (path: [number, number][]): void => {
    if (path.length === 0) {
      console.error("Tried to annotate image with no points in path");
      return;
    }

    setLoadingMask(true);
    const distinctPath: [number, number][] = [];
    path.forEach((point) => {
      const intPoint: [number, number] = [
        Math.trunc(point[0]),
        Math.trunc(point[1]),
      ];
      if (
        !distinctPath.some(
          (point2) => point2[0] === intPoint[0] && point2[1] === intPoint[1],
        )
      ) {
        distinctPath.push(intPoint);
      }
    });

    fetch(
      `${process.env.EXPO_PUBLIC_API_URL}/api/ecmos/${ecmoId}/images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}/segmentations`,
      {
        method: "POST",
        body: JSON.stringify({
          path: distinctPath,
          thrombus_type: thrombusType,
        }),
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
        setLoadingMask(false);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  const doUndo = () => {
    setLoadingMask(true);
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
        setLoadingMask(false);
      })
      .catch((error) => {
        console.error(error);
      });
  };

  const doRedo = () => {
    setLoadingMask(true);
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
        setLoadingMask(false);
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

  if (loadingImage || image === null) {
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
    <View
      style={{
        height: "100%",
        display: "flex",
        justifyContent: "center",
        overflow: "hidden",
      }}
    >
      <Canvas
        annotateImage={annotateImage}
        image={image}
        mask={mask}
        hideMask={hideMask}
      />

      {/* toolbar-- must place after canvas so that it layers on top */}
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
        <TouchableOpacity
          style={{
            backgroundColor: hideMask ? "rgb(97, 85, 245)" : "white",
            borderRadius: 20,
            padding: 10,
            boxShadow: hideMask
              ? "0px 0px 10px 0px rgba(97, 85, 245, 0.1)"
              : "0px 0px 10px 0px rgba(0, 0, 0, 0.1)",
          }}
          disabled={loadingMask}
          onPress={() => setHideMask(!hideMask)}
        >
          <MaterialCommunityIcons
            name="eye-off"
            size={18}
            color={!hideMask ? "#rgb(199,199,204)" : "white"}
          />
        </TouchableOpacity>

        <View
          style={{
            display: "flex",
            flex: 1,
            backgroundColor: "rgb(229,229,234)",
            boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
            flexDirection: "row",
            borderRadius: 20,
            alignItems: "center",
            borderColor: "white",
            borderWidth: 3,
          }}
        >
          <TouchableOpacity
            style={{
              backgroundColor:
                thrombusType === AnnotationType.CLOT ? "white" : undefined,
              borderRadius: 15,
              paddingHorizontal: 15,
              paddingVertical: 5,
              marginVertical: 3,
              marginLeft: 3,
            }}
            onPress={() => setAnnotationType(AnnotationType.CLOT)}
          >
            <Text
              style={{
                fontWeight:
                  thrombusType === AnnotationType.CLOT ? 500 : undefined,
              }}
            >
              Clot
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={{
              backgroundColor:
                thrombusType === AnnotationType.FIBRIN ? "white" : undefined,
              borderRadius: 15,
              paddingHorizontal: 15,
              paddingVertical: 5,
              marginVertical: 3,
              marginRight: 3,
            }}
            onPress={() => setAnnotationType(AnnotationType.FIBRIN)}
          >
            <Text
              style={{
                fontWeight:
                  thrombusType === AnnotationType.FIBRIN ? 500 : undefined,
              }}
            >
              Fibrin
            </Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={{
            backgroundColor:
              thrombusType === AnnotationType.ERASE
                ? "rgb(255, 138, 196)"
                : "white",
            borderRadius: 20,
            padding: 10,
            boxShadow:
              thrombusType === AnnotationType.ERASE
                ? "0px 0px 10px 0px rgba(255, 138, 196, 0.1)"
                : "0px 0px 10px 0px rgba(0, 0, 0, 0.1)",
          }}
          disabled={loadingMask}
          onPress={() =>
            setAnnotationType(
              thrombusType === AnnotationType.ERASE
                ? AnnotationType.CLOT
                : AnnotationType.ERASE,
            )
          }
        >
          <MaterialCommunityIcons
            name="eraser"
            size={18}
            color={
              loadingMask || thrombusType !== AnnotationType.ERASE
                ? "#rgb(199,199,204)"
                : "white"
            }
          />
        </TouchableOpacity>

        <TouchableOpacity
          style={{
            backgroundColor: "white",
            borderRadius: 20,
            padding: 10,
            boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
          }}
          disabled={loadingMask}
          onPress={doUndo}
        >
          <MaterialCommunityIcons
            name="undo"
            size={18}
            color={loadingMask ? "gray" : "black"}
          />
        </TouchableOpacity>

        <TouchableOpacity
          style={{
            backgroundColor: "white",
            borderRadius: 20,
            padding: 10,
            boxShadow: "0px 0px 10px 0px rgba(0,0,0,0.1)",
          }}
          disabled={loadingMask}
          onPress={doRedo}
        >
          <MaterialCommunityIcons
            name="redo"
            size={18}
            color={loadingMask ? "gray" : "black"}
          />
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
