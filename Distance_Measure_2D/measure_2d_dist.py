import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

# ─────────────────────────────────────────────────────────────────────────────
#  Global State
# ─────────────────────────────────────────────────────────────────────────────
state  = "SET_SCALE_X"   # flow: SET_SCALE_X → SET_SCALE_Y → READY
mode   = "measure"       # measure | circle  (only used in READY)

scale_x = None           # pixels per real unit (horizontal axis)
scale_y = None           # pixels per real unit (vertical axis)

points       = []        # temporary click buffer
measurements = []        # finalised drawings  → list of (type, [pts])
calib_lines  = []        # calibration segments to draw persistently

img   = None             # displayed frame (redrawn each loop)
clone = None             # pristine copy of the loaded image
root  = None             # tkinter root kept alive for dialogs


# ─────────────────────────────────────────────────────────────────────────────
#  Colors  (BGR)
# ─────────────────────────────────────────────────────────────────────────────
C_POINT     = (0, 255,   0)    # green        – click dots
C_LINE      = (0,  80, 255)    # red-orange   – measurement lines
C_PROJ      = (130, 130, 130)  # grey         – projection helpers
C_CALIB     = (255, 220,   0)  # cyan-yellow  – calibration segments
C_CIRCLE    = (255,   0, 200)  # magenta      – fitted circle / ellipse
C_CENTER    = (0,  255, 255)   # yellow       – circle centre dot
C_TEXT      = (255, 255, 255)  # white
C_DIM       = (0,  220, 255)   # gold         – dimension labels

# Banner backgrounds
BG_DARK     = ( 25,  25,  25)
C_BAN_X     = (  0, 210, 255)  # amber  – STEP 1
C_BAN_Y     = (  0, 140, 255)  # orange – STEP 2
C_BAN_OK    = (  0, 200,  80)  # green  – READY


# ─────────────────────────────────────────────────────────────────────────────
#  Utility
# ─────────────────────────────────────────────────────────────────────────────
def put(im, text, pos, color=C_TEXT, fs=0.44, th=1):
    cv2.putText(im, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                fs, color, th, cv2.LINE_AA)


def ask_float(prompt):
    """Show a tkinter dialog and return a positive float, or None."""
    root.update()
    val = simpledialog.askfloat("Scale Calibration", prompt, minvalue=1e-6)
    return val


def warn(msg):
    root.update()
    messagebox.showwarning("Calibration Warning", msg)


# ─────────────────────────────────────────────────────────────────────────────
#  Banner  (top-of-frame status bar)
# ─────────────────────────────────────────────────────────────────────────────
def draw_banner(im):
    w = im.shape[1]
    cv2.rectangle(im, (0, 0), (w, 58), BG_DARK, -1)

    if state == "SET_SCALE_X":
        heading = "STEP 1 / 2  —  Horizontal Scale Calibration"
        sub     = "Click 2 points on a known HORIZONTAL reference line, then enter its real length."
        hcol    = C_BAN_X

    elif state == "SET_SCALE_Y":
        heading = "STEP 2 / 2  —  Vertical Scale Calibration"
        sub     = "Click 2 points on a known VERTICAL reference line, then enter its real length."
        hcol    = C_BAN_Y

    else:  # READY
        sx  = f"{scale_x:.4f}" if scale_x else "?"
        sy  = f"{scale_y:.4f}" if scale_y else "?"
        heading = f"READY   |   scale_x = {sx} px/unit     scale_y = {sy} px/unit"
        sub     = (f"Mode: [{mode.upper()}]   |   "
                   "m = measure    o = circle    c = clear drawings    r = recalibrate    q = quit")
        hcol    = C_BAN_OK

    put(im, heading, (12, 22), hcol,  fs=0.50, th=1)
    put(im, sub,     (12, 44), C_TEXT, fs=0.38, th=1)

    # Pending-point counter hint
    if state in ("SET_SCALE_X", "SET_SCALE_Y") and len(points) == 1:
        put(im, f"  Point 1 set — click Point 2", (w - 310, 22), C_BAN_X, fs=0.42)


# ─────────────────────────────────────────────────────────────────────────────
#  Calibration line renderer
# ─────────────────────────────────────────────────────────────────────────────
def draw_calib_lines(im):
    for seg in calib_lines:
        p1, p2 = seg[0], seg[1]
        cv2.line(im, p1, p2, C_CALIB, 2, cv2.LINE_AA)
        cv2.circle(im, p1, 5, C_CALIB, -1)
        cv2.circle(im, p2, 5, C_CALIB, -1)


