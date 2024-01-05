import zlib
import math
from pathlib import Path
import os


def entropy(b):
    e = 0
    byte_counts = [0] * 256
    for x in b:
        byte_counts[x] += 1

    for count in byte_counts:
        if count == 0:
            continue
        p = 1.0 * count / len(b)
        e -= p * math.log(p, 256)
    return e


def extract_arcv(arcv_path):
    with open(arcv_path, "rb") as f:
        data = f.read()
    magic = data[:5]
    assert magic == b"ARCV\x00"
    header_len = int.from_bytes(data[6:10], "little")
    header_ = data[10 : 10 + header_len]
    header = zlib.decompress(header_[11:], -8)

    file_count = int.from_bytes(header[:4], "little")
    header_sz = int.from_bytes(header[4:8], "little")
    file_name_len = list(map(lambda x: x + 1, header[8 : 8 + file_count]))
    file_names = header[8 + file_count :].split(b"\0")

    file_offsets_ = data[14 + header_len : 14 + header_len + (file_count + 1) * 4]
    file_offsets = [
        int.from_bytes(file_offsets_[i : i + 4], "little")
        for i in range(0, len(file_offsets_), 4)
    ]

    data2 = data[14+header_len+(file_count+1)*4:]

    for i in range(0, len(file_offsets) - 1):
        chunk = data2[file_offsets[i] : file_offsets[i + 1]]
        filename = file_names[i].decode()
        # first 9 bytes is unknown(maybe checksum)
        chunk2 = chunk[9:]
        # extract fragments
        segments = []
        total_len = 0
        while total_len < len(chunk2):
            frag_len = int.from_bytes(
                chunk2[2 * len(segments) : 2 * (1 + len(segments))], "little"
            )
            if frag_len == 0:
                frag_len = 0x10000
            segments.append(frag_len)
            total_len += frag_len + 2
        chunk2 = chunk2[2 * len(segments) :]

        cursor = 0
        rawdata = b""
        for seg_size in segments:
            filedata = chunk2[cursor : min(cursor + seg_size, len(chunk2))]
            if seg_size != 0x10000:
                rawdata += zlib.decompress(filedata, -zlib.MAX_WBITS)
            else:
                rawdata += filedata
            cursor += seg_size

        e = entropy(rawdata)
        print(
            f"{i}: {filename} off: 0x{file_offsets[i]:X} len: {file_offsets[i+1]-file_offsets[i]} entropy: {e:.2f}"
        )

        folder = Path(f"{Path(arcv_path).stem}.dat")
        dirname = folder / os.path.dirname(filename)
        os.makedirs(dirname, exist_ok=True)
        with open(folder / filename, "wb") as f:
            f.write(rawdata)


if __name__ == "__main__":
    import sys

    extract_arcv(sys.argv[1])
