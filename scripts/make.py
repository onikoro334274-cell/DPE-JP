#!/usr/bin/env python3

import os
import subprocess
import sys

############
#Options go here.
############

ROM_NAME = "BPRJ0.gba"  #The name of your rom
OFFSET_TO_PUT = 0x1600000
SEARCH_FREE_SPACE = False  # Set to True if you want the script to search for free space
                           # Set to False if you don't want to search for free space as you for example update the engine

#############
# Options end here.
#############

###############
# Functions start here.
###############


def MakeOffset0x100Aligned(offset: int) -> int:
    return (offset + 15) & ~15


def FindOffsetToPut(rom, neededBytes: int, startOffset: int) -> int:
    if neededBytes <= 0 or startOffset < 0:
        raise ValueError("Invalid free-space search range")
    offset = MakeOffset0x100Aligned(startOffset)
    rom.seek(offset)
    run_start = offset
    run_length = 0
    while True:
        chunk = rom.read(65536)
        if not chunk:
            raise ValueError("End of file reached. Not enough free space.")
        for value in chunk:
            if value != 0xFF:
                run_length = 0
                run_start = MakeOffset0x100Aligned(offset + 1)
            elif offset >= run_start:
                run_length += 1
                if run_length >= neededBytes:
                    return run_start
            offset += 1


def ChangeFileLine(filePath: str, lineToChange: int, replacement: str):
    with open(filePath, 'r') as file:
        lines = file.readlines()
    if not 1 <= lineToChange <= len(lines):
        raise ValueError("Line number outside file")
    lines[lineToChange - 1] = replacement
    with open(filePath, 'w') as file:
        file.writelines(lines)


def EditLinker(offset: int):
    if not 0 <= offset < 0x2000000 or offset % 4:
        raise ValueError("Insertion offset must be aligned and inside a 32 MiB ROM")
    ChangeFileLine("linker.ld", 4, "\t\trom     : ORIGIN = (0x08000000 + " + hex(offset)
                   + "), LENGTH = (32M - " + hex(offset) + ")\n")


def EditInsert(offset: int):
    filePath = "./scripts/insert.py"
    with open(filePath) as file:
        lines = file.readlines()
    replacements = {'OFFSET_TO_PUT': hex(offset), 'SOURCE_ROM': repr(ROM_NAME)}
    for name, value in replacements.items():
        matches = [i for i, line in enumerate(lines) if line.split('=', 1)[0].strip() == name]
        if len(matches) != 1:
            raise ValueError("Expected one assignment for " + name)
        lines[matches[0]] = name + ' = ' + value + '\n'
    with open(filePath, 'w') as file:
        file.writelines(lines)


def BuildCode():
    subprocess.check_call([sys.executable, "scripts/build.py"])


def InsertCode():
    subprocess.check_call([sys.executable, "scripts/insert.py"])


def ClearFromTo(rom, from_: int, to_: int):
    if from_ < 0 or to_ < from_:
        raise ValueError("Invalid clear range")
    rom.seek(from_)
    remaining = to_ - from_
    block = b'\xFF' * 65536
    while remaining:
        size = min(remaining, len(block))
        rom.write(block[:size])
        remaining -= size

##############
# Functions end here.
##############


def main():
    try:
        with open(ROM_NAME, 'rb') as rom:
            offset = OFFSET_TO_PUT
            if SEARCH_FREE_SPACE is True:
                offset = FindOffsetToPut(rom, 0x50000, MakeOffset0x100Aligned(offset))

            EditLinker(offset)
            EditInsert(offset)
            BuildCode()
            InsertCode()
            rom.close()

    except FileNotFoundError:
        print('Error: Could not find source rom: "' + ROM_NAME + '".\n'
              + 'Please make sure a rom with this name exists in the root.')
        sys.exit(1)
    except (ValueError, subprocess.CalledProcessError) as error:
        print('Error:', error, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

