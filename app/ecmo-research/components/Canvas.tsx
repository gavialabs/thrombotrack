import React, { useEffect } from "react";
import { useCanvas } from "./CanvasContext";
import Background from "../../assets/images/IMG_4452c.jpg";

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
      onTouchStart={(e) => {
        startDrawing(e);
      }}
      onTouchEnd={finishDrawing}
      onTouchMove={(e) => {
        if (e.touches.length < 2) {
          draw(e);
        }
      }}
      ref={canvasRef}
    />
  );
}
