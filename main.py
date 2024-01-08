from arcv import extract_arcv
from levels import read_level_bin
from gm import read_gm_lib, write_gm_lib, merge_patch, GmLib

import logging
from pathlib import Path
from argparse import ArgumentParser


parser = ArgumentParser()
subparsers = parser.add_subparsers(required=True, dest="subparser")

parser_extract = subparsers.add_parser("extract")
parser_extract.add_argument("-i", "--input", type=Path, required=True)
parser_extract.add_argument("-o", "--output", type=Path)

parser_patch = subparsers.add_parser("patch")
parser_patch.add_argument("input", type=Path)
parser_patch.add_argument("patch", type=Path)
parser_patch.add_argument("output", type=Path)


def extract(input: Path, output: Path):
    if output == None:
        output = Path(f"{input.stem}.dat")
    arcv = extract_arcv(input)
    for filename, data in arcv:
        logging.info(f"Extracting {filename}")
        (output / filename).write_bytes(data)
        if filename.endswith(".level.bin"):
            level = read_level_bin(data)
            level_path = output / filename[: -len(".bin")]
            level_path.mkdir(parents=True, exist_ok=True)
            for scriptname, script in level.items():
                logging.info(f"Extracting script {scriptname} in {filename}")
                (level_path / (scriptname + "b")).write_bytes(script)
                lib = read_gm_lib(script)
                (level_path / (scriptname)).write_text(
                    lib.sourceCode.source[:-1].decode("cp1250"),
                    encoding="utf-8",
                )


def patch(input, patch, output):
    gmlib = read_gm_lib(input.read_bytes())
    patchlib = read_gm_lib(patch.read_bytes())
    merge_patch(gmlib, patchlib)
    output.write_bytes(write_gm_lib(gmlib))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    args = parser.parse_args()
    if args.subparser == "extract":
        extract(args.input, args.output)
    elif args.subparser == "patch":
        patch(args.input, args.patch, args.output)
