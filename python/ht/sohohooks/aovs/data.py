

VEXTYPE_MENU_ITEMS = (
    ("float", "Float Type", ":ht/rsc/icons/sohohooks/aovs/float.png"),
    ("vector", "Vector Type", ":ht/rsc/icons/sohohooks/aovs/vector.png"),
    ("vector4", "Vector4 Type", ":ht/rsc/icons/sohohooks/aovs/vector4.png"),
    ("unitvector", "Unit Vector Type", ":ht/rsc/icons/sohohooks/aovs/unitvector.png"),
)

QUANTIZE_MENU_ITEMS = (
    ("8", "8 bit integer"),
    ("16", "16 bit integer"),
    ("half", "16 bit float"),
    ("float", "32 bit float"),
)


SFILTER_MENU_ITEMS = (
    ("alpha", "Opacity Filtering"),
    ("fullopacity", "Full Opacity Filtering"),
    ("closest", "Closest Surface"),
)

PFILTER_MENU_ITEMS = (
    ("Inherit from main plane", ""),
    ("Unit Box Filter", "box -w 1"),
    ("Gaussian 2x2", "gaussian -w 2"),
    ("Gaussian 3x3 (softer)", "gaussian -w 3"),
    ("Gaussian 2x2 with noisy sample refiltering", "gaussian -w 2 -r 1"),
    ("Ray Histogram Fusion", "combine -t 20.0"),
    ("Bartlett (triangle)", "bartlett -w 2"),
    ("Catmull-Rom", "catrom -w 3"),
    ("Hanning", "hanning -w 2"),
    ("Blackman", "blackman -w 2"),
    ("Sinc (sharpening)", "sinc -w 3"),
    ("Edge Detection Filter", "edgedetect"),
    ("Closest Sample Filter", "minmax min"),
    ("Farthest Sample Filter", "minmax max"),
    ("Disable Edge Antialiasing", "minmax edge"),
    ("Object With Most Pixel Coverage", "minmax ocover"),
    ("Object With Most Pixel Coverage (no filtering)", "minmax idcover"),
)

LIGHTEXPORT_MENU_ITEMS = (
    ("", "No light exports"),
    ("per-category", "Export variable for each category"),
    ("per-light", "Export variable for each light"),
    ("single", "Merge all lights into single channel"),
)

