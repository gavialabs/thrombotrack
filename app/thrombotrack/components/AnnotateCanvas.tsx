// Canvas for drawing on image to create annotations

import { FC, JSX, useEffect, useRef } from "react";

type AnnotateCanvasProps = {
  disabled: boolean;
  image: ImageBitmap;
  mask: ImageBitmap | null;
  annotateImage: (path: [number, number][]) => void;
  hideMask: boolean;
};

type Coordinate = {
  x: number;
  y: number;
};

/**
 * Renders annotation canvas.
 *
 * Uses an HTML <canvas> component to draw the image and allow drawing on it. Overrides zoom and
 * scroll to implement our own fake zooming and scrolling. After a drawing is completed, sends to
 * backend to segment the circled/tapped region and get an updated mask of annotations to display
 * on top of the image.
 *
 * IMPORTANT NOTE: Concept of CSS pixels vs. image pixels. The image is about 1500x1500. The HTML
 * page is about 400px wide. HTML canvas is set to render all 1500 pixels, but display in 400. So,
 * at every step, we must convert between the two pixel spaces.
 *
 * @param props Props containing image, current mask, function to call API to create annotations,
 *  and whether or not mask should be hidden.
 *
 * @returns Annotation canvas component.
 */
const AnnotateCanvas: FC<AnnotateCanvasProps> = ({
  disabled,
  image,
  mask,
  annotateImage,
  hideMask,
}): JSX.Element => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const contextRef = useRef<CanvasRenderingContext2D | null>(null);

  // zoom + panning
  const imageScaleRef = useRef<number>(1); // scaling factor to display the entire image on screen
  const cssScaleRef = useRef<number>(1); // how much the user is zooming
  const lastPinchDistanceRef = useRef<number>(1); // distance between user's fingers zooming
  const originRef = useRef<Coordinate>({ x: 0, y: 0 }); // origin of image (used for panning)
  const lastPinchMidpointRef = useRef<Coordinate>({ x: 0, y: 0 }); // midpoint of user's fingers zooming/panning

  // drawing: use refs here so that we don't trigger state updates while drawing
  const pathRef = useRef<[number, number][]>([]); // xy coordinates of annotation on image
  const isDrawingRef = useRef<boolean>(false); // whether we are currently drawing

  /**
   * Converts from a CSS pixel value to image pixel value.
   *
   * @param point CSS pixel coordinate to convert.
   * @param origin Current origin of image due to panning.
   *
   * @returns Image pixel coordinate.
   */
  const cssToImagePoint = (point: number, origin: number): number =>
    (point - origin) / imageScaleRef.current / cssScaleRef.current;

  /**
   * Draw image and mask of annotations.
   *
   * Runs on initial load, after every annotation is made, and when hiding/unhiding annotations.
   * Scales image to fit on entire screen and saves scaling factor used, so we can convert from
   * image pixels to CSS pixels.
   */
  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas === null) {
      return;
    }

    const ctx = canvas.getContext("2d");
    if (ctx === null) {
      return;
    }

    // make canvas represent every pixel of original image
    canvas.width = image.width;
    canvas.height = image.height;

    // use css to set the displayed size so full image is shown
    const scaleX = window.innerWidth / canvas.width;
    const scaleY = window.innerHeight / canvas.height;

    // save the scaling factor from original size -> css size
    imageScaleRef.current = Math.min(scaleX, scaleY, 1);

    canvas.style.width = `${canvas.width * imageScaleRef.current}px`;
    canvas.style.height = `${canvas.height * imageScaleRef.current}px`;

    // display image
    ctx.drawImage(image, 0, 0);

    // overlay mask with annotations
    if (mask !== null && !hideMask) {
      ctx.globalAlpha = 0.5;
      ctx.drawImage(mask, 0, 0);
      ctx.globalAlpha = 1.0;
    }

    // setup paintbrush
    ctx.lineCap = "round";
    ctx.strokeStyle = "#38b6ff";
    ctx.lineWidth = 5;

    contextRef.current = ctx;
  }, [image, mask, hideMask]);

  /**
   * Defines event listeners for touching the screen.
   *
   * This is 99% of the logic for this component. Lots of functions have to be nested in here so
   * that we don't end up in a state update loop.
   */
  useEffect(() => {
    /**
     * Gets the distance between user's fingers while pinching to zoom.
     *
     * Operates in CSS pixel space.
     *
     * @param touches TouchList containing locations of touches on screen.
     *
     * @returns Distance between touches.
     */
    const getPinchDistance = (touches: TouchList): number => {
      const dx = touches[0].clientX - touches[1].clientX;
      const dy = touches[0].clientY - touches[1].clientY;

      return Math.sqrt(dx * dx + dy * dy);
    };

    /**
     * Starts drawing, or starts zooming/panning.
     *
     * If using one finger, begins a stroke on the canvas at the current image point. If using two
     * fingers, records the current pinch distance and midpoint to compare to.
     *
     * @param e TouchEvent.
     */
    const doTouchStart = (e: TouchEvent): void => {
      if (e.touches.length === 1 && !disabled) {
        // @ts-ignore
        const { layerX, layerY } = e;

        const canvas = canvasRef.current;
        const ctx = contextRef.current;
        if (canvas === null || ctx === null) {
          return;
        }

        const imageX = cssToImagePoint(layerX, originRef.current.x);
        const imageY = cssToImagePoint(layerY, originRef.current.y);

        ctx.beginPath();
        // draw point at initial tap in case they are tapping and not circling
        ctx.ellipse(imageX, imageY, 0.5, 0.5, 0, 0, Math.PI * 2);
        ctx.stroke();

        ctx.moveTo(imageX, imageY);

        isDrawingRef.current = true;
        pathRef.current.push([imageX, imageY]);
      } else if (e.touches.length === 2) {
        // zooming/panning
        e.preventDefault();

        // record baseline pinch distance and midpoint to compare changes to
        lastPinchDistanceRef.current = getPinchDistance(e.touches);
        lastPinchMidpointRef.current = {
          // @ts-ignore
          x: e.layerX,
          // @ts-ignore
          y: e.layerY,
        };

        if (isDrawingRef.current) {
          isDrawingRef.current = false;
        }
      }
    };

    /**
     * Draws, or zoom/pans.
     *
     * If drawing, connects the last point in the current path to the current point.
     * If zooming/panning, calculates the change in pinch distance and midpoint from last step and
     * pans or zooms the image appropriately.
     *
     * @param e TouchEvent.
     */
    const doTouchMove = (e: TouchEvent): void => {
      // not strictly necessary, but might help prevent panning the viewport rather than the image
      e.preventDefault();

      if (e.touches.length === 1 && !disabled) {
        // drawing on image
        const canvas = canvasRef.current;
        const ctx = contextRef.current;

        if (!isDrawingRef.current || canvas === null || ctx === null) {
          return;
        }

        // @ts-ignore
        const { layerX, layerY } = e;

        // convert css (screen pixels) to image pixels, since canvas renders full resolution
        const imageX = cssToImagePoint(layerX, originRef.current.x);
        const imageY = cssToImagePoint(layerY, originRef.current.y);

        // draws from last point to this point
        ctx.lineTo(imageX, imageY);
        ctx.stroke();

        pathRef.current.push([imageX, imageY]);
      } else if (e.touches.length === 2) {
        // zooming/panning
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
      }
    };

    /**
     * Sends annotation to the API or redraws image/mask.
     *
     * If user just finished drawing, sends the drawing path to the API to create an annotation.
     * Otherwise, user just finished zooming or panning, so we redraw the image and mask-- this is
     * so that any accidental strokes are removed and the current path gets reset. If not, then
     * the next annotation path will be corrupted and contain points from the wrong location of the
     * image.
     *
     * @param e TouchEvent.
     */
    const doTouchEnd = (e: TouchEvent): void => {
      const canvas = canvasRef.current;
      const ctx = contextRef.current;
      if (canvas === null || ctx === null) {
        return;
      }

      if (
        isDrawingRef.current &&
        e.changedTouches.length === 1 &&
        e.touches.length === 0 &&
        !disabled
      ) {
        // we are currently drawing and the user just lifted their finger
        if (pathRef.current.length < 10) {
          // handles a couple cases:
          // 1. the path did not get properly cleared and now the user is tapping on a completely
          // different part of the image, and we don't want to segment the entire distance
          // between these points
          // 2. a small line was drawn mistakenly rather than tapping, and we can assume they
          // meant to just tap
          annotateImage([pathRef.current[pathRef.current.length - 1]]);
        } else {
          annotateImage([...pathRef.current]);
        }
      } else {
        // user just finished zooming/panning; redraw image and mask to remove any accidental
        // strokes
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(image, 0, 0);
        if (mask !== null && !hideMask) {
          ctx.globalAlpha = 0.5;
          ctx.drawImage(mask, 0, 0);
          ctx.globalAlpha = 1.0;
        }
      }

      pathRef.current = [];
    };

    /**
     * Redraws image and mask to remove accidental strokes.
     *
     * Not entirely sure how to reliably call this touch event, but useful to have as a failsafe.
     */
    const doTouchCancel = (): void => {
      const canvas = canvasRef.current;
      const ctx = contextRef.current;
      if (canvas === null || ctx === null) {
        return;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(image, 0, 0);
      if (mask !== null) {
        ctx.globalAlpha = 0.5;
        ctx.drawImage(mask, 0, 0);
        ctx.globalAlpha = 1.0;
      }
    };

    const canvas = canvasRef.current;
    if (canvas === null) {
      return;
    }

    // define listeners
    canvas.addEventListener("touchstart", doTouchStart, {
      passive: false,
    });
    canvas.addEventListener("touchmove", doTouchMove, {
      passive: false,
    });
    canvas.addEventListener("touchend", doTouchEnd);
    canvas.addEventListener("touchcancel", doTouchCancel);

    return () => {
      canvas.removeEventListener("touchstart", doTouchStart);
      canvas.removeEventListener("touchmove", doTouchMove);
      canvas.removeEventListener("touchend", doTouchEnd);
      canvas.removeEventListener("touchcancel", doTouchCancel);
    };
  }, [annotateImage, image, mask, hideMask, disabled]);

  return <canvas ref={canvasRef} style={{ transformOrigin: "0 0" }} />;
};

export default AnnotateCanvas;
