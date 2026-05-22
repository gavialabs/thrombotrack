import React, { useContext, useRef, useState } from "react";

const CanvasContext = React.createContext();

export const CanvasProvider = ({
  children,
  ecmoImage,
  detectThrombus,
  mask,
}) => {
  const [isDrawing, setIsDrawing] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const contextRef = useRef<CanvasRenderingContext2D | null>(null);
  const originalImageRef = useRef<ImageBitmap | null>(null);
  const actualScale = useRef(1);
  const scale = useRef(1);
  const originX = useRef(0);
  const originY = useRef(0);

  const path = useRef(new Set<[number, number]>());

  const prepareCanvas = async () => {
    const canvas = canvasRef.current;
    if (canvas === null) {
      return;
    }
    const ctx = canvas.getContext("2d");
    if (ctx === null) {
      return;
    }

    const originalImage = await createImageBitmap(ecmoImage);
    originalImageRef.current = originalImage;

    canvas.width = originalImage.width;
    canvas.height = originalImage.height;

    const scaleX = window.innerWidth / canvas.width;
    const scaleY = window.innerHeight / canvas.height;
    actualScale.current = Math.min(scaleX, scaleY, 1);

    // CSS size controls how big it LOOKS
    canvas.style.width = `${canvas.width * actualScale.current}px`;
    canvas.style.height = `${canvas.height * actualScale.current}px`;

    ctx.drawImage(originalImage, 0, 0);

    // draw current mask
    if (mask !== null) {
      const offscreen = new OffscreenCanvas(canvas.width, canvas.height);
      const offCtx = offscreen.getContext("2d");
      if (offCtx === null) {
        return;
      }

      offCtx.drawImage(mask, 0, 0);

      const maskData = offCtx.getImageData(
        0,
        0,
        canvas.width,
        canvas.height,
      ).data;

      // Read the current canvas pixels
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imageData.data;

      // Only color pixels where the mask is non-zero
      for (let i = 0; i < maskData.length; i += 4) {
        if (maskData[i] === 255) {
          data[i] = 100;
          data[i + 1] = 149;
          data[i + 2] = 237;
        }
      }

      ctx.putImageData(imageData, 0, 0);
      // ctx.drawImage(offscreen, 0, 0);
    }

    // context.scale(2, 2);
    ctx.lineCap = "round";
    ctx.strokeStyle = "cornflowerblue";
    ctx.lineWidth = 5;
    ctx.fillStyle = "cornflowerblue";

    contextRef.current = ctx;
  };

  const startDrawing = ({ nativeEvent }) => {
    const { layerX, layerY } = nativeEvent;

    const canvas = canvasRef.current;
    const ctx = contextRef.current;
    if (canvas === null || ctx === null) {
      return;
    }

    // const rect = canvas.getBoundingClientRect();

    // CSS pixel position within the canvas element
    // const cssX = layerX - rect.left;
    // const cssY = layerY - rect.top;

    const imageX =
      (layerX - originX.current) / actualScale.current / scale.current;
    const imageY =
      (layerY - originY.current) / actualScale.current / scale.current;

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

  const draw = ({ nativeEvent }) => {
    const canvas = canvasRef.current;
    const ctx = contextRef.current;

    if (!isDrawing || canvas === null || ctx === null) {
      return;
    }

    const { layerX, layerY } = nativeEvent;

    // const rect = canvas.getBoundingClientRect();

    // // CSS pixel position within the canvas element
    // const cssX = layerX - rect.left;
    // const cssY = layerY - rect.top;

    // Convert to image pixel coordinates
    const imageX =
      (layerX - originX.current) / actualScale.current / scale.current;
    const imageY =
      (layerY - originY.current) / actualScale.current / scale.current;

    ctx.lineTo(imageX, imageY);
    ctx.stroke();

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
    // detectThrombus(x1, y1, x2, y2);
    path.current = new Set();
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
        scale,
        originX,
        originY,
      }}
    >
      {children}
    </CanvasContext.Provider>
  );
};

export const useCanvas = () => useContext(CanvasContext);
