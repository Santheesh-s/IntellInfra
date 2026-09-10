"""
Loads the 6 source CSVs into PostgreSQL.
Run this once after creating the database and enabling PostGIS.

Usage:
    python load_data.py
"""
import pandas as pd
from sqlalchemy import text
from database import engine, SessionLocal
from models import (
    Base, Location, Asset, OSRequirement,
    SoftwareRequirement, SoftwareCache, NLPQuery
)

DATA_DIR = "../data"


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


def load_locations(session):
    df = pd.read_csv(f"{DATA_DIR}/campus_spatial_data.csv")
    for _, row in df.iterrows():
        loc = Location(
            location_id=row["location_id"],
            block_name=row["block_name"],
            lab_name=row["lab_name"],
            floor=int(row["floor"]) if pd.notna(row["floor"]) else None,
            latitude=row["latitude"],
            longitude=row["longitude"],
            geom=f"SRID=4326;POINT({row['longitude']} {row['latitude']})",
            asset_count=int(row["asset_count"]) if pd.notna(row["asset_count"]) else 0,
        )
        session.merge(loc)
    session.commit()
    print(f"Loaded {len(df)} locations.")


def load_assets(session):
    df = pd.read_csv(f"{DATA_DIR}/hardware_inventory.csv")
    for _, row in df.iterrows():
        asset = Asset(
            asset_id=row["asset_id"],
            block=row["block"],
            lab=row["lab"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            cpu_model=row["cpu_model"],
            cpu_generation=int(row["cpu_generation"]),
            cpu_cores=int(row["cpu_cores"]),
            cpu_clock_ghz=row["cpu_clock_ghz"],
            ram_gb=int(row["ram_gb"]),
            storage_type=row["storage_type"],
            storage_gb=int(row["storage_gb"]),
            gpu=row["gpu"],
            tpm_version=row["tpm_version"] if pd.notna(row["tpm_version"]) else None,
            secure_boot_support=bool(row["secure_boot_support"]),
            purchase_year=int(row["purchase_year"]),
            current_os=row["current_os"],
            architecture=row["architecture"],
            last_updated=str(row["last_updated"]),
        )
        session.merge(asset)
    session.commit()
    print(f"Loaded {len(df)} assets.")


def load_os_requirements(session):
    df = pd.read_csv(f"{DATA_DIR}/os_requirements.csv")
    for _, row in df.iterrows():
        osr = OSRequirement(
            os_id=row["os_id"],
            os_name=row["os_name"],
            os_family=row["os_family"],
            min_ram_gb=int(row["min_ram_gb"]),
            recommended_ram_gb=int(row["recommended_ram_gb"]),
            min_storage_gb=int(row["min_storage_gb"]),
            min_cpu_cores=int(row["min_cpu_cores"]),
            min_clock_ghz=row["min_clock_ghz"],
            tpm_required=row["tpm_required"] if pd.notna(row["tpm_required"]) else None,
            secure_boot_required=bool(row["secure_boot_required"]),
            architecture_support=row["architecture_support"],
            eol_date=row["eol_date"] if pd.notna(row["eol_date"]) else None,
            source_url=row["source_url"],
            best_use_case=row["best_use_case"],
        )
        session.merge(osr)
    session.commit()
    print(f"Loaded {len(df)} OS requirements.")


def load_software_requirements(session):
    df = pd.read_csv(f"{DATA_DIR}/software_requirements.csv")
    for _, row in df.iterrows():
        sw = SoftwareRequirement(
            software_id=row["software_id"],
            software_name=row["software_name"],
            category=row["category"],
            min_ram_gb=int(row["min_ram_gb"]),
            min_storage_gb=int(row["min_storage_gb"]),
            min_cpu_cores=int(row["min_cpu_cores"]),
            gpu_required=bool(row["gpu_required"]),
            gpu_min_vram_gb=int(row["gpu_min_vram_gb"]),
            supported_os=row["supported_os"],
            confidence=row["confidence"],
            source=row["source"],
            source_url=row["source_url"] if pd.notna(row["source_url"]) else None,
            last_verified=row["last_verified"],
        )
        session.merge(sw)
    session.commit()
    print(f"Loaded {len(df)} software requirements (Tier 1).")


def load_software_cache(session):
    df = pd.read_csv(f"{DATA_DIR}/software_cache.csv")
    for _, row in df.iterrows():
        cache = SoftwareCache(
            software_id=row["software_id"],
            software_name=row["software_name"],
            min_ram_gb=int(row["min_ram_gb"]),
            min_storage_gb=int(row["min_storage_gb"]),
            supported_os=row["supported_os"],
            gpu_required=bool(row["gpu_required"]),
            confidence=row["confidence"],
            source=row["source"],
            raw_extraction_text=row["raw_extraction_text"],
            queried_at=row["queried_at"],
            verified_by_human=bool(row["verified_by_human"]),
        )
        session.merge(cache)
    session.commit()
    print(f"Loaded {len(df)} software cache entries (Tier 2).")


def load_nlp_queries(session):
    df = pd.read_csv(f"{DATA_DIR}/nlp_query_dataset_10000.csv")
    for _, row in df.iterrows():
        q = NLPQuery(
            query_id=row["query_id"],
            text=row["text"],
            intent=row["intent"],
            location=row["location"] if pd.notna(row["location"]) else None,
            target_os=row["target_os"] if pd.notna(row["target_os"]) else None,
            software=row["software"] if pd.notna(row["software"]) else None,
            condition=row["condition"] if pd.notna(row["condition"]) else None,
        )
        session.merge(q)
    session.commit()
    print(f"Loaded {len(df)} NLP queries.")


if __name__ == "__main__":
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()

    create_tables()
    session = SessionLocal()
    try:
        load_locations(session)
        load_assets(session)
        load_os_requirements(session)
        load_software_requirements(session)
        load_software_cache(session)
        load_nlp_queries(session)
        print("\nAll datasets loaded successfully.")
    finally:
        session.close()