# ─────────────────────────────────────────────────────────────────────────────
#  Pending click-point dots
# ─────────────────────────────────────────────────────────────────────────────
def draw_pending(im):
    for p in points:
        cv2.circle(im, p, 5, C_POINT, -1)
        cv2.circle(im, p, 8, C_POINT, 1)


# ─────────────────────────────────────────────────────────────────────────────
#  Measurement renderers
# ─────────────────────────────────────────────────────────────────────────────
def render_measure(im, p1, p2):
    """Draw annotated measurement line with real-world dx, dy, distance, angle."""
    pdx = abs(p2[0] - p1[0])
    pdy = abs(p2[1] - p1[1])

    rdx   = pdx / scale_x
    rdy   = pdy / scale_y
    rdist = np.sqrt(rdx**2 + rdy**2)
    angle = np.degrees(np.arctan2(rdy, rdx))

    # Main line
    cv2.line(im, p1, p2, C_LINE, 2, cv2.LINE_AA)

    # Projection helpers (dotted look via dashes)
    corner = (p2[0], p1[1])
    cv2.line(im, p1,     corner, C_PROJ, 1, cv2.LINE_AA)
    cv2.line(im, corner, p2,     C_PROJ, 1, cv2.LINE_AA)

    # End-point dots
    cv2.circle(im, p1, 5, C_POINT, -1)
    cv2.circle(im, p2, 5, C_POINT, -1)

    # Labels
    mx = (p1[0] + p2[0]) // 2
    my = (p1[1] + p2[1]) // 2

    put(im, f"dx = {rdx:.2f}",    (min(p1[0], p2[0]), p1[1] - 10), C_TEXT)
    put(im, f"dy = {rdy:.2f}",    (p2[0] + 8, (p1[1] + p2[1]) // 2), C_TEXT)
    put(im, f"d  = {rdist:.2f}",  (mx - 30, my - 12), C_DIM, fs=0.50, th=1)
    put(im, f"{angle:.1f}"+" °",   (p2[0] + 4, p2[1] + 18), C_TEXT)


def render_circle(im, p1, p2, p3):
    """
    Fit a circle to three pixel-clicked points in REAL-WORLD space,
    then draw it back as an ellipse in pixel space (correct when scale_x != scale_y).
    """
    def to_real(p):
        return np.array([p[0] / scale_x, p[1] / scale_y], dtype=float)

    A, B, C = to_real(p1), to_real(p2), to_real(p3)

    mid_ab, mid_bc = (A + B) / 2, (B + C) / 2
    d_ab,   d_bc   = B - A, C - B

    def perp(v):
        return np.array([-v[1], v[0]])

    bis_ab, bis_bc = perp(d_ab), perp(d_bc)

    M = np.vstack([bis_ab, -bis_bc]).T
    try:
        t, _, rank, _ = np.linalg.lstsq(M, mid_bc - mid_ab, rcond=None)
        if rank < 2:
            warn("The three points are collinear — cannot fit a circle.")
            return
    except np.linalg.LinAlgError:
        warn("Circle fit failed — try different points.")
        return

    center_real  = mid_ab + t[0] * bis_ab
    radius_real  = float(np.linalg.norm(center_real - A))

    # Back to pixel space
    cx_px = int(center_real[0] * scale_x)
    cy_px = int(center_real[1] * scale_y)

    # Because scale_x ≠ scale_y the circle appears as an ellipse on screen
    rx_px = int(radius_real * scale_x)
    ry_px = int(radius_real * scale_y)

    cv2.ellipse(im, (cx_px, cy_px), (rx_px, ry_px), 0, 0, 360, C_CIRCLE, 2, cv2.LINE_AA)
    cv2.circle(im,  (cx_px, cy_px), 5, C_CENTER, -1)

    # Draw the three anchor points
    for p in [p1, p2, p3]:
        cv2.circle(im, p, 5, C_POINT, -1)

    put(im, f"r = {radius_real:.2f}", (cx_px + 10, cy_px), C_CIRCLE, fs=0.50)


# ─────────────────────────────────────────────────────────────────────────────
#  Master redraw  (called every loop tick)
# ─────────────────────────────────────────────────────────────────────────────
def redraw():
    global img
    img = clone.copy()

    draw_banner(img)
    draw_calib_lines(img)
    draw_pending(img)

    if state == "READY":
        for mtype, pts in measurements:
            if mtype == "measure":
                render_measure(img, pts[0], pts[1])
            elif mtype == "circle":
                render_circle(img, pts[0], pts[1], pts[2])


# ─────────────────────────────────────────────────────────────────────────────
#  Mouse callback
# ─────────────────────────────────────────────────────────────────────────────
def mouse_callback(event, x, y, flags, param):
    global points, state, scale_x, scale_y, mode

    if event != cv2.EVENT_LBUTTONDOWN:
        return

    points.append((x, y))

    # ── STEP 1 : Horizontal scale ────────────────────────────────────────────
    if state == "SET_SCALE_X" and len(points) == 2:
        pdx = abs(points[1][0] - points[0][0])
        if pdx < 3:
            warn("The two points are too close horizontally.\n"
                 "Please pick points further apart on a horizontal line.")
            points.clear()
            return
        val = ask_float(
            f"Pixel horizontal span = {pdx} px\n\n"
            "Enter the REAL horizontal distance (in your units, e.g. mm, cm, inches):"
        )
        if val and val > 0:
            scale_x = pdx / val
            calib_lines.append(points.copy())
            print(f"[✓] Horizontal scale set: {scale_x:.4f} px / unit")
            points.clear()
            state = "SET_SCALE_Y"
        else:
            points.clear()   # cancelled → retry

    # ── STEP 2 : Vertical scale ──────────────────────────────────────────────
    elif state == "SET_SCALE_Y" and len(points) == 2:
        pdy = abs(points[1][1] - points[0][1])
        if pdy < 3:
            warn("The two points are too close vertically.\n"
                 "Please pick points further apart on a vertical line.")
            points.clear()
            return
        val = ask_float(
            f"Pixel vertical span = {pdy} px\n\n"
            "Enter the REAL vertical distance (same units as before):"
        )
        if val and val > 0:
            scale_y = pdy / val
            calib_lines.append(points.copy())
            print(f"[✓] Vertical scale set:   {scale_y:.4f} px / unit")
            points.clear()
            state = "READY"
            mode  = "measure"
            print("[✓] Calibration complete — measure and circle modes unlocked.")
        else:
            points.clear()   # cancelled → retry

    # ── READY : Measure mode ─────────────────────────────────────────────────
    elif state == "READY" and mode == "measure" and len(points) == 2:
        measurements.append(("measure", points.copy()))
        points.clear()

    # ── READY : Circle mode ──────────────────────────────────────────────────
    elif state == "READY" and mode == "circle" and len(points) == 3:
        measurements.append(("circle", points.copy()))
        points.clear()


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    global img, clone, root
    global state, scale_x, scale_y, mode
    global measurements, points, calib_lines

    # ── Launch file picker ───────────────────────────────────────────────────
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select an image to measure",
        filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif")]
    )
    if not file_path:
        print("No file selected — exiting.")
        return

    img   = cv2.imread(file_path)
    if img is None:
        print(f"Could not read image: {file_path}")
        return
    clone = img.copy()

    cv2.namedWindow("Measurement Tool", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Measurement Tool", mouse_callback)

    print("\n=== Image Measurement Tool ===")
    print("STEP 1: Click 2 points on a known HORIZONTAL reference line.")
    print("STEP 2: Click 2 points on a known VERTICAL  reference line.")
    print("Then measure freely.  Keys: m=measure  o=circle  c=clear  r=recalibrate  q=quit\n")

    # ── Main loop ────────────────────────────────────────────────────────────
    while True:
        redraw()
        cv2.imshow("Measurement Tool", img)
        key = cv2.waitKey(20) & 0xFF

        if key in [27, ord("q")]:       # quit
            break

        if state == "READY":
            if   key == ord("m"):        # switch to measure mode
                mode = "measure"
                points.clear()
            elif key == ord("o"):        # switch to circle mode
                mode = "circle"
                points.clear()
            elif key == ord("c"):        # clear drawings, keep scale
                measurements.clear()
                points.clear()
            elif key == ord("r"):        # full reset → back to calibration
                measurements.clear()
                calib_lines.clear()
                points.clear()
                scale_x = scale_y = None
                state = "SET_SCALE_X"
                mode  = "measure"
                print("\n[↺] Reset — please recalibrate.")

    cv2.destroyAllWindows()
    root.destroy()


if __name__ == "__main__":
    main()