"""An invalid legacy seal flag must fail before any source-byte read."""
from pathlib import Path

import pytest

from quanta_agents.meta.ashare_case import AShareCase


@pytest.mark.parametrize('value', ['false', 'true', '0', '1', 0, 1, None, [], {}])
def test_nonboolean_allow_final_rejected_before_source_access(monkeypatch, value):
    monkeypatch.setattr(Path, 'read_bytes', lambda *a, **k: pytest.fail('source read before flag validation'))
    with pytest.raises(ValueError, match='explicit boolean'):
        AShareCase({'allow_final': value})
