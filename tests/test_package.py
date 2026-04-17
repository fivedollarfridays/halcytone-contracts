import re

import halcytone_contracts


def test_version_string_present_and_semver_shaped():
    version = halcytone_contracts.__version__
    assert isinstance(version, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:[-+].+)?", version), version
