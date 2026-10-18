"""Select a dated output revision without overwriting the original release."""
import os
import re

DEFAULT_PREFIX = "20261018_v3_"


def output_prefix():
    prefix = os.environ.get("TFK_OUTPUT_PREFIX", DEFAULT_PREFIX)
    if not re.fullmatch(r"[0-9]{8}_v[1-9][0-9]*_", prefix):
        raise ValueError("TFK_OUTPUT_PREFIX must look like YYYYMMDD_v2_")
    return prefix


PREFIX = output_prefix()
