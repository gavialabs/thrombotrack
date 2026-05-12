import React, { useEffect } from "react";
import { useCanvas } from "./CanvasContext";

export function Canvas({ scaleOffset }) {
  const { canvasRef, prepareCanvas, startDrawing, finishDrawing, draw } =
    useCanvas();

  const handleTouchEvent = (e) => {
    if (e.touches.length < 2) {
      e.preventDefault();
    }

    if (e.touches.length === 2) {
      e.preventDefault();
    }
  };

  // const handlePan = (e) => {
  //   if (e.touches.length === 2) {

  //   }
  // };

  useEffect(() => {
    const currentCanvas = canvasRef.current;

    currentCanvas.addEventListener("touchstart", handleTouchEvent, {
      passive: false,
    });
    
    // currentCanvas.addEventListener("touchmove", handlePan, {
    //   passive: false,
    // });

    prepareCanvas(scaleOffset);

    return () => {
      currentCanvas.removeEventListener("touchstart", handleTouchEvent);
    };
  }, [canvasRef, prepareCanvas, scaleOffset]);

  return (
    <canvas
      onMouseDown={startDrawing}
      onMouseUp={finishDrawing}
      onMouseMove={draw}
      onTouchStart={startDrawing}
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
