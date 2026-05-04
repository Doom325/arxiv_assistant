"""scheduler.start_scheduler() must be a no-op when MIGRATING=1.

The deploy script sets MIGRATING=1 on the backend container during the
DDL window so APScheduler doesn't fire ingestion / batch / rescore jobs
that would re-introduce lock contention on ALTER TABLE.

NOTE: ``conftest.py`` replaces ``sys.modules["scheduler"]`` with a MagicMock
to keep APScheduler from starting during tests. We bypass that here by
loading the real module from disk via importlib.
"""

import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def real_scheduler_module(monkeypatch):
    """Load the real scheduler module bypassing conftest's MagicMock."""
    monkeypatch.delitem(sys.modules, "scheduler", raising=False)
    path = Path(__file__).resolve().parent.parent / "scheduler.py"
    spec = importlib.util.spec_from_file_location("scheduler_real", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module


def test_start_scheduler_skips_when_migrating(monkeypatch, real_scheduler_module):
    monkeypatch.setenv("MIGRATING", "1")
    with patch.object(real_scheduler_module.scheduler, "start") as mock_start:
        real_scheduler_module.start_scheduler()
        mock_start.assert_not_called()


def test_start_scheduler_runs_when_not_migrating(monkeypatch, real_scheduler_module):
    monkeypatch.delenv("MIGRATING", raising=False)
    with patch.object(real_scheduler_module.scheduler, "start") as mock_start:
        real_scheduler_module.start_scheduler()
        mock_start.assert_called_once()


def test_start_scheduler_runs_when_migrating_zero(monkeypatch, real_scheduler_module):
    """MIGRATING=0 is the off-state set after the migration window."""
    monkeypatch.setenv("MIGRATING", "0")
    with patch.object(real_scheduler_module.scheduler, "start") as mock_start:
        real_scheduler_module.start_scheduler()
        mock_start.assert_called_once()
