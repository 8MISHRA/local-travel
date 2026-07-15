"""Property test configuration with Hypothesis settings."""

import os

from hypothesis import settings

os.environ["FLASK_ENV"] = "testing"

# Register a Hypothesis profile with minimum 100 examples
settings.register_profile("ci", max_examples=100)
settings.register_profile("default", max_examples=100)
settings.load_profile("default")
