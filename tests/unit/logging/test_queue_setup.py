from __future__ import annotations

import logging

import pytest

from core.logging.queue_setup import attach_queue_to_root, effective_handlers, stop_queue


@pytest.mark.unit
def test_queue_setup_and_effective_handlers() -> None:
    root = logging.getLogger()
    # Ensure at least one handler exists
    if not root.handlers:
        h = logging.StreamHandler()
        root.addHandler(h)
    orig = list(root.handlers)

    attach_queue_to_root()
    # After attaching, root handlers should be a single QueueHandler
    assert len(root.handlers) == 1
    # effective handlers should report original handlers wired behind listener
    eff = effective_handlers()
    assert all(isinstance(h, logging.Handler) for h in eff)
    # Should include a handler of the same type as original
    assert any(type(h) is type(orig[0]) for h in eff)

    stop_queue()
    # After stopping, fall back to current root handlers (QueueHandler remains until reconfigured)
    _ = effective_handlers()  # should not raise

