"""Array backend selection.

The project is written against a small NumPy-compatible surface. Installing the
`jax` extra enables JAX arrays; the NumPy fallback keeps the CLI and tests usable
on machines where JAX wheels are unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:  # pragma: no cover - exercised only in JAX-enabled environments
    import jax
    import jax.numpy as jnp

    HAS_JAX = True
except Exception:  # pragma: no cover - the default in this execution environment
    jax = None
    jnp = np
    HAS_JAX = False


@dataclass(frozen=True)
class BackendInfo:
    name: str
    differentiable: bool


def xp(prefer_jax: bool = True):
    """Return the array module for numerical kernels."""

    return jnp if prefer_jax and HAS_JAX else np


def backend_info(prefer_jax: bool = True) -> BackendInfo:
    if prefer_jax and HAS_JAX:
        return BackendInfo(name="jax", differentiable=True)
    return BackendInfo(name="numpy", differentiable=False)


def to_numpy(array):
    """Convert a NumPy/JAX array-like object into a host NumPy array."""

    return np.asarray(array)
