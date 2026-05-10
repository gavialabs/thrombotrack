import React, { useContext, useRef, useState } from "react";

const CanvasContext = React.createContext();

export const CanvasProvider = ({ children, ecmoImage, detectClotOrFibrin }) => {
  const [isDrawing, setIsDrawing] = useState(false);
  const canvasRef = useRef(null);
  const contextRef = useRef(null);
  
  const path = useRef(new Set<[number, number]>());

  //defining width & height of the canvas
  const prepareCanvas = () => {
    const canvas = canvasRef.current;
    canvas.width = window.innerWidth * 2;
    canvas.height = window.innerHeight * 2;
    canvas.style.width = `${window.innerWidth}px`;
    canvas.style.height = `${window.innerHeight}px`;

    // defining the thickness and colour of our brush
    const context = canvas.getContext("2d");

    const image = new Image();
    const src = URL.createObjectURL(ecmoImage);
    // TODO - URL.revokeObjectURL(url)
    image.src = src;
    image.onload = () => {
      context.drawImage(
        image,
        0,
        0,
        window.innerWidth,
        (image.height / image.width) * window.innerWidth,
      );
    };

    context.scale(2, 2);
    context.lineCap = "round";
    context.strokeStyle = "cornflowerblue";
    context.lineWidth = 5;
    context.fillStyle = "cornflowerblue";
    contextRef.current = context;
  };

  const startDrawing = ({ nativeEvent }) => {
    const { layerX, layerY } = nativeEvent;
    contextRef.current.beginPath();
    contextRef.current.ellipse(layerX, layerY, 0.5, 0.5, 0, 0, Math.PI * 2);
    contextRef.current.stroke();
    contextRef.current.moveTo(layerX, layerY);
    setIsDrawing(true);
    path.current.add([layerX, layerY]);
  };

  const finishDrawing = () => {
    contextRef.current.closePath();
    setIsDrawing(false);

    // call endpoint
    // on response, clear canvas and reload image (this might clear it anyway)
    detectClotOrFibrin(path.current);
  };

  const draw = ({ nativeEvent }) => {
    if (!isDrawing) {
      return;
    }

    const { layerX, layerY } = nativeEvent;
    contextRef.current.lineTo(layerX, layerY);
    contextRef.current.stroke();
    path.current.add([layerX, layerY]);
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
