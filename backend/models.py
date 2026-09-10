"""
SQLAlchemy models for the Campus Spatial Decision Support System.
Mirrors the structure of the 6 source CSVs exactly, so loading is a direct mapping.
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text
)
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry
import datetime

Base = declarative_base()


class Location(Base):
    """Campus spatial data — one row per lab/room."""
    __tablename__ = "locations"

    location_id = Column(String, primary_key=True)
    block_name = Column(String, nullable=False)
    lab_name = Column(String, nullable=False)
    floor = Column(Integer)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry(geometry_type="POINT", srid=4326))
    asset_count = Column(Integer, default=0)

    assets = relationship("Asset", back_populates="location")


class Asset(Base):
    """Hardware inventory — one row per physical machine."""
    __tablename__ = "assets"

    asset_id = Column(String, primary_key=True)
    block = Column(String, nullable=False)
    lab = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    cpu_model = Column(String)
    cpu_generation = Column(Integer)
    cpu_cores = Column(Integer)
    cpu_clock_ghz = Column(Float)
    ram_gb = Column(Integer)
    storage_type = Column(String)
    storage_gb = Column(Integer)
    gpu = Column(String)
    tpm_version = Column(Float, nullable=True)   # NULL = no TPM chip present
    secure_boot_support = Column(Boolean)
    purchase_year = Column(Integer)
    current_os = Column(String)
    architecture = Column(String)
    last_updated = Column(String)

    location_id = Column(String, ForeignKey("locations.location_id"), nullable=True)
    location = relationship("Location", back_populates="assets")

    scores = relationship("CompatibilityScore", back_populates="asset")


class OSRequirement(Base):
    """OS requirements matrix — one row per operating system."""
    __tablename__ = "os_requirements"

    os_id = Column(String, primary_key=True)
    os_name = Column(String, nullable=False)
    os_family = Column(String)
    min_ram_gb = Column(Integer)
    recommended_ram_gb = Column(Integer)
    min_storage_gb = Column(Integer)
    min_cpu_cores = Column(Integer)
    min_clock_ghz = Column(Float)
    tpm_required = Column(Float, nullable=True)  # NULL = not required
    secure_boot_required = Column(Boolean)
    architecture_support = Column(String)  # semicolon-separated, e.g. "x86;x64"
    eol_date = Column(String, nullable=True)
    source_url = Column(String)
    best_use_case = Column(String)

    scores = relationship("CompatibilityScore", back_populates="os")


class SoftwareRequirement(Base):
    """Tier 1 — curated, manually verified software catalog."""
    __tablename__ = "software_requirements"

    software_id = Column(String, primary_key=True)
    software_name = Column(String, nullable=False)
    category = Column(String)
    min_ram_gb = Column(Integer)
    min_storage_gb = Column(Integer)
    min_cpu_cores = Column(Integer)
    gpu_required = Column(Boolean)
    gpu_min_vram_gb = Column(Integer)
    supported_os = Column(String)  # semicolon-separated
    confidence = Column(String, default="high")
    source = Column(String)
    source_url = Column(String, nullable=True)
    last_verified = Column(String)


class SoftwareCache(Base):
    """Tier 2 — dynamically enriched software lookups, grows at runtime."""
    __tablename__ = "software_cache"

    software_id = Column(String, primary_key=True)
    software_name = Column(String, nullable=False)
    min_ram_gb = Column(Integer)
    min_storage_gb = Column(Integer)
    supported_os = Column(String)
    gpu_required = Column(Boolean)
    confidence = Column(String)  # high | medium | low
    source = Column(String)
    raw_extraction_text = Column(Text, nullable=True)
    queried_at = Column(String)
    verified_by_human = Column(Boolean, default=False)


class NLPQuery(Base):
    """Labeled NLP query dataset — used for training/evaluating the intent classifier."""
    __tablename__ = "nlp_queries"

    query_id = Column(String, primary_key=True)
    text = Column(Text, nullable=False)
    intent = Column(String, nullable=False)
    location = Column(String, nullable=True)
    target_os = Column(String, nullable=True)
    software = Column(String, nullable=True)
    condition = Column(String, nullable=True)


class CompatibilityScore(Base):
    """
    Computed output — NOT loaded from a CSV.
    Populated at runtime by the MCDM (TOPSIS) + SHAP engine.
    """
    __tablename__ = "compatibility_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String, ForeignKey("assets.asset_id"))
    os_id = Column(String, ForeignKey("os_requirements.os_id"))
    suitability_score = Column(Float)
    rank = Column(Integer)
    shap_ram = Column(Float, nullable=True)
    shap_tpm = Column(Float, nullable=True)
    shap_storage = Column(Float, nullable=True)
    shap_cpu = Column(Float, nullable=True)
    computed_at = Column(DateTime, default=datetime.datetime.utcnow)

    asset = relationship("Asset", back_populates="scores")
    os = relationship("OSRequirement", back_populates="scores")
