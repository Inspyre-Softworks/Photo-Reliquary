"""Plugin registry and built-in example plugins.

Taylor B. | Inspyre-Softworks
"""

from __future__ import annotations

from photo_reliquary.analysis.models import AnalysisResult, Annotation, AnnotationRegion
from photo_reliquary.exceptions import PluginError
from photo_reliquary.logging_utils import ReliquaryLoggable
from photo_reliquary.models import PhotoRecord
from photo_reliquary.plugins.base import PhotoAnalyzerPlugin


class ExampleNudeNetPlugin(PhotoAnalyzerPlugin):
    """A NudeNet-style stub plugin that demonstrates the analysis API."""

    name = 'nudenet-example'
    version = '0.1.0'
    supported_file_types = ('.jpg', '.jpeg', '.png', '.webp')

    def analyze(self, photo_record: PhotoRecord) -> AnalysisResult:
        """Return example confidence-scored annotations for a photo."""

        self.log_device.info(f'Running example analyzer {self.name} for {photo_record.current_path}.')
        annotations = [
            Annotation(
                namespace='nudenet',
                label='example_detection',
                confidence=0.42,
                value='stubbed',
                plugin_name=self.name,
                plugin_version=self.version,
                model_name='example-nudenet-model',
                model_version='0.1',
            )
        ]
        if photo_record.current_path.suffix.lower() == '.jpg':
            annotations.append(
                Annotation(
                    namespace='nudenet',
                    label='example_region',
                    confidence=0.17,
                    region=AnnotationRegion(x=0.1, y=0.2, width=0.3, height=0.4),
                    plugin_name=self.name,
                    plugin_version=self.version,
                    model_name='example-nudenet-model',
                    model_version='0.1',
                )
            )
        return AnalysisResult(
            photo_id=photo_record.photo_id,
            plugin_name=self.name,
            plugin_version=self.version,
            annotations=annotations,
            model_name='example-nudenet-model',
            model_version='0.1',
        )


class PluginRegistry(ReliquaryLoggable):
    """Registry for built-in and future external analyzer plugins."""

    def __init__(self) -> None:
        super().__init__()
        self._plugins: dict[str, PhotoAnalyzerPlugin] = {}
        self.load_builtin_plugins()

    def load_builtin_plugins(self) -> None:
        """Register built-in example plugins."""

        self.register(ExampleNudeNetPlugin())
        self.log_device.debug('Loaded built-in analyzer plugins.')

    def register(self, plugin: PhotoAnalyzerPlugin) -> None:
        """Register a plugin instance."""

        self._plugins[plugin.name] = plugin
        self.log_device.debug(f'Registered plugin {plugin.name} {plugin.version}.')

    def get(self, name: str) -> PhotoAnalyzerPlugin:
        """Return a plugin by name."""

        try:
            return self._plugins[name]
        except KeyError as error:
            raise PluginError(f'Unknown analyzer plugin: {name}') from error

    def list_plugins(self) -> list[PhotoAnalyzerPlugin]:
        """Return registered plugins in sorted order."""

        return [self._plugins[name] for name in sorted(self._plugins)]
