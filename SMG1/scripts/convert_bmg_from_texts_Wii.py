#!/usr/bin/env python3
"""
convert_bmg_from_texts_wii.py

Build a Wii-compatible message.bmg from translated JSON files,
preserving original BMG metadata/layout. This script applies a
small post-save patch to fix a byte-order/packing mismatch in the
FLI1 header that otherwise causes "Unexpected FLI1 entry length (0)".
"""
import json
import os
import re
import sys

import bmg

WII_CONTROL_CONVERTER = {
    re.compile(r"\\f"): r"[1:0001]",
    re.compile(r"\[unk1\]"): r"[1:0002]",
    re.compile(r"\[wait:([0-9a-f]{2})([0-9a-f]{2})\]"): r"[1:0000\1\2]",
    re.compile(r"\[icon:([0-9a-f]{2})([0-9a-f]{2})\]"): r"[3:\1\2]",
    re.compile(r"\[unk4:([0-9a-f]{2})([0-9a-f]{2})\]"): r"[4:\1\2]",
    re.compile(r"\[unk5:([0-9a-f]{2})\]"): r"[5:0000\g<1>00]",
    re.compile(
        r"\[placeholder6:([0-9a-f]{2})([0-9a-f]{2}),([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})\]"
    ): r"[6:\g<1>\g<2>00000000\g<3>\g<4>\g<5>\g<6>]",
    re.compile(
        r"\[placeholder7:([0-9a-f]{2})([0-9a-f]{2}),([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})\]"
    ): r"[7:\g<1>\g<2>00000000\g<3>\g<4>\g<5>\g<6>]",
    re.compile(r"\[unk9:([0-9a-f]{2})([0-9a-f]{2})\]"): r"[9:\1\2]",
    re.compile(r"\[color:([0-9a-f]{2})\]"): r"[255:0000\g<1>00]",
}


def load_json(path):
    with open(path, "r", -1, "utf8") as fh:
        return json.load(fh)


def patch_fli1_header_bytes(data: bytes, original_data: bytes | None = None) -> bytes:
    """
    Patch the saved BMG bytes to fix swapped entryLength/unk0B bytes in FLI1 header.

    Strategy:
    - Find "FLI1" (or "1ILF") in data.
    - At offset+8 the parser expects: H (count), B (entryLength), B (unk0B), I (unk0C).
    - Some writers incorrectly wrote the 16-bit word as 0x0008 instead of 0x0800,
      resulting in entryLength==0 and unk0B==8 (swapped). We detect this case
      and swap the two bytes to restore entryLength=8, unk0B=0.
    - If original_data is given, we use the original's two bytes as the canonical source.
    """
    b = bytearray(data)
    idx = data.find(b"FLI1")
    if idx == -1:
        idx = data.find(b"1ILF")
    if idx == -1:
        # no FLI1 found, nothing to patch
        return bytes(b)

    # positions of the two bytes we may need to swap:
    # parser reads bytes at idx+10 (entryLength) and idx+11 (unk0B)
    pos_entry = idx + 10
    pos_unk = idx + 11
    if pos_unk >= len(b):
        return bytes(b)

    entry_val = b[pos_entry]
    unk_val = b[pos_unk]

    # If it looks like the swapped case (entry==0 and unk==8) then correct it
    if entry_val == 0 and unk_val == 8:
        # If original_data supplied, copy the original pair (safer)
        if original_data:
            orig_idx = original_data.find(b"FLI1")
            if orig_idx == -1:
                orig_idx = original_data.find(b"1ILF")
            if orig_idx != -1 and orig_idx + 11 < len(original_data):
                b[pos_entry] = original_data[orig_idx + 10]
                b[pos_unk] = original_data[orig_idx + 11]
                print("Patched FLI1 header bytes using original file bytes.")
                return bytes(b)

        # else swap them (entry gets 8, unk gets 0)
        b[pos_entry], b[pos_unk] = unk_val, entry_val
        print("Detected swapped FLI1 entryLength/unk0B; swapped bytes to fix entryLength=8.")
    else:
        # No obvious swap needed. However, we can also accept the case where entry_val != 0.
        print("No FLI1 swapping needed (entry_len, unk) =", entry_val, unk_val)

    return bytes(b)


def main():
    ja_path = "texts/ja/wii/messages.json"
    zh_path = "texts/zh_Hans/nsw/messages.json"
    bmg_input_path = "unpacked/wii/Message/message.bmg"
    out_path = "temp/import_wii/Message/message.bmg"

    if not os.path.exists(ja_path) or not os.path.exists(zh_path):
        print("Missing JSON files. Expected:", ja_path, "and", zh_path, file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(bmg_input_path):
        print("Missing original Wii BMG:", bmg_input_path, file=sys.stderr)
        sys.exit(1)

    ja_items = load_json(ja_path)
    zh_items = load_json(zh_path)
    zh_dict = {it["key"]: it for it in zh_items}

    # Merge translations
    translated_items = ja_items
    for it in translated_items:
        k = it["key"]
        if k in zh_dict:
            it["translation"] = zh_dict[k].get("translation", it.get("translation", ""))

    # Load original bmg to preserve metadata/layout
    with open(bmg_input_path, "rb") as fh:
        orig_bytes = fh.read()
    base_bmg = bmg.BMG(orig_bytes)

    # Apply translations into loaded BMG object
    for i, msg in enumerate(base_bmg.messages):
        try:
            text = translated_items[i]["translation"]
        except IndexError:
            text = ""
        if text == "":
            continue

        for pat, rep in WII_CONTROL_CONVERTER.items():
            text = pat.sub(rep, text)

        parts = []
        pos = 0
        L = len(text)
        while pos < L:
            next_br = text.find("[", pos)
            if next_br == -1:
                chunk = text[pos:]
                if chunk:
                    parts.append(chunk)
                break
            if next_br > pos:
                parts.append(text[pos:next_br])
            end_br = text.find("]", next_br)
            if end_br == -1:
                raise ValueError(f"Missing closing bracket in message #{i}: '{text[next_br:]}'")
            inner = text[next_br + 1 : end_br]
            if ":" not in inner:
                parts.append(text[next_br : end_br + 1])
                pos = end_br + 1
                continue
            control_type, control_data = inner.split(":", 1)
            try:
                control_bytes = bytes.fromhex(control_data)
            except Exception as ex:
                raise ValueError(f"Bad hex in control token in message #{i}: '{inner}' -> {ex}") from ex

            parts.append(bmg.Message.Escape(int(control_type), control_bytes, base_bmg.magic_endianness))
            pos = end_br + 1

        msg.stringParts = parts

    # Save, then patch FLI1 bytes if necessary
    new_bytes = base_bmg.save()
    new_bytes = patch_fli1_header_bytes(new_bytes, original_data=orig_bytes)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as fh:
        fh.write(new_bytes)

    print(f"Wii BMG written to: {out_path} (size {len(new_bytes)} bytes)")

    # Validate by reloading
    try:
        _ = bmg.BMG(new_bytes)
        print("Validation: saved Wii BMG successfully parsed by bmg.BMG()")
    except Exception as exc:
        print("Validation error: bmg.BMG() failed to parse the saved file.", file=sys.stderr)
        print("Exception:", exc, file=sys.stderr)
        print("First 256 bytes (hex):", new_bytes[:256].hex(), file=sys.stderr)
        print("Original first 256 bytes (hex):", orig_bytes[:256].hex(), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
