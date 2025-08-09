"""
SIGMA FILEBOSS Tabs Package
Modular tab components for the unified interface
"""

from .casebuilder_tab import CaseBuilderTab
from .document_generator_tab import DocumentGeneratorTab
from .whisperx_tab import WhisperXTab
from .file_organizer_tab import FileOrganizerTab
from .photoprism_tab import PhotoPrismTab
from .legal_brain_tab import LegalBrainTab
from .ai_analysis_tab import AIAnalysisTab
from .system_monitor_tab import SystemMonitorTab

__all__ = [
    'CaseBuilderTab',
    'DocumentGeneratorTab',
    'WhisperXTab',
    'FileOrganizerTab',
    'PhotoPrismTab',
    'LegalBrainTab',
    'AIAnalysisTab',
    'SystemMonitorTab'
]
