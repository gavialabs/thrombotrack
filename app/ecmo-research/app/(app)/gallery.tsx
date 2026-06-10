import { useEffect, useState } from "react";
import { View, Text } from "react-native";
import { useGlobalSearchParams } from "expo-router";
import moment from "moment";
import { Image } from "expo-image";

const Gallery: React.FC = () => {
  const { ecmoId } = useGlobalSearchParams<{ ecmoId: string }>();
  const [images, setImages] = useState<{ [key: string]: any[] }>({});
  const [thumbnails, setThumbnails] = useState<{ [key: string]: string }>({});

  useEffect(() => {
    fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/ecmos/${ecmoId}/gallery`)
      .then((response) => response.json())
      .then((json) => {
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

        const imagesByDate: { [key: string]: any[] } = {};
        json.forEach((image) => {
          const date = moment(image.created_at).format("YYYY-MM-DD");
          if (!imagesByDate[date]) {
            imagesByDate[date] = [];
          }
          imagesByDate[date].push(image);
        });
        setImages(imagesByDate);
      });
  }, [ecmoId]);

  return (
    <View style={{ padding: 15 }}>
      {Object.keys(images).map((date) => (
        <View key={date}>
          <Text style={{ fontSize: 20, fontWeight: 700 }}>
            {moment(date).format("MMMM D, YYYY")}
          </Text>
          <View
            style={{
              flexDirection: "row",
              flexWrap: "wrap",
              justifyContent: "space-between",
            }}
          >
            {images[date].map((image) => (
              <View key={image.id}>
                {thumbnails[image.id] ? (
                  <Image
                    source={{ uri: thumbnails[image.id] }}
                    style={{ width: 100, height: 100 }}
                  />
                ) : (
                  <View
                    style={{
                      width: 100,
                      height: 100,
                      backgroundColor: "lightgray",
                      justifyContent: "center",
                      alignItems: "center",
                    }}
                  >
                    <Text>No Thumbnail</Text>
                  </View>
                )}
              </View>
            ))}
          </View>
        </View>
      ))}
    </View>
  );
};

export default Gallery;
