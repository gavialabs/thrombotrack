import React, { useEffect, useRef, useState } from "react";

interface CanvasProps {
  image: Blob;
  mask: Blob | null;
  annotateImage: (path: [number, number][]) => void;
}

type Coordinate = {
  x: number;
  y: number;
};

const Canvas = ({ image, mask, annotateImage }: CanvasProps) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const contextRef = useRef<CanvasRenderingContext2D | null>(null);

  // zoom + panning
  const imageScaleRef = useRef<number>(1);
  const cssScaleRef = useRef<number>(1);
  const lastPinchDistanceRef = useRef<number>(1);
  const originRef = useRef<Coordinate>({ x: 0, y: 0 });
  const lastPinchMidpointRef = useRef<Coordinate>({ x: 0, y: 0 });

  // drawing
  const pathRef = useRef<[number, number][]>([]);
  const [isDrawing, setIsDrawing] = useState(false);

  useEffect(() => {
    const prepareCanvas = async () => {
      const canvas = canvasRef.current;
      if (canvas === null) {
        return;
      }

      const ctx = canvas.getContext("2d");
      if (ctx === null) {
        return;
      }

      // convert blob to image bitmap so it can be drawn on canvas
      const originalImage = await createImageBitmap(image);

      // make canvas represent every pixel of original image
      canvas.width = originalImage.width;
      canvas.height = originalImage.height;

      // use css to set the displayed size so full image is shown
      const scaleX = window.innerWidth / canvas.width;
      const scaleY = window.innerHeight / canvas.height;

      // save the scaling factor from original size -> css size
      imageScaleRef.current = Math.min(scaleX, scaleY, 1);

      canvas.style.width = `${canvas.width * imageScaleRef.current}px`;
      canvas.style.height = `${canvas.height * imageScaleRef.current}px`;

      // display image
      ctx.drawImage(originalImage, 0, 0);

      // overlay mask with annotations
      if (mask !== null) {
        const maskImage = await createImageBitmap(mask);
        ctx.globalAlpha = 0.5;
        ctx.drawImage(maskImage, 0, 0);
        ctx.globalAlpha = 1.0;
      }

      // setup paintbrush
      ctx.lineCap = "round";
      ctx.strokeStyle = "#38b6ff";
      ctx.lineWidth = 5;

      contextRef.current = ctx;
    };

    prepareCanvas();
  }, [image, mask]);

  useEffect(() => {
    const getPinchDistance = (touches: TouchList) => {
      // get the distance between the user's fingers while pinching to zoom
      const dx = touches[0].clientX - touches[1].clientX;
      const dy = touches[0].clientY - touches[1].clientY;
      return Math.sqrt(dx * dx + dy * dy);
    };

    const doTouchStart = (e: TouchEvent) => {
      if (e.touches.length === 2) {
        e.preventDefault();

        // record baseline pinch distance
        lastPinchDistanceRef.current = getPinchDistance(e.touches);
        lastPinchMidpointRef.current = {
          // @ts-ignore
          x: e.layerX,
          // @ts-ignore
          y: e.layerY,
        };
      } else if (e.touches.length === 1) {
        startDrawing(e);
      }
    };

    const doTouchMove = (e: TouchEvent) => {
      const draw = (e: TouchEvent) => {
        const canvas = canvasRef.current;
        const ctx = contextRef.current;

        // !isDrawing
        if (canvas === null || ctx === null) {
          return;
        }

        // @ts-ignore
        const { layerX, layerY } = e;

        const imageX = cssToImagePoint(layerX, originRef.current.x);
        const imageY = cssToImagePoint(layerY, originRef.current.y);

        ctx.lineTo(imageX, imageY);
        ctx.stroke();

        pathRef.current.push([imageX, imageY]);
      };

      if (e.touches.length === 2) {
        const canvas = canvasRef.current;
        const ctx = contextRef.current;

        if (canvas === null || ctx === null) {
          return;
        }

        const currentPinchDistance = getPinchDistance(e.touches);
        const zoom = currentPinchDistance / lastPinchDistanceRef.current;

        const currentScale = cssScaleRef.current;
        // don't allow zooming out more than original scale, max 10x zoom
        const newScale = Math.min(Math.max(currentScale * zoom, 1), 10);

        let newOriginX = 0;
        let newOriginY = 0;
        if (newScale > 1) {
          // @ts-ignore
          const { layerX, layerY } = e; // midpoint of the user's fingers

          // set origin to zoomed location
          newOriginX =
            layerX -
            (layerX - originRef.current.x) * (newScale / cssScaleRef.current);
          newOriginY =
            layerY -
            (layerY - originRef.current.y) * (newScale / cssScaleRef.current);

          // pan origin by amount fingers moved
          newOriginX += layerX - lastPinchMidpointRef.current.x;
          newOriginY += layerY - lastPinchMidpointRef.current.y;

          // prevent panning x off-screen
          const scaledWidth = canvas.width * imageScaleRef.current * newScale;

          const minX = Math.min(0, window.innerWidth - scaledWidth);
          const maxX = Math.max(0, window.innerWidth - scaledWidth);

          newOriginX = Math.min(Math.max(newOriginX, minX), maxX);

          // TODO - prevent panning the y off-screen
        }

        // apply transform, add z component to possibly enable GPU acceleration
        canvas.style.transform = `translate(${newOriginX}px, ${newOriginY}px) scale(${newScale}) translateZ(0)`;

        lastPinchDistanceRef.current = currentPinchDistance;
        cssScaleRef.current = newScale;
        originRef.current = {
          x: newOriginX,
          y: newOriginY,
        };
        lastPinchMidpointRef.current = {
          // @ts-ignore
          x: e.layerX,
          // @ts-ignore
          y: e.layerY,
        };
      } else if (e.touches.length === 1) {
        draw(e);
      }
    };

    const doTouchEnd = (e: TouchEvent) => {
      const finishDrawing = () => {
        const ctx = contextRef.current;
        if (ctx === null) {
          return;
        }

        annotateImage([...pathRef.current]);

        pathRef.current = [];
      };

      if (e.changedTouches.length === 1 && e.touches.length === 0) {
        finishDrawing();
      }
    };

    const canvas = canvasRef.current;
    if (canvas === null) {
      return;
    }

    canvas.addEventListener("touchstart", doTouchStart, {
      passive: false,
    });
    canvas.addEventListener("touchmove", doTouchMove);
    canvas.addEventListener("touchend", doTouchEnd);

    return () => {
      canvas.removeEventListener("touchstart", doTouchStart);
      canvas.removeEventListener("touchmove", doTouchMove);
      canvas.removeEventListener("touchend", doTouchEnd);
    };
  }, [annotateImage]);

  const startDrawing = (e: TouchEvent) => {
    // @ts-ignore
    const { layerX, layerY } = e;

    const canvas = canvasRef.current;
    const ctx = contextRef.current;
    if (canvas === null || ctx === null) {
      return;
    }

    const imageX =
      (layerX - originRef.current.x) /
      imageScaleRef.current /
      cssScaleRef.current;
    const imageY =
      (layerY - originRef.current.y) /
      imageScaleRef.current /
      cssScaleRef.current;

    ctx.beginPath();
    // draw point at initial tap in case they are tapping and not circling
    ctx.ellipse(imageX, imageY, 0.5, 0.5, 0, 0, Math.PI * 2);
    ctx.stroke();

    ctx.moveTo(imageX, imageY);

    setIsDrawing(true);
    pathRef.current.push([imageX, imageY]);
  };

  const cssToImagePoint = (point: number, origin: number): number =>
    (point - origin) / imageScaleRef.current / cssScaleRef.current;

  return <canvas ref={canvasRef} style={{ transformOrigin: "0 0" }} />;
};

export default Canvas;
