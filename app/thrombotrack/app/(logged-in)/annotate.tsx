// Annotation screen to circle/tap on clots and fibrin

import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import {
  Redirect,
  useGlobalSearchParams,
  useNavigation,
  useRouter,
} from "expo-router";
import { FC, JSX, useEffect, useRef, useState } from "react";
import {
  View,
  Text,
  ActivityIndicator,
  TouchableOpacity,
  StyleSheet,
} from "react-native";

import { apiFetch } from "@/api";
import Canvas from "@/components/AnnotateCanvas";
import * as Colors from "@/constants/colors";
import { useStateContext } from "@/context/StateContext";
import AnnotateHeader from "@/components/AnnotateHeader";
import { Annotation, OxygenatorImage } from "@/constants/types";
import { base64ToBitmap } from "@/helpers";

enum AnnotationType {
  CLOT = "clot",
  FIBRIN = "fibrin",
  ERASE = "erase",
}

/**
 * The annotation page for circling/tapping on thrombi.
 */
const AnnotateScreen: FC = (): JSX.Element => {
  const { state, dispatch } = useStateContext();
  const navigation = useNavigation();
  const router = useRouter();
  const { oxygenatorId, oxygenatorImageId, disabled } = useGlobalSearchParams<{
    oxygenatorId: string;
    oxygenatorImageId?: string;
    disabled?: string;
  }>();

  const [isLoadingImage, setIsLoadingImage] = useState(true); // displays loading indicator
  const [image, setImage] = useState<ImageBitmap | null>(null); // cropped oxygenator image for annotations
  const [mask, setMask] = useState<ImageBitmap | null>(null); // overlay of existing annotations
  const [annotationType, setAnnotationType] = useState<AnnotationType>(
    AnnotationType.CLOT,
  ); // whether clot/fibrin/eraser is selected
  const [loadingMask, setLoadingMask] = useState(false); // disables annotations while loading
  const [hideMask, setHideMask] = useState(false); // hides annotations

  const imageIdRef = useRef<string | null>(oxygenatorImageId ?? null); // database oxygenator image id
  const annotationSessionIdRef = useRef<string | null>(null); // database annotation session id

  const isAnnotatingClot = annotationType === AnnotationType.CLOT;
  const isAnnotatingFibrin = annotationType === AnnotationType.FIBRIN;
  const isErasing = annotationType === AnnotationType.ERASE;
  const isAnnotationDisabled = annotationSessionIdRef.current === null;

  // Uploads the image stored in state context to API on page load, or fetches the specified image.
  useEffect(() => {
    if (
      oxygenatorId === undefined ||
      (state.file === null && oxygenatorImageId === undefined) ||
      dispatch === null ||
      !isLoadingImage
    ) {
      return;
    }

    if (state.file !== null) {
      // upload the image file stored in state context-- this means we just came from the home
      // screen after taking/selecting an image to upload
      const formData = new FormData();
      formData.append("image", state.file);

      apiFetch(`/oxygenators/${oxygenatorId}/oxygenator_images`, {
        method: "POST",
        body: formData,
      })
        .then(
          (
            data: Omit<OxygenatorImage, "thumbnail" | "created_at" | "mask">,
          ) => {
            imageIdRef.current = data.id;
            annotationSessionIdRef.current = data.current_annotation_session_id;
            return base64ToBitmap(data.cropped, data.mimetype);
          },
        )
        .then((bitmap) => setImage(bitmap))
        .catch((error): void => {
          console.error(error);
          router.back();
          window.alert("Failed to process image");
        })
        .finally(() => {
          setIsLoadingImage(false);
          dispatch({ type: "SET_FILE", payload: null });
        });
    } else {
      // fetch the image ID specified in URL params-- this means we just came from the gallery
      apiFetch(
        `/oxygenators/${oxygenatorId}/oxygenator_images/${oxygenatorImageId}?start_annotation_session=${disabled === "true" ? "false" : "true"}`,
      )
        .then(async (data: OxygenatorImage) => {
          // set the current annotation session ID-- if we are starting a new session
          // (disabled == false), this will be a new session ID, and if we are continuing an
          // unsaved session, this will be the existing session ID (otherwise null)
          console.log(data);
          annotationSessionIdRef.current = data.current_annotation_session_id;
          const imageBitmap = await base64ToBitmap(data.cropped, data.mimetype);
          setImage(imageBitmap);

          if (data.mask !== null) {
            const maskBitmap = await base64ToBitmap(data.mask);
            setMask(maskBitmap);
          }
        })
        .catch((error) => console.error(error))
        .finally(() => setIsLoadingImage(false));
    }
  }, [
    state.file,
    router,
    oxygenatorId,
    oxygenatorImageId,
    disabled,
    dispatch,
    isLoadingImage,
  ]);

  /**
   * Sets the title and function of the "Save" button in the header.
   *
   * Defined here rather than in AnnotateHeader for easier access to local variables.
   */
  useEffect(() => {
    // Marks the session as ended in the database and redirects to home screen.
    const doFinish = (): void => {
      apiFetch(
        `/oxygenators/${oxygenatorId}/oxygenator_images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}/end`,
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
      header: () => (
        <AnnotateHeader disabled={isAnnotationDisabled} onFinish={doFinish} />
      ),
    });
  }, [navigation, oxygenatorId, router, isAnnotationDisabled]);

  /**
   * Uploads an annotation path to the database.
   *
   * Converts float path coordinates into unique integers and updates `mask` with returned mask.
   *
   * @param path List of xy coordinates comprising the annotation.
   */
  const annotateImage = (path: [number, number][]): void => {
    if (path.length === 0) {
      console.error("Tried to annotate image with no points in path");
      return;
    }

    setLoadingMask(true);
    const distinctPath: [number, number][] = [];
    path.forEach((point) => {
      const intPoint: [number, number] = [
        Math.abs(Math.trunc(point[0])),
        Math.abs(Math.trunc(point[1])),
      ];
      if (
        !distinctPath.some(
          (point2) => point2[0] === intPoint[0] && point2[1] === intPoint[1],
        )
      ) {
        distinctPath.push(intPoint);
      }
    });

    apiFetch(
      `/oxygenators/${oxygenatorId}/oxygenator_images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}`,
      {
        method: "POST",
        body: {
          path: distinctPath,
          type: annotationType,
        },
      },
    )
      .then((data: Annotation) => base64ToBitmap(data.mask))
      .then((bitmap) => setMask(bitmap))
      .catch((error) => console.error(error))
      .finally(() => setLoadingMask(false));
  };

  // Hides or unhides mask of annotations.
  const doPressHide = (): void => {
    setHideMask(!hideMask);
  };

  const doPressErase = (): void => {
    setAnnotationType(isErasing ? AnnotationType.CLOT : AnnotationType.ERASE);
  };

  // Undoes the latest annotation.
  const doPressUndo = () => {
    setLoadingMask(true);
    apiFetch(
      `/oxygenators/${oxygenatorId}/oxygenator_images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}/undo`,
      {
        method: "POST",
      },
    )
      .then((data: Annotation) => base64ToBitmap(data.mask))
      .then((bitmap) => setMask(bitmap))
      .catch((error) => console.error(error))
      .finally(() => setLoadingMask(false));
  };

  // Redoes the latest undone annotation.
  const doPressRedo = () => {
    setLoadingMask(true);
    apiFetch(
      `/oxygenators/${oxygenatorId}/oxygenator_images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}/redo`,
      {
        method: "POST",
      },
    )
      .then((data: Annotation) => base64ToBitmap(data.mask))
      .then((bitmap) => setMask(bitmap))
      .catch((error) => console.error(error))
      .finally(() => setLoadingMask(false));
  };

  // Clears all existing annotations.
  const doPressClear = () => {
    setLoadingMask(true);
    apiFetch(
      `/oxygenators/${oxygenatorId}/oxygenator_images/${imageIdRef.current}/annotation_sessions/${annotationSessionIdRef.current}/clear`,
      {
        method: "POST",
      },
    )
      .then(() => setMask(null))
      .catch((error) => console.error(error))
      .finally(() => setLoadingMask(false));
  };

  const renderToolbar = (): JSX.Element => {
    const leftActions = [
      {
        key: "hide",
        color: Colors.INDIGO,
        icon: "eye-off",
        isActive: hideMask,
        onPress: doPressHide,
      },
    ];
    const rightActions = [];

    if (!isAnnotationDisabled) {
      leftActions.push({
        key: "erase",
        color: Colors.PINK,
        icon: "eraser",
        isActive: isErasing,
        onPress: doPressErase,
      });
      rightActions.push(
        {
          key: "undo",
          icon: "undo",
          onPress: doPressUndo,
        },
        {
          key: "redo",
          icon: "redo",
          onPress: doPressRedo,
        },
        {
          key: "clear",
          icon: "trash-can",
          color: Colors.RED,
          onPress: doPressClear,
        },
      );
    }

    return (
      <View style={styles.toolbar}>
        {/* Hide/erase buttons */}
        {leftActions.map((action) => (
          <TouchableOpacity
            key={action.key}
            disabled={loadingMask}
            onPress={action.onPress}
            style={[
              styles.basicAction,
              {
                backgroundColor: action.isActive ? action.color : undefined,
                boxShadow: hideMask
                  ? `0px 0px 10px 0px ${action.color}1a`
                  : undefined,
              },
            ]}
          >
            <MaterialCommunityIcons
              // @ts-ignore
              name={action.icon}
              size={18}
              color={!action.isActive ? Colors.GRAY : Colors.WHITE}
            />
          </TouchableOpacity>
        ))}

        {/* Clot/fibrin switch */}
        {!isAnnotationDisabled ? (
          <View style={styles.switch}>
            <TouchableOpacity
              style={[
                styles.switchButton,
                styles.switchButtonLeft,
                {
                  backgroundColor: isAnnotatingClot ? Colors.WHITE : undefined,
                },
              ]}
              onPress={() => setAnnotationType(AnnotationType.CLOT)}
            >
              <Text
                style={{
                  fontWeight: isAnnotatingClot ? 500 : undefined,
                }}
              >
                Clot
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.switchButton,
                styles.switchButtonRight,
                {
                  backgroundColor: isAnnotatingFibrin
                    ? Colors.WHITE
                    : undefined,
                },
              ]}
              onPress={() => setAnnotationType(AnnotationType.FIBRIN)}
            >
              <Text
                style={{
                  fontWeight: isAnnotatingFibrin ? 500 : undefined,
                }}
              >
                Fibrin
              </Text>
            </TouchableOpacity>
          </View>
        ) : null}

        {/* Undo/redo/clear buttons */}
        {rightActions.map((action) => (
          <TouchableOpacity
            key={action.key}
            disabled={loadingMask}
            onPress={action.onPress}
            style={styles.basicAction}
          >
            <MaterialCommunityIcons
              // @ts-ignore
              name={action.icon}
              size={18}
              color={loadingMask ? Colors.GRAY : action.color || Colors.BLACK}
            />
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  if (
    oxygenatorId === undefined ||
    (state.file === null && image === null && oxygenatorImageId === undefined)
  ) {
    return <Redirect href="/" />;
  }

  if (isLoadingImage || image === null) {
    return (
      <View
        // @ts-ignore
        style={[styles.loadingContainer, { height: "calc(100dvh - 50px)" }]}
      >
        <ActivityIndicator color={Colors.PURPLE} size="large" />
        <Text style={styles.loadingText}>Loading image...</Text>
      </View>
    );
  }

  return (
    // @ts-ignore
    <View style={[styles.container, { height: "calc(100dvh - 50px)" }]}>
      {/* Annotation canvas */}
      <Canvas
        annotateImage={annotateImage}
        disabled={isAnnotationDisabled}
        hideMask={hideMask}
        image={image}
        mask={mask}
      />

      {/* Toolbar-- must place after canvas so that it layers on top */}
      {renderToolbar()}
    </View>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    display: "flex",
    alignItems: "center",
    gap: 15,
    justifyContent: "center",
  },
  loadingText: { color: Colors.GRAY, fontSize: 16 },
  container: {
    display: "flex",
    justifyContent: "center",
    overflow: "hidden",
  },
  toolbar: {
    position: "absolute",
    top: 10,
    display: "flex",
    alignItems: "center",
    flexDirection: "row",
    gap: 10,
    alignSelf: "center",
  },
  basicAction: {
    backgroundColor: Colors.WHITE,
    borderRadius: 20,
    padding: 10,
    boxShadow: `0px 0px 10px 0px ${Colors.BLACK}1a`,
  },
  switch: {
    display: "flex",
    flex: 1,
    backgroundColor: Colors.GRAY_5,
    boxShadow: `0px 0px 10px 0px ${Colors.BLACK}1a`,
    flexDirection: "row",
    borderRadius: 20,
    alignItems: "center",
    borderColor: "white",
    overflow: "hidden",
    borderWidth: 3,
  },
  switchButton: {
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 5,
    marginVertical: 3,
    overflow: "hidden",
  },
  switchButtonLeft: {
    marginLeft: 3,
  },
  switchButtonRight: {
    marginRight: 3,
  },
});

export default AnnotateScreen;
