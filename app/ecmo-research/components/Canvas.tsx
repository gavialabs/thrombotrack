import React, { useEffect, useRef } from "react";
import { useCanvas } from "./CanvasContext";

export function Canvas() {
  const {
    canvasRef,
    contextRef,
    prepareCanvas,
    startDrawing,
    finishDrawing,
    draw,
    scale,
    originX,
    originY,
  } = useCanvas();
  const lastPinchDistance = useRef(null);
  const lastPinchMidpoint = useRef(null);

  const getPinchDistance = (touches) => {
    const dx = touches[0].clientX - touches[1].clientX;
    const dy = touches[0].clientY - touches[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  const getPinchMidpoint = (touches) => {
    return {
      x: (touches[0].clientX + touches[1].clientX) / 2,
      y: (touches[0].clientY + touches[1].clientY) / 2,
    };
  };

  useEffect(() => {
    const applyTransform = () => {
      canvasRef.current.style.transform = `translate(${originX.current}px, ${originY.current}px) scale(${scale.current})`;
      canvasRef.current.style.transformOrigin = "0 0";
    };

    const zoomAt = (newScale, cssX, cssY) => {
      newScale = Math.min(Math.max(newScale, 1), 6);

      // Adjust origin so the point under (cssX, cssY) stays fixed on screen
      if (newScale === 1) {
        // when zoomed out entirely, don't want image to be translated at all
        originX.current = 0;
        originY.current = 0;
      } else {
        originX.current =
          cssX - (cssX - originX.current) * (newScale / scale.current);
        originY.current =
          cssY - (cssY - originY.current) * (newScale / scale.current);
      }
      scale.current = newScale;

      contextRef.current.translate(originX.current, originY.current);
      contextRef.current.scale(newScale, newScale);
      // contextRef.current.scale(newScale, newScale);

      // applyTransform();
    };

    const handleTouchStart = (e) => {
      console.log(e);
      e.preventDefault();

      if (e.touches.length === 2) {
        // Start of pinch — record initial distance and midpoint
        lastPinchDistance.current = getPinchDistance(e.touches);
        lastPinchMidpoint.current = getPinchMidpoint(e.touches);
        // lastPinchMidpoint.current = { x: e.pageX, y: e.pageY };
      } else {
        startDrawing(e);
      }
    };

    const handleTouchMove = (e) => {
      e.preventDefault();

      if (e.touches.length === 2) {
        const newDistance = getPinchDistance(e.touches);
        const newMidpoint = getPinchMidpoint(e.touches);

        // Scale proportionally to the change in pinch distance
        const newScale =
          scale.current * (newDistance / lastPinchDistance.current);
        // console.log(scale.current);
        // console.log(e.scale);
        // const newScale = scale.current * e.scale;
        // console.log(newScale);

        // Zoom centered on the midpoint between the two fingers
        // zoomAt(newScale, newMidpoint.x, newMidpoint.y);
        zoomAt(newScale, e.pageX, e.pageY);

        // Also pan by how much the midpoint itself moved
        // originX.current += newMidpoint.x - lastPinchMidpoint.current.x;
        // originY.current += newMidpoint.y - lastPinchMidpoint.current.y;
        // originX.current += e.pageX - lastPinchMidpoint.current.x;
        // originY.current += e.pageY - lastPinchMidpoint.current.y;
        // console.log(`panning x by ${e.pageX - lastPinchMidpoint.current.x}`);
        // console.log(`panning y by ${e.pageY - lastPinchMidpoint.current.y}`)
        // applyTransform();

        // lastPinchDistance.current = newDistance;
        lastPinchMidpoint.current = {
          x: e.pageX,
          y: e.pageY,
        };
      } else {
        draw(e);
      }
    };

    const handleTouchEnd = (e) => {
      e.preventDefault();

      // TODO - event has a scale attribute, could we use this instead of calculating pinch distance?

      // if (e.changedTouches.length < 2) {
      if (e.touches.length < 2) {
        finishDrawing(e);
      }

      if (e.touches.length < 2) {
        lastPinchDistance.current = null;
        lastPinchMidpoint.current = null;
      }
    };

    const currentCanvas = canvasRef.current;

    currentCanvas.addEventListener("touchstart", handleTouchStart, {
      passive: false,
    });
    currentCanvas.addEventListener("touchmove", handleTouchMove, {
      passive: false,
    });
    currentCanvas.addEventListener("touchend", handleTouchEnd, {
      passive: false,
    });

    prepareCanvas();

    return () => {
      currentCanvas.removeEventListener("touchstart", handleTouchStart);
      currentCanvas.removeEventListener("touchmove", handleTouchMove);
      currentCanvas.removeEventListener("touchend", handleTouchEnd);
    };
  }, [
    canvasRef,
    prepareCanvas,
    draw,
    finishDrawing,
    startDrawing,
    // lastPinchDistance,
    // lastPinchMidpoint,
    // originX,
    // originY,
    // scale,
  ]);

  return (
    <canvas
      onMouseDown={startDrawing}
      onMouseMove={draw}
      onMouseUp={finishDrawing}
      ref={canvasRef}
    />
  );
}
