# Image Measurement Tool

A Python-based interactive image measurement and circle-fitting utility built with **OpenCV** and **Tkinter**.

This tool allows you to:

* Calibrate separate **horizontal** and **vertical** scales
* Measure real-world distances directly from an image
* Compute:

  * Horizontal distance (`dx`)
  * Vertical distance (`dy`)
  * True distance (`d`)
  * Angle between points
* Fit a real-world circle using **3 clicked points**
* Handle **non-uniform image scaling** (`scale_x ≠ scale_y`)
* Visually annotate measurements on-screen

---

# Features

## Dual-Axis Calibration

Unlike simple pixel scaling tools, this application supports:

* Independent X-axis calibration
* Independent Y-axis calibration

This is useful when:

* Images are stretched
* Aspect ratio is distorted
* Different scaling exists in horizontal and vertical directions

---

## Measurement Mode

Measure between any two clicked points:

* Horizontal distance
* Vertical distance
* Euclidean distance
* Angle

Displayed directly on the image.

---

## Circle Fitting Mode

Select 3 points on a circular object.

The tool:

1. Converts clicked points into real-world coordinates
2. Fits a geometric circle
3. Converts it back into image space
4. Draws the corrected ellipse representation

Useful for:

* Lens measurement
* Pipe inspection
* Mechanical part analysis
* CAD reference extraction

---

# Requirements

Install dependencies:

```bash
pip install opencv-python numpy
```

Tkinter usually comes preinstalled with Python.

If not:

### Ubuntu/Debian

```bash
sudo apt install python3-tk
```

### Windows

Tkinter is included with standard Python installation.

---

# How to Run

```bash
python measurement_tool.py
```

After launch:

1. Select an image file
2. Perform calibration
3. Start measuring

---

# Calibration Workflow

## Step 1 — Horizontal Calibration

Click two points on a known horizontal reference.

Example:

* Known width = 100 mm
* Pixel span = 500 px

The tool computes:

```text
scale_x = 500 / 100 = 5 px/mm
```

---

## Step 2 — Vertical Calibration

Click two points on a known vertical reference.

Example:

* Known height = 50 mm
* Pixel span = 250 px

The tool computes:

```text
scale_y = 250 / 50 = 5 px/mm
```

---

# Controls

| Key   | Action                     |
| ----- | -------------------------- |
| `m`   | Switch to measurement mode |
| `o`   | Switch to circle mode      |
| `c`   | Clear drawings             |
| `r`   | Reset calibration          |
| `q`   | Quit application           |
| `ESC` | Quit application           |

---

# Measurement Output

For each measurement:

* `dx` → horizontal real-world distance
* `dy` → vertical real-world distance
* `d` → true Euclidean distance
* `θ` → angle

---

# Circle Fitting Mathematics

The circle fitting process works in **real-world coordinate space**.

The tool:

1. Converts pixel coordinates:

```text
x_real = x_pixel / scale_x
y_real = y_pixel / scale_y
```

2. Computes perpendicular bisectors
3. Solves for circle center
4. Computes radius
5. Projects result back to pixel space

If:

```text
scale_x != scale_y
```

a real-world circle appears as an ellipse on screen.

This behavior is handled automatically.

---

# Visual Indicators

| Color       | Meaning            |
| ----------- | ------------------ |
| Green       | Selected points    |
| Red-Orange  | Measurement lines  |
| Grey        | Projection helpers |
| Cyan-Yellow | Calibration lines  |
| Magenta     | Circle / ellipse   |
| Yellow      | Circle center      |
| White       | General text       |
| Gold        | Distance labels    |

---

# Project Structure

```text
measurement_tool.py
README.md
```

---

# Main Components

## Core Functions

### `draw_banner()`

Displays status and instructions.

---

### `render_measure()`

Draws:

* Distance line
* Projection lines
* Labels
* Angle

---

### `render_circle()`

Fits and renders a corrected circle/ellipse.

---

### `mouse_callback()`

Handles:

* Calibration clicks
* Measurement clicks
* Circle fitting clicks

---

### `redraw()`

Refreshes the entire frame each loop iteration.

---

# Supported Image Formats

* PNG
* JPG
* JPEG
* BMP
* TIFF
* TIF

---

# Example Use Cases

* Engineering measurement
* Mechanical inspection
* CAD scaling
* Research image analysis
* Scientific imaging
* Microscopy
* Manufacturing QA
* Dimensional analysis

---

# Error Handling

The tool prevents:

* Zero-length calibration
* Invalid scale input
* Collinear circle points
* Numerical fitting failures

Warnings are shown using Tkinter dialogs.

---

# Future Improvements

Possible extensions:

* Export measurements to CSV
* Zoom and pan
* Undo functionality
* Angle-only mode
* Polygon area measurement
* Automatic edge snapping
* Subpixel precision
* Unit selection UI
* Saving annotated images

---

# Author Notes

This tool is designed for practical engineering and scientific workflows where image scaling may not be uniform across axes.

The separate X/Y calibration approach makes it significantly more accurate than traditional single-scale image measurement tools.

Feel free to modify and extend the project.
