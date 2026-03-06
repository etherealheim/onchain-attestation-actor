"""Data models for attestations."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AttestationMetadata(BaseModel):
    """Metadata about the attestation."""

    actor_id: Optional[str] = None
    run_id: Optional[str] = None
    source_url: Optional[str] = None
    description: Optional[str] = None
    custom: Optional[Dict[str, Any]] = None


class AttestationOptions(BaseModel):
    """Options for attestation creation."""

    verification_url: bool = True
    store_full_data: bool = True


class AttestationInput(BaseModel):
    """Input for creating an attestation."""

    chain: str = Field(..., description="Blockchain to use (solana or base)")
    data: Dict[str, Any] = Field(..., description="Data to attest")
    metadata: Optional[AttestationMetadata] = None
    options: Optional[AttestationOptions] = AttestationOptions()

    # Verification mode
    verify: bool = False
    tx_hash: Optional[str] = None


class CostInfo(BaseModel):
    """Cost information for the attestation."""

    chain_fee_usd: float
    token: str
    amount: float


class VerificationInfo(BaseModel):
    """Verification instructions."""

    method: str = "SHA-256 hash of JSON-canonicalized input data"
    instructions: str = "Hash your data with SHA-256 and compare with data_hash"


class AttestationOutput(BaseModel):
    """Output from attestation creation."""

    attestation_id: str
    chain: str
    tx_hash: str
    explorer_url: str
    data_hash: str
    attestor_address: str
    timestamp: str
    block_number: Optional[int] = None
    verification: VerificationInfo
    cost: CostInfo
    metadata: Optional[Dict[str, Any]] = None

    # Optional: link to full data stored in Apify
    apify_data_url: Optional[str] = None


class VerificationResult(BaseModel):
    """Result of attestation verification."""

    verified: bool
    attestation: Optional[AttestationOutput] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
