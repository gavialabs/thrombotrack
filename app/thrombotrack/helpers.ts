interface DataWithThumbnail {
  id: string;
  thumbnail: string | null;
}

// Load thumbnails for a list of objects in parallel and replace the base64 with blob URLs.
export const loadThumbnails = <T extends DataWithThumbnail>(
  data: T[],
  setState: (prev: (prev: any) => any) => void,
) => {
  data.forEach((d) => {
    if (d.thumbnail === null) {
      return;
    }

    fetch(`data:image/jpeg;base64,${d.thumbnail}`).then((r) =>
      r.blob().then((blob) => {
        setState((prev) =>
          prev.map((p: T) => {
            if (p.id === d.id) {
              return {
                ...p,
                thumbnail: URL.createObjectURL(blob),
              };
            } else {
              return p;
            }
          }),
        );
      }),
    );
  });
};

// Convert a base64 image string to ImageBitmap.
export const base64ToBitmap = async (
  base64: string,
  mimetype: string = "png",
): Promise<ImageBitmap> =>
  fetch(`data:${mimetype};base64,${base64}`)
    .then((r) => r.blob())
    .then((blob) => createImageBitmap(blob));
