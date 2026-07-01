# Auto-cropping and perspective correction

To enable auto-cropping, set ENABLE_CROPPING to true in `constants.py` (top-level file). There is a separate algorithm for HLS oxygenators (no longer in use) and Nautilus oxygenators. The HLS algorithm is contained within `oxygenator_detector.py` and the Nautilus one uses components from `linear_equation.py` and `RANSAC.py`.

## Troubleshooting

### HLS oxygenator not found

Most likely the oxygenator is not found because there are not four candidate corner points. Candidates are found by the intersection of lines found by the probabilistic Hough transform. The Hough lines are found within the output of Canny edge detection. So, the issue lies in either the Hough detection or the Canny detection.

#### Troubleshooting Canny edge detection

After the Canny edge detection is run, you can see the Canny output with `Image.fromarray(edges).save("edges.png")`. If the inner edges of the oxygenator are not showing up in the Canny output, then the upper and lower threshold need to be adjusted on this line: `edges = cv2.Canny(self.img, ret / 3 * 2, ret * 2)`.

#### Troubleshooting Hough transform

If the edges are present but lines are not being detected, the Hough parameters need to be adjusted. Lowering `HOUGH_THRESHOLD` in `constants.py` will accept more potential line candidates and lowering `HOUGH_MIN_LINE_LENGTH` will accept shorter line candidates if the edges are small.