"""phototrips — turn a geotagged photo library into a travel timeline."""

from .config import Config
from .pipeline import PipelineResult, run_pipeline

__version__ = "0.1.0"
__all__ = ["Config", "PipelineResult", "run_pipeline"]
