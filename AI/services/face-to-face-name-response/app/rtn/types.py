import numpy as np
import numpy.typing as npt

FrameBGR = npt.NDArray[np.uint8]
MaskU8 = npt.NDArray[np.uint8]

BBox = tuple[float, float, float, float]  # (x1, y1, x2, y2)

Landmark3D = tuple[float, float, float]  # (x, y, z)
Landmarks = list[Landmark3D]

Track = tuple[float, float, float, float, int]  # (x1, y1, x2, y2, track_id)
