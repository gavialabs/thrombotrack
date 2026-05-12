import React, { useContext, useRef, useState } from "react";

const CanvasContext = React.createContext();

export const CanvasProvider = ({
  children,
  ecmoImage,
  detectThrombus,
  masks,
}) => {
  const [isDrawing, setIsDrawing] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const contextRef = useRef<CanvasRenderingContext2D | null>(null);
  const originalImageRef = useRef<ImageBitmap | null>(null);

  const scaleRef = useRef(1);

  const path = useRef(new Set<[number, number]>());

  //defining width & height of the canvas
  const prepareCanvas = async (scaleOffset) => {
    const canvas = canvasRef.current;
    if (canvas === null) {
      return;
    }
    // canvas.width = window.innerWidth * 2;
    // canvas.height = window.innerHeight * 2;
    // canvas.style.width = `${window.innerWidth}px`;
    // canvas.style.height = `${window.innerHeight}px`;

    // defining the thickness and colour of our brush
    const ctx = canvas.getContext("2d");
    if (ctx === null) {
      return;
    }

    // const image = new Image();
    // const src = URL.createObjectURL(ecmoImage);
    // TODO - URL.revokeObjectURL(url)
    // image.src = src;
    // image.onload = () => {
    //   context.drawImage(
    //     image,
    //     0,
    //     0,
    //     // image.width,
    //     // image.height,
    //     window.innerWidth,
    //     (image.height / image.width) * window.innerWidth,
    //   );
    // };

    const originalImage = await createImageBitmap(ecmoImage);
    originalImageRef.current = originalImage;

    canvas.width = originalImage.width;
    canvas.height = originalImage.height;

    const scaleX = window.innerWidth / canvas.width;
    const scaleY = window.innerHeight / canvas.height;
    const scale = Math.min(scaleX, scaleY, 1) + scaleOffset; // never scale UP beyond 1:1

    scaleRef.current = scale + scaleOffset;

    console.log(`drawing with scale ${scale + scaleOffset}`);

    // CSS size controls how big it LOOKS
    canvas.style.width = `${canvas.width * scale}px`;
    canvas.style.height = `${canvas.height * scale}px`;

    ctx.drawImage(originalImage, 0, 0);
    masks.forEach((bitmap) => {
      const offscreen = new OffscreenCanvas(canvas.width, canvas.height);
      const offCtx = offscreen.getContext("2d");
      if (offCtx === null) {
        return;
      }

      offCtx.drawImage(bitmap, 0, 0);

      const maskData = offCtx.getImageData(
        0,
        0,
        canvas.width,
        canvas.height,
      ).data;

      // Read the current canvas pixels
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;

      const r = 100;
      const g = 149;
      const b = 237;
      const a = 1.0;

      // Only color pixels where the mask is non-zero
      for (let i = 0; i < maskData.length; i += 4) {
        if (maskData[i] > 0) {
          // check the red channel of the mask
          data[i + 0] = r;
          data[i + 1] = g;
          data[i + 2] = b;
          data[i + 3] = a;
        }
      }

      ctx.putImageData(imageData, 0, 0);
    });

    // context.scale(2, 2);
    ctx.lineCap = "round";
    ctx.strokeStyle = "cornflowerblue";
    ctx.lineWidth = 5;
    ctx.fillStyle = "cornflowerblue";

    contextRef.current = ctx;
  };

  const startDrawing = ({ nativeEvent }) => {
    const { clientX, clientY } = nativeEvent;

    const canvas = canvasRef.current;
    const ctx = contextRef.current;
    if (canvas === null || ctx === null) {
      return;
    }

    const rect = canvas.getBoundingClientRect();

    // CSS pixel position within the canvas element
    const cssX = clientX - rect.left;
    const cssY = clientY - rect.top;

    // Convert to image pixel coordinates
    const imageX = cssX / scaleRef.current;
    const imageY = cssY / scaleRef.current;

    // imageX, imageY are now in the original image's coordinate space
    // — safe to send directly to the backend
    // contextRef.current.beginPath();
    // contextRef.current.ellipse(layerX, layerY, 0.5, 0.5, 0, 0, Math.PI * 2);
    // contextRef.current.stroke();
    // contextRef.current.moveTo(layerX, layerY);
    // setIsDrawing(true);
    // path.current.add([layerX, layerY]);

    ctx.beginPath();
    // draw point at initial tap in case they are tapping and not circling
    ctx.ellipse(imageX, imageY, 0.5, 0.5, 0, 0, Math.PI * 2);
    ctx.stroke();

    ctx.moveTo(imageX, imageY);

    setIsDrawing(true);
    path.current.add([imageX, imageY]);
  };

  const finishDrawing = () => {
    const ctx = contextRef.current;
    if (ctx === null) {
      return;
    }

    ctx.closePath();
    setIsDrawing(false);

    let x1, y1, x2, y2;

    if (path.current.size === 1) {
      const pathArr = [...path.current];
      x1 = pathArr[0][0];
      y1 = pathArr[0][1];
    } else {
      const xVals: number[] = [];
      const yVals: number[] = [];

      path.current.forEach(([x, y]) => {
        xVals.push(x);
        yVals.push(y);
      });

      xVals.sort((a, b) => a - b);
      yVals.sort((a, b) => a - b);

      x1 = xVals[0];
      y1 = yVals[0];
      x2 = xVals[xVals.length - 1];
      y2 = yVals[yVals.length - 1];
    }

    // call endpoint
    // on response, clear canvas and reload image (this might clear it anyway)
    detectThrombus(x1, y1, x2, y2);
  };

  const draw = ({ nativeEvent }) => {
    const canvas = canvasRef.current;
    const ctx = contextRef.current;

    if (!isDrawing || canvas === null || ctx === null) {
      return;
    }

    const { clientX, clientY } = nativeEvent;

    const rect = canvas.getBoundingClientRect();

    // CSS pixel position within the canvas element
    const cssX = clientX - rect.left;
    const cssY = clientY - rect.top;

    // Convert to image pixel coordinates
    const imageX = cssX / scaleRef.current;
    const imageY = cssY / scaleRef.current;

    ctx.lineTo(imageX, imageY);
    ctx.stroke();

    path.current.add([imageX, imageY]);
  };

  //once the canvas is cleared it return to the default colour
  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");
    context.fillStyle = "white";
    context.fillRect(0, 0, canvas.width, canvas.height);
  };

  return (
    <CanvasContext.Provider
      value={{
        canvasRef,
        contextRef,
        prepareCanvas,
        startDrawing,
        finishDrawing,
        clearCanvas,
        draw,
      }}
    >
      {children}
    </CanvasContext.Provider>
  );
};

export const useCanvas = () => useContext(CanvasContext);
