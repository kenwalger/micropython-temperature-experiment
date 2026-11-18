"""Investigate the original journal CRC32 serialization mismatch.

This script intentionally inspects the historical v0 envelope format."""


import json
import binascii

with open("observations.jsonl", "r") as f:
    line = f.readline()

envelope = json.loads(line)
payload = envelope["payload"]

reserialized = json.dumps(payload)
calculated = "%08x" % (
    binascii.crc32(reserialized.encode()) & 0xFFFFFFFF
)

print("Stored CRC:", envelope["crc32"])
print("Recalculated CRC:", calculated)
print("Match:", calculated == envelope["crc32"])
print("Reserialized payload:", reserialized)
