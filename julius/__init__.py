# Package julius

import warnings
import logging

# Suppress deprecation and user warnings from third-party libraries (e.g., torch, opentelemetry)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Suppress noisy logger warnings from mem0
logging.getLogger("mem0").setLevel(logging.ERROR)
