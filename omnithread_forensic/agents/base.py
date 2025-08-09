"""
Base classes and interfaces for forensic analysis agents.
Defines the common interface that all analysis agents must implement.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from core.models import (
    Artifact, ArtifactType, ArtifactSource, ArtifactRelationship,
    RelationshipType, EvidenceStatus, ArtifactProcessingLog
)
from config.settings import settings

# Type variables
T = TypeVar('T', bound='AgentConfig')
ArtifactT = TypeVar('ArtifactT', bound=Artifact)

class AgentCapability(str, Enum):
    """Capabilities that agents can declare."""
    # Data source capabilities
    READ_FILES = "read_files"
    WRITE_FILES = "write_files"
    NETWORK_ACCESS = "network_access"
    
    # Processing capabilities
    OCR = "ocr"
    AUDIO_PROCESSING = "audio_processing"
    VIDEO_PROCESSING = "video_processing"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    
    # Analysis capabilities
    TIMELINE_ANALYSIS = "timeline_analysis"
    CONTRADICTION_DETECTION = "contradiction_detection"
    PATTERN_RECOGNITION = "pattern_recognition"
    ENTITY_EXTRACTION = "entity_extraction"
    
    # Specialized capabilities
    LEGAL_ANALYSIS = "legal_analysis"
    FORENSIC_ANALYSIS = "forensic_analysis"
    MALWARE_ANALYSIS = "malware_analysis"

class AgentStatus(str, Enum):
    """Status of an agent instance."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

class AgentConfig(BaseModel):
    """Base configuration for agents."""
    agent_id: str = Field(default_factory=lambda: f"agent_{uuid4().hex[:8]}")
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    enabled: bool = True
    
    # Agent capabilities
    capabilities: Set[AgentCapability] = Field(default_factory=set)
    
    # Resource limits
    max_memory_mb: int = 1024  # Max memory in MB
    max_runtime_seconds: int = 300  # Max runtime in seconds
    
    # Processing settings
    batch_size: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    
    # Logging and monitoring
    log_level: str = "INFO"
    enable_metrics: bool = True
    
    class Config:
        json_encoders = {
            set: list,  # Convert sets to lists for JSON serialization
        }
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Agent name cannot be empty")
        return v.strip()
    
    @validator('log_level')
    def validate_log_level(cls, v):
        v = v.upper()
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log level")
        return v

class AgentContext(BaseModel):
    """Context shared between agents during processing."""
    correlation_id: str = Field(default_factory=lambda: f"ctx_{uuid4().hex[:8]}")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Artifacts being processed
    artifacts: Dict[UUID, Artifact] = Field(default_factory=dict)
    
    # Relationships between artifacts
    relationships: List[ArtifactRelationship] = Field(default_factory=list)
    
    # Shared state between agents
    state: Dict[str, Any] = Field(default_factory=dict)
    
    # Processing metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def update(self):
        """Update the last modified timestamp."""
        self.updated_at = datetime.utcnow()
    
    def add_artifact(self, artifact: Artifact) -> None:
        """Add an artifact to the context."""
        self.artifacts[artifact.id] = artifact
        self.update()
    
    def get_artifact(self, artifact_id: UUID) -> Optional[Artifact]:
        """Get an artifact by ID."""
        return self.artifacts.get(artifact_id)
    
    def add_relationship(self, relationship: ArtifactRelationship) -> None:
        """Add a relationship between artifacts."""
        self.relationships.append(relationship)
        self.update()
    
    def get_related_artifacts(
        self, 
        artifact_id: UUID, 
        relationship_type: Optional[RelationshipType] = None
    ) -> List[Artifact]:
        """Get artifacts related to the specified artifact."""
        related = []
        for rel in self.relationships:
            if rel.source_id == artifact_id and (
                relationship_type is None or rel.relationship_type == relationship_type
            ):
                artifact = self.get_artifact(rel.target_id)
                if artifact:
                    related.append(artifact)
        return related

class AgentStats(BaseModel):
    """Statistics for agent execution."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Counters
    artifacts_processed: int = 0
    artifacts_skipped: int = 0
    artifacts_failed: int = 0
    relationships_created: int = 0
    
    # Timing
    total_processing_time: float = 0.0  # seconds
    
    # Errors
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    @property
    def is_running(self) -> bool:
        """Check if the agent is currently running."""
        return self.start_time is not None and self.end_time is None
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get the duration of the agent's execution in seconds."""
        if self.start_time is None:
            return None
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()
    
    @property
    def artifacts_per_second(self) -> float:
        """Get the processing rate in artifacts per second."""
        duration = self.duration_seconds
        if not duration or duration == 0:
            return 0.0
        return self.artifacts_processed / duration
    
    def start(self) -> None:
        """Mark the start of processing."""
        self.start_time = datetime.utcnow()
        self.end_time = None
    
    def stop(self) -> None:
        """Mark the end of processing."""
        if self.start_time is not None and self.end_time is None:
            self.end_time = datetime.utcnow()
    
    def add_error(self, error: Exception, artifact_id: Optional[UUID] = None) -> None:
        """Record an error that occurred during processing."""
        self.errors.append({
            "timestamp": datetime.utcnow(),
            "artifact_id": str(artifact_id) if artifact_id else None,
            "error_type": error.__class__.__name__,
            "message": str(error),
            "traceback": None,  # Could add traceback if needed
        })
        self.artifacts_failed += 1

