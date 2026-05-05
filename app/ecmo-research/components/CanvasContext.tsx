import React, { useContext, useRef, useState } from "react";
import ecmoImage from "./IMG_4452c.jpg";

// enabling drawing on the blank canvas
const CanvasContext = React.createContext();

export const CanvasProvider = ({ children }) => {
  const [isDrawing, setIsDrawing] = useState(false);
  const canvasRef = useRef(null);
  const contextRef = useRef(null);

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
    // image.src = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Picture_icon_BLACK.svg/1200px-Picture_icon_BLACK.svg.png";
    console.log(image);
    console.log(image.src);
    console.log(ecmoImage);
    image.src = ecmoImage.uri;
    console.log(image);
    console.log(image.src);
    // image.src = require("./IMG_4452c.jpg");
    image.onload = () => {
      context.drawImage(image, 0, 0, window.innerWidth, image.height / image.width * window.innerWidth);
    };

    context.scale(2, 2);
    context.lineCap = "round";
    context.strokeStyle = "black";
    context.lineWidth = 5;
    contextRef.current = context;
  };

  const startDrawing = ({ nativeEvent }) => {
    console.log(nativeEvent);

    const { offsetX, offsetY, layerX, layerY } = nativeEvent;
    contextRef.current.beginPath();
    contextRef.current.moveTo(layerX, layerY);
    setIsDrawing(true);
  };

  const finishDrawing = () => {
    contextRef.current.closePath();
    setIsDrawing(false);
  };

  const draw = ({ nativeEvent }) => {
    if (!isDrawing) {
      return;
    }
    const { offsetX, offsetY, layerX, layerY } = nativeEvent;
    contextRef.current.lineTo(layerX, layerY);
    contextRef.current.stroke();
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
        draw
      }}
    >
      {children}
    </CanvasContext.Provider>
  );
};

export const useCanvas = () => useContext(CanvasContext);
