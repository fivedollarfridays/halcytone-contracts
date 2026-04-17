"""Session-bundle contracts: filesystem handoff artifacts.

`SessionManifest` is the cross-language boundary between halcytone-publish
(producer, Python) and AgentGrounds (consumer, TypeScript). The JSON Schema
mirror ships alongside the model in this subpackage and is regenerated via
``scripts/regen_manifest_schema.py``.
"""

from halcytone_contracts.bundles.manifest import SessionManifest

__all__ = ["SessionManifest"]
