import sys
import os
import io
import struct
import tarfile
import zipfile

import pytest

# Add the repo root to sys.path so tests can import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def make_minimal_pe(path, machine=0x8664):
    """
    Writes a header-only PE file that pefile parses successfully.
    machine: 0x8664 for 64-bit (AMD64), 0x14c for 32-bit (i386).
    """
    is64 = machine == 0x8664
    dos = bytearray(64)
    dos[0:2] = b"MZ"
    dos[60:64] = struct.pack("<I", 64)  # e_lfanew → PE signature right after DOS header

    opt_size = 240 if is64 else 224
    characteristics = 0x0002 | (0 if is64 else 0x0100)  # EXECUTABLE_IMAGE (+ 32BIT_MACHINE)
    coff = struct.pack("<HHIIIHH", machine, 0, 0, 0, 0, opt_size, characteristics)

    if is64:
        opt = struct.pack("<HBBIIIII", 0x20B, 0, 0, 0, 0, 0, 0, 0)
        opt += struct.pack("<QIIHHHHHHIIIIHHQQQQII",
                           0x140000000, 0x1000, 0x200, 6, 0, 0, 0, 6, 0, 0,
                           0x2000, 0x400, 0, 2, 0, 0x100000, 0x1000, 0x100000, 0x1000, 0, 16)
    else:
        opt = struct.pack("<HBBIIIIII", 0x10B, 0, 0, 0, 0, 0, 0, 0, 0)
        opt += struct.pack("<IIIHHHHHHIIIIHHIIIIII",
                           0x400000, 0x1000, 0x200, 6, 0, 0, 0, 6, 0, 0,
                           0x2000, 0x400, 0, 2, 0, 0x100000, 0x1000, 0x100000, 0x1000, 0, 16)
    opt += b"\0" * (16 * 8)  # 16 empty data directories
    assert len(opt) == opt_size

    data = bytes(dos) + b"PE\0\0" + coff + opt
    data += b"\0" * (0x400 - len(data))
    with open(path, "wb") as f:
        f.write(data)
    return path


def make_archive(fmt, prefix, subfolders, dll_names, payload_for):
    """
    Builds an in-memory DXVK/vkd3d-style archive:
        {prefix}/{subfolder}/{dll}   with contents payload_for(subfolder, dll)
    fmt: 'zip', 'tar.gz' or 'tar.zst'. Returns bytes.
    """
    if fmt == "zip":
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(f"{prefix}/", "")
            for sub in subfolders:
                for dll in dll_names:
                    zf.writestr(f"{prefix}/{sub}/{dll}", payload_for(sub, dll))
        return buf.getvalue()

    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w") as tf:
        for sub in subfolders:
            for dll in dll_names:
                data = payload_for(sub, dll)
                info = tarfile.TarInfo(f"{prefix}/{sub}/{dll}")
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
    raw = tar_buf.getvalue()

    if fmt == "tar.gz":
        import gzip
        return gzip.compress(raw)
    if fmt == "tar.zst":
        import zstandard
        return zstandard.ZstdCompressor().compress(raw)
    raise ValueError(fmt)


@pytest.fixture
def game_dir(tmp_path):
    """An empty fake game folder with a 64-bit game.exe."""
    make_minimal_pe(str(tmp_path / "game.exe"), 0x8664)
    return str(tmp_path)
