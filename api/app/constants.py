import enum

class OxygenatorType(str, enum.Enum):
    HLS = "hls"
    NAUTILUS = "nautilus"


class AnnotationType(str, enum.Enum):
    CLOT = "clot"
    FIBRIN = "fibrin"
    ERASE = "erase"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "heic"}
HLS_SIDE_LENGTH_MM = 88
