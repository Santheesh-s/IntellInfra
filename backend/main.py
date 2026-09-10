"""
Campus Spatial Decision Support System — FastAPI backend.

Run with:
    uvicorn main:app --reload
Then visit http://localhost:8000/docs for interactive API docs.
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "nlp"))
sys.path.append(str(Path(__file__).parent / "mcdm"))

sys.path.append(str(Path(__file__).parent / "xai"))

sys.path.append(str(Path(__file__).parent / "software_tier2"))

from database import get_db
from models import Asset, OSRequirement, SoftwareRequirement, SoftwareCache, Location
from nlp_pipeline import NLPPipeline
from topsis_ranker import TOPSISRanker
from shap_explainer import CompatibilityExplainer
from enrichment_pipeline import SoftwareEnrichmentPipeline

nlp_pipeline = NLPPipeline()
os_ranker = TOPSISRanker()
explainer = CompatibilityExplainer()
tier2_pipeline = SoftwareEnrichmentPipeline()

app = FastAPI(
    title="Campus Spatial Decision Support System",
    description="GIS + NLP + XAI framework for OS and software compatibility assessment",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev-only: restrict this to your actual frontend origin before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "campus-dss-api"}


@app.get("/locations")
def list_locations(db: Session = Depends(get_db)):
    """List every lab/room on campus with coordinates."""
    locs = db.query(Location).all()
    return [
        {
            "location_id": l.location_id,
            "block": l.block_name,
            "lab": l.lab_name,
            "floor": l.floor,
            "latitude": l.latitude,
            "longitude": l.longitude,
            "asset_count": l.asset_count,
        }
        for l in locs
    ]


@app.get("/assets")
def list_assets(
    block: Optional[str] = Query(None, description="Filter by block, e.g. 'Block C'"),
    lab: Optional[str] = Query(None, description="Filter by lab name"),
    db: Session = Depends(get_db),
):
    """List hardware assets, optionally filtered by block and/or lab."""
    q = db.query(Asset)
    if block:
        q = q.filter(Asset.block == block)
    if lab:
        q = q.filter(Asset.lab == lab)
    assets = q.all()
    if not assets:
        raise HTTPException(status_code=404, detail="No assets found for that filter")
    return [
        {
            "asset_id": a.asset_id,
            "block": a.block,
            "lab": a.lab,
            "cpu_model": a.cpu_model,
            "ram_gb": a.ram_gb,
            "storage_gb": a.storage_gb,
            "tpm_version": a.tpm_version,
            "current_os": a.current_os,
        }
        for a in assets
    ]


@app.get("/assets/{asset_id}/os-compatibility")
def check_os_compatibility(asset_id: str, os_id: str, db: Session = Depends(get_db)):
    """
    Check a single machine against a single OS's requirements.
    This is the simple rule-based version — the MCDM/SHAP ranking
    engine (Phase 5) will replace this with full multi-OS scoring.
    """
    asset = db.query(Asset).filter(Asset.asset_id == asset_id).first()
    os_req = db.query(OSRequirement).filter(OSRequirement.os_id == os_id).first()

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")
    if not os_req:
        raise HTTPException(status_code=404, detail=f"OS '{os_id}' not found")

    reasons = []
    compatible = True

    if asset.ram_gb < os_req.min_ram_gb:
        compatible = False
        reasons.append(f"RAM {asset.ram_gb}GB below minimum {os_req.min_ram_gb}GB")
    if asset.storage_gb < os_req.min_storage_gb:
        compatible = False
        reasons.append(f"Storage {asset.storage_gb}GB below minimum {os_req.min_storage_gb}GB")
    if asset.cpu_cores < os_req.min_cpu_cores:
        compatible = False
        reasons.append(f"CPU cores {asset.cpu_cores} below minimum {os_req.min_cpu_cores}")
    if os_req.tpm_required is not None:
        if asset.tpm_version is None or asset.tpm_version < os_req.tpm_required:
            compatible = False
            reasons.append(f"TPM {os_req.tpm_required} required, machine has {asset.tpm_version}")

    return {
        "asset_id": asset_id,
        "os_id": os_id,
        "os_name": os_req.os_name,
        "compatible": compatible,
        "reasons": reasons or ["Meets all minimum requirements"],
    }


@app.get("/software/{software_id}/compatible-assets")
def find_compatible_assets_for_software(software_id: str, db: Session = Depends(get_db)):
    """
    Given a software title, find which assets can run it.
    Checks Tier 1 (curated) first, then Tier 2 (cache).
    """
    sw = db.query(SoftwareRequirement).filter(
        SoftwareRequirement.software_id == software_id
    ).first()
    tier = "tier_1"

    if not sw:
        sw = db.query(SoftwareCache).filter(
            SoftwareCache.software_id == software_id
        ).first()
        tier = "tier_2"

    if not sw:
        # Live Tier 2 enrichment: try Wikipedia lookup, cache the result
        def cache_lookup(name):
            cached = db.query(SoftwareCache).filter(SoftwareCache.software_name == name).first()
            return cached

        def cache_save(entry):
            new_cache_row = SoftwareCache(
                software_id=entry["software_id"],
                software_name=entry["software_name"],
                min_ram_gb=entry["min_ram_gb"],
                min_storage_gb=entry["min_storage_gb"],
                supported_os=entry["supported_os"],
                gpu_required=entry["gpu_required"] or False,
                confidence=entry["confidence"],
                source=entry["source"],
                raw_extraction_text=entry["raw_extraction_text"],
                queried_at=entry["queried_at"],
                verified_by_human=False,
            )
            db.merge(new_cache_row)
            db.commit()

        pipeline = SoftwareEnrichmentPipeline(cache_lookup_fn=cache_lookup, cache_save_fn=cache_save)
        enriched = pipeline.lookup(software_id)

        if enriched["confidence"] == "none":
            raise HTTPException(
                status_code=404,
                detail=f"Software '{software_id}' not found in Tier 1, Tier 2 cache, "
                       f"or live Wikipedia lookup. Reason: {enriched['raw_extraction_text']}",
            )

        sw = db.query(SoftwareCache).filter(SoftwareCache.software_name == software_id).first()
        tier = "tier_2_live_enrichment"

    assets = db.query(Asset).filter(
        Asset.ram_gb >= sw.min_ram_gb,
        Asset.storage_gb >= sw.min_storage_gb,
    ).all()

    return {
        "software_id": software_id,
        "software_name": sw.software_name,
        "data_tier": tier,
        "confidence": sw.confidence,
        "compatible_asset_count": len(assets),
        "compatible_assets": [a.asset_id for a in assets],
    }


@app.get("/explain/{asset_id}/{os_id}")
def explain_compatibility(asset_id: str, os_id: str):
    """
    Returns a SHAP-based feature-contribution breakdown for one
    asset x OS pair -- the "why" behind a compatibility score.
    """
    try:
        return explainer.explain(asset_id, os_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/query")
def natural_language_query(text: str, db: Session = Depends(get_db)):
    """
    The main entry point: takes a raw natural language question,
    classifies its intent, extracts entities, and routes to the
    right logic -- exactly the pipeline described in the paper.
    """
    parsed = nlp_pipeline.process(text)

    if parsed["location_is_ambiguous"]:
        parsed["warning"] = (
            f"'{parsed['location']}' does not map to a specific known lab. "
            f"Results may be incomplete or the query may need clarification."
        )

    # Route based on intent -- this is deliberately simple for now.
    # Phase 5 (MCDM) and Phase 6 (Tier 2 software) will replace these
    # with full ranking/enrichment logic.
    result = {"parsed_query": parsed}

    if parsed["intent"] in ("os_compatibility_check", "os_recommendation") and parsed["location"]:
        assets = db.query(Asset).filter(
            (Asset.block == parsed["location"]) | (Asset.lab == parsed["location"])
        ).all()
        result["matched_asset_count"] = len(assets)

        if parsed["intent"] == "os_recommendation":
            # Full TOPSIS ranking per machine
            result["recommendations"] = [
                {
                    "asset_id": a.asset_id,
                    "top_3_os": os_ranker.rank(a.asset_id)[:3],
                }
                for a in assets
            ]
        else:
            # os_compatibility_check against the specifically named OS
            if parsed["target_os"]:
                os_row = db.query(OSRequirement).filter(
                    OSRequirement.os_name == parsed["target_os"]
                ).first()
                if os_row:
                    result["compatibility_results"] = [
                        {
                            "asset_id": a.asset_id,
                            "os_name": parsed["target_os"],
                            "ranking": next(
                                (r for r in os_ranker.rank(a.asset_id) if r["os_id"] == os_row.os_id),
                                None,
                            ),
                            "explanation": explainer.explain(a.asset_id, os_row.os_id),
                        }
                        for a in assets
                    ]
            else:
                result["matched_assets"] = [a.asset_id for a in assets]

    elif parsed["intent"] == "software_compatibility_check" and parsed["software"]:
        sw = db.query(SoftwareRequirement).filter(
            SoftwareRequirement.software_name == parsed["software"]
        ).first()
        if sw:
            result["software_requirements"] = {
                "min_ram_gb": sw.min_ram_gb,
                "min_storage_gb": sw.min_storage_gb,
                "supported_os": sw.supported_os,
            }

    return result
