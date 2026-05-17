"""Plugin interfaces and registry.

Taylor B. | Inspyre-Softworks
"""

from photo_reliquary.plugins.base import PhotoAnalyzerPlugin
from photo_reliquary.plugins.registry import ExampleNudeNetPlugin, PluginRegistry

__all__ = ['ExampleNudeNetPlugin', 'PhotoAnalyzerPlugin', 'PluginRegistry']
