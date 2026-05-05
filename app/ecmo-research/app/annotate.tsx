import { ReactNativeZoomableView } from '@openspacelabs/react-native-zoomable-view';
import { Image } from "expo-image";
import { View, Text } from "react-native";
import { CanvasProvider } from '../components/CanvasContext';
import { Canvas } from '../components/Canvas';

export default function Annotate() {
  return (
    <CanvasProvider>
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
