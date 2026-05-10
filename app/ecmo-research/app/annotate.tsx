import { ReactNativeZoomableView } from "@openspacelabs/react-native-zoomable-view";
import { Image } from "expo-image";
import { View, Text, Alert, ActivityIndicator } from "react-native";
import { CanvasProvider } from "../components/CanvasContext";
import { Canvas } from "../components/Canvas";
import { useStateContext } from "@/components/StateContext";
import { useEffect, useState } from "react";
import { Redirect, useGlobalSearchParams, useRouter } from "expo-router";

export default function Annotate() {
  const { state, dispatch } = useStateContext();
  const router = useRouter();
  const { ecmoId } = useGlobalSearchParams<{ ecmoId: string }>();
  const [loading, setLoading] = useState(true);
  const [image, setImage] = useState(null);
  const [imageId, setImageId] = useState(null);

  useEffect(() => {
    const uploadImage = (file: File): void => {
      const formData = new FormData();
      formData.append("image", file);

      fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmo/${ecmoId}`, {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then(async (json) => {
          setLoading(false);
          setImageId(json.image_id);
          const blob = await fetch(
            `data:${json.mime_type};base64,${json.image}`,
          ).then((r) => r.blob());
          setImage(blob);
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

  const detectClotOrFibrin = (path: Set<[number, number]>): void => {
    let payload = {};

    if (path.size === 1) {
      // single tap
      payload = {
        tap: [...path][0],
      };
    } else {
      const xVals: number[] = [];
      const yVals: number[] = [];

      path.forEach(([x, y]) => {
        xVals.push(x);
        yVals.push(y);
      });

      xVals.sort((a, b) => a - b);
      yVals.sort((a, b) => a - b);

      const corner1 = [xVals[0], yVals[0]];
      const corner2 = [xVals[xVals.length - 1], yVals[yVals.length - 1]];

      payload = {
        corner1,
        corner2,
      };
    }

    fetch(
      `${process.env.EXPO_PUBLIC_API_URL}/api/ecmo/${ecmoId}/images/${imageId}/annotations`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    )
      .then((response) => {
        
      })
      .catch((error) => {
        console.error(error);
        window.alert("Failed to process image");
        router.back();
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
    <CanvasProvider ecmoImage={image} detectClotOrFibrin={detectClotOrFibrin}>
      {/* <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', }}>
        <Image
          allowDownscaling={false}
          source={require("../assets/images/IMG_4452c.jpg")}
          contentFit="contain"
          style={{ flex: 1, width: "100%" }}
          onPointerDown={(event) => console.log(event)}
          // on
        />
      </View> */}
      <Canvas />
    </CanvasProvider>
  );
}