class BaseAgent(ABC):
    """
    Abstract base class for all forensic analysis agents.
    
    Agents are responsible for processing artifacts and extracting information,
    detecting patterns, and creating relationships between artifacts.
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with configuration."""
        self.config = config
        self.status = AgentStatus.STOPPED
        self.stats = AgentStats()
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{config.agent_id}]")
        
        # Set up logging level
        logging.basicConfig(level=getattr(logging, config.log_level))
    
    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> Type[AgentConfig]:
        """Return the configuration model for this agent type."""
        raise NotImplementedError
    
    @classmethod
    def create(cls, config: Dict) -> 'BaseAgent':
        """Create a new agent instance from a configuration dictionary."""
        config_model = cls.get_config_schema()
        config_obj = config_model(**config)
        return cls(config_obj)
    
    async def start(self) -> None:
        """Start the agent."""
        if self.status != AgentStatus.STOPPED:
            raise RuntimeError(f"Cannot start agent in state: {self.status}")
        
        self.status = AgentStatus.STARTING
        self.logger.info(f"Starting {self.config.name} agent")
        
        try:
            await self._start()
            self.status = AgentStatus.RUNNING
            self.stats.start()
            self.logger.info(f"{self.config.name} agent started successfully")
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Failed to start agent: {str(e)}", exc_info=True)
            raise
    
    async def stop(self) -> None:
        """Stop the agent."""
        if self.status == AgentStatus.STOPPED:
            return
            
        self.logger.info(f"Stopping {self.config.name} agent")
        self.status = AgentStatus.STOPPED
        
        try:
            await self._stop()
            self.stats.stop()
            self.logger.info(f"{self.config.name} agent stopped")
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Error stopping agent: {str(e)}", exc_info=True)
            raise
    
    async def process(
        self, 
        context: AgentContext,
        artifact: Optional[Artifact] = None,
        artifacts: Optional[List[Artifact]] = None
    ) -> AgentContext:
        """
        Process one or more artifacts.
        
        Args:
            context: The current agent context.
            artifact: A single artifact to process.
            artifacts: Multiple artifacts to process.
            
        Returns:
            Updated agent context.
        """
        if self.status != AgentStatus.RUNNING:
            await self.start()
            
        if artifact is not None:
            artifacts = [artifact]
        elif artifacts is None:
            artifacts = []
            
        self.logger.debug(
            f"Processing {len(artifacts)} artifacts with {self.config.name} agent"
        )
        
        try:
            # Process artifacts in batches
            for i in range(0, len(artifacts), self.config.batch_size):
                batch = artifacts[i:i + self.config.batch_size]
                context = await self._process_batch(context, batch)
                
            return context
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(
                f"Error in {self.config.name} agent: {str(e)}", 
                exc_info=True
            )
            self.stats.add_error(e)
            raise
    
    async def _process_batch(
        self, 
        context: AgentContext, 
        artifacts: List[Artifact]
    ) -> AgentContext:
        """Process a batch of artifacts."""
        for artifact in artifacts:
            try:
                # Skip artifacts that don't match the agent's capabilities
                if not self._can_process(artifact):
                    self.stats.artifacts_skipped += 1
                    continue
                    
                # Process the artifact
                result = await self._process_artifact(context, artifact)
                
                # Update context with results
                if result is not None:
                    if isinstance(result, Artifact):
                        context.add_artifact(result)
                    elif isinstance(result, ArtifactRelationship):
                        context.add_relationship(result)
                    
                self.stats.artifacts_processed += 1
                
            except Exception as e:
                self.logger.error(
                    f"Error processing artifact {artifact.id}: {str(e)}",
                    exc_info=True
                )
                self.stats.add_error(e, artifact.id)
                
                # Update artifact status
                artifact.status = EvidenceStatus.ERROR
                artifact.processing_errors.append(str(e))
                
        return context
    
    def _can_process(self, artifact: Artifact) -> bool:
        """Determine if this agent can process the given artifact."""
        # Base implementation checks if the agent has the required capabilities
        # Subclasses can override this for more specific logic
        return True
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    async def _start(self) -> None:
        """Perform any setup required before processing artifacts."""
        pass
    
    @abstractmethod
    async def _stop(self) -> None:
        """Perform any cleanup after processing is complete."""
        pass
    
    @abstractmethod
    async def _process_artifact(
        self, 
        context: AgentContext, 
        artifact: Artifact
    ) -> Union[None, Artifact, ArtifactRelationship]:
        """
        Process a single artifact.
        
        Args:
            context: The current agent context.
            artifact: The artifact to process.
            
        Returns:
            - None: No updates to the context
            - Artifact: An updated or new artifact
            - ArtifactRelationship: A new relationship between artifacts
        """
        raise NotImplementedError

# Example agent implementations would go here
# class TimelineAgent(BaseAgent):
#     """Agent for timeline analysis of artifacts."""
#     ...

# class ContradictionDetectionAgent(BaseAgent):
#     """Agent for detecting contradictions between artifacts."""
#     ...

# class EntityExtractionAgent(BaseAgent):
#     """Agent for extracting entities from text content."""
#     ...
