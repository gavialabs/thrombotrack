import React, { useEffect } from "react";
import { useCanvas } from "./CanvasContext";
import * as Device from "expo-device";

export function Canvas() {
  const { canvasRef, prepareCanvas, startDrawing, finishDrawing, draw } =
    useCanvas();

  const handleTouchEvent = (e) => {
    if (e.touches.length < 2) {
      e.preventDefault();
    }
  };

  useEffect(() => {
    const currentCanvas = canvasRef.current;

    currentCanvas.addEventListener("touchstart", handleTouchEvent, {
      passive: false,
    });

    prepareCanvas();

    return () => {
      currentCanvas.removeEventListener("touchstart", handleTouchEvent);
    };
  }, [canvasRef, prepareCanvas]);

  return (
    <canvas
      onMouseDown={startDrawing}
      onMouseUp={finishDrawing}
      onMouseMove={draw}
      onTouchStart={startDrawing}
      onTouchEnd={finishDrawing}
      onTouchMove={(e) => {
        if (e.touches.length < 2) {
          console.log("drawing");
          draw(e);
        }
      }}
      ref={canvasRef}
    />
  );
}
