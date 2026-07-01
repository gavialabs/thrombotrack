// Auto-scrolls to top of each page (fixes issue with scroll position persisting between pages on web)

import { FC, useEffect } from "react";
import { usePathname } from "expo-router";
import { Platform } from "react-native";

const ScrollToTop: FC = () => {
  const pathname = usePathname();

  useEffect(() => {
    if (Platform.OS === "web") {
      window.scrollTo(0, 0);
    }
  }, [pathname]);

  return null;
};

export default ScrollToTop;
