"""Blockchain sederhana untuk jejak integritas aset catatan DIARYLOCK."""
from datetime import datetime, timezone
import hashlib
import json

import connection as cn

GENESIS_PREVIOUS_HASH = "0" * 64


def _calculate_block_hash(block: dict) -> str:
    payload = {
        "block_index": block["block_index"],
        "timestamp": block["timestamp"],
        "username": block["username"],
        "asset_type": block["asset_type"],
        "asset_id": block.get("asset_id"),
        "asset_name": block["asset_name"],
        "asset_hash": block["asset_hash"],
        "previous_hash": block["previous_hash"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def add_asset_record(username: str, asset_type: str, asset_id: int | None, asset_name: str, asset_bytes: bytes) -> dict:
    latest = cn.get_latest_block()
    block = {
        "block_index": (latest["block_index"] + 1) if latest else 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "username": username,
        "asset_type": asset_type,
        "asset_id": asset_id,
        "asset_name": asset_name,
        "asset_hash": hashlib.sha256(asset_bytes).hexdigest(),
        "previous_hash": latest["block_hash"] if latest else GENESIS_PREVIOUS_HASH,
    }
    block["block_hash"] = _calculate_block_hash(block)
    cn.insert_block(block)
    return block


def verify_chain() -> tuple[bool, list[str]]:
    blocks = cn.get_all_blocks()
    messages: list[str] = []
    previous_hash = GENESIS_PREVIOUS_HASH
    expected_index = 0
    valid = True

    for row in blocks:
        block = dict(row)
        if block["block_index"] != expected_index:
            valid = False
            messages.append(f"Blok #{block['block_index']}: urutan indeks tidak sesuai.")
        if block["previous_hash"] != previous_hash:
            valid = False
            messages.append(f"Blok #{block['block_index']}: previous hash tidak cocok.")
        calculated = _calculate_block_hash(block)
        if calculated != block["block_hash"]:
            valid = False
            messages.append(f"Blok #{block['block_index']}: hash blok tidak cocok.")
        if block["asset_type"] == "diary" and block["asset_id"] is not None:
            entry = cn.run_query(
                "SELECT encrypted_payload FROM diary_entries WHERE id = ?",
                (block["asset_id"],),
            )
            if not entry:
                valid = False
                messages.append(f"Blok #{block['block_index']}: catatan terkait tidak ditemukan.")
            else:
                actual_hash = hashlib.sha256(entry[0]["encrypted_payload"].encode("utf-8")).hexdigest()
                if actual_hash != block["asset_hash"]:
                    valid = False
                    messages.append(f"Blok #{block['block_index']}: ciphertext catatan berubah.")
        previous_hash = block["block_hash"]
        expected_index += 1

    if valid:
        messages.append(f"Valid: {len(blocks)} blok berhasil diperiksa dan rantai hash konsisten.")
    return valid, messages


def verify_uploaded_asset(block_id: int, file_bytes: bytes) -> bool:
    rows = cn.run_query("SELECT asset_hash FROM blockchain_blocks WHERE id = ?", (block_id,))
    if not rows:
        return False
    return hashlib.sha256(file_bytes).hexdigest() == rows[0]["asset_hash"]
