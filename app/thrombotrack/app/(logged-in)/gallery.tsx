// Image history gallery

import { JSX, useEffect, useMemo, useState } from "react";
import {
  View,
  Text,
  useWindowDimensions,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { useGlobalSearchParams, useRouter } from "expo-router";
import moment from "moment";
import { Image } from "expo-image";
import { apiFetch } from "@/api";
import { OxygenatorImage } from "@/constants/types";
import { loadThumbnails } from "@/helpers";
import { PURPLE } from "@/constants/colors";

type GalleryImage = Pick<OxygenatorImage, "id" | "created_at"> &
  Partial<Pick<OxygenatorImage, "thumbnail">>;

// Displays a gallery of past images for this oxygenator
const GalleryScreen: React.FC = (): JSX.Element => {
  const { oxygenatorId } = useGlobalSearchParams<{ oxygenatorId: string }>();
  const { width } = useWindowDimensions();
  const router = useRouter();

  const [images, setImages] = useState<GalleryImage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const imagesByDate = useMemo(() => {
    const newImagesByDate: Record<string, GalleryImage[]> = {};

    images.forEach((image) => {
      const date = moment(image.created_at).format("YYYY-MM-DD");
      if (!newImagesByDate[date]) {
        newImagesByDate[date] = [];
      }
      newImagesByDate[date].push(image);
    });

    return newImagesByDate;
  }, [images]);

  const imageWidth = (width - 8) / 3;

  useEffect(() => {
    if (oxygenatorId === undefined || !isLoading) {
      return;
    }

    apiFetch(`/oxygenators/${oxygenatorId}/oxygenator_images`).then(
      (images: Required<GalleryImage>[]) => {
        setIsLoading(false);
        setImages(
          images.map((image) => ({
            ...image,
            thumbnail: undefined, // temporarily set to null while loadThumbnails loads the blobs
          })),
        );
        loadThumbnails(images, setImages);
      },
    );
  }, [oxygenatorId, isLoading]);

  // Navigate to the annotation screen with this image ID and annotations disabled.
  // NOTE - if re-annotation functionality is desired, change disabled to false here. can also just
  // be temporarily overriden in the URL for one-off use.
  const doPressImage = (oxygenatorImageId: string) => {
    router.navigate({
      pathname: "/annotate",
      params: { oxygenatorId, oxygenatorImageId, disabled: "true" },
    });
  };

  return (
    <View style={{ paddingHorizontal: 2, paddingTop: 15, gap: 20 }}>
      {isLoading ? (
        <ActivityIndicator size="large" color={PURPLE} />
      ) : (
        Object.keys(imagesByDate).map((date) => (
          <View key={date}>
            <Text
              style={{
                fontSize: 20,
                fontWeight: 700,
                marginBottom: 10,
                marginLeft: 20,
              }}
            >
              {moment(date).format("MMMM D, YYYY")}
            </Text>
            <View
              style={{
                flexDirection: "row",
                flexWrap: "wrap",
                gap: 2,
              }}
            >
              {imagesByDate[date].map((image) => (
                <TouchableOpacity
                  key={image.id}
                  onPress={() => doPressImage(image.id)}
                  style={{ borderRadius: 3, overflow: "hidden" }}
                >
                  {image.thumbnail !== undefined ? (
                    <Image
                      source={{ uri: image.thumbnail }}
                      style={{ width: imageWidth, height: imageWidth }}
                    />
                  ) : (
                    <View
                      style={{
                        width: imageWidth,
                        height: imageWidth,
                        backgroundColor: "lightgray",
                        justifyContent: "center",
                        alignItems: "center",
                      }}
                    />
                  )}
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))
      )}
    </View>
  );
};

export default GalleryScreen;
