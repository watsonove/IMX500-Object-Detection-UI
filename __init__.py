cat > __init__.py << EOF
# IMX500 GUI - Hauptpackage

# Wird von app.py verwendet
from .detector import IMX500Detector, FrameSnapshot, Det
from .steps import StepTransformer, STEP
