import os
import sys
import json
from glob import glob

# Data
TM_HM_COUNT = 128
TUTOR_COUNT = 152
SPECIES_COUNT = 0x59F + 1

TM_OUTPUT = "assembly/generated/tm_compatibility.s"
TUTOR_OUTPUT = "assembly/generated/tutor_compatibility.s"
TM_COMPATIBILITY = "src/tm_compatibility"
TUTOR_COMPATIBILITY = "src/tutor_compatibility"
SPECIES_DEFINES = "include/species.h"


# Uses pre-made files corresponding to each TM to build species TM Data
def TMDataBuilder():
    DataBuilder(TM_COMPATIBILITY, TM_HM_COUNT, TM_OUTPUT, "TMHM")


def TutorDataBuilder():
    DataBuilder(TUTOR_COMPATIBILITY, TUTOR_COUNT, TUTOR_OUTPUT, "Tutor")


def DataBuilder(directory: str, numEntries: int, outputFile: str, dataType: str):
    fileList = sorted(glob(os.path.join(directory, '**', '*.txt'), recursive=True))
    if not fileList or numEntries <= 0:
        raise ValueError("Missing compatibility files or invalid move count")
    dependencies = fileList + [SPECIES_DEFINES, 'scripts/tm_tutor.py']
    manifest = {'entries': numEntries, 'species': SPECIES_COUNT,
                'files': [[path, os.stat(path).st_mtime_ns, os.stat(path).st_size] for path in dependencies]}
    manifestFile = outputFile + '.json'
    try:
        with open(manifestFile) as file:
            previous = json.load(file)
    except (FileNotFoundError, ValueError):
        previous = None
    if os.path.isfile(outputFile) and manifest == previous:
        return

    print("Processing {} Data.".format(dataType))
    compatibilityTable = [bytearray((numEntries + 7) // 8) for _ in range(SPECIES_COUNT)]
    seenIds = set()
    for filePath in fileList:
        tmId = int(os.path.basename(filePath).split()[0]) - 1
        if not 0 <= tmId < numEntries or tmId in seenIds:
            raise ValueError("Invalid or duplicate move number in " + filePath)
        seenIds.add(tmId)
        with open(filePath) as file:
            for i, line in enumerate(file, 1):
                value = line.strip()
                if not value or ':' in value or value.startswith('//'):
                    continue
                try:
                    species = int(value)
                except ValueError:
                    try:
                        species = int(value, 16)
                    except ValueError:
                        key = value if value.startswith('SPECIES_') else 'SPECIES_' + value
                        if key not in ReverseSpeciesDict:
                            raise ValueError("Unknown species {} at {}:{}".format(value, filePath, i))
                        species = ReverseSpeciesDict[key]
                if not 0 <= species < SPECIES_COUNT:
                    raise ValueError("Species outside table at {}:{}".format(filePath, i))
                compatibilityTable[species][tmId // 8] |= 1 << (tmId % 8)

    temporary = outputFile + '.tmp'
    with open(temporary, 'w') as output:
        output.write(".thumb\n.align 2\n\n@THIS IS A GENERATED FILE! DO NOT MODIFY IT!\n\n"
                     ".global g{}Learnsets\ng{}Learnsets:\n".format(dataType, dataType))
        for mon in compatibilityTable:
            output.write('.byte ' + ','.join(hex(byte) for byte in mon) + '\n')
    os.replace(temporary, outputFile)
    with open(manifestFile, 'w') as file:
        json.dump(manifest, file)


# Utility Functions
def FixEndian(string: str) -> str:  # Converts bitlist from big endian to little endian
    index, newString = 0, ''
    for a in range(len(string) + 1):
        if index % 8 == 0 and index != 0:
            newString += ReverseString(string[index - 8:index])
        index += 1
    return newString


def ReverseString(string: str) -> str:
    return ''.join(string[len(string)-a-1] for a in range(len(string)))


def PokemonDataListInitializer(numEntries: int) -> [[]]:
    outerList = []
    for a in range(int(SPECIES_COUNT)):
        innerList = [0] * numEntries
        outerList.append(innerList)
    return outerList


def DefinesDictMaker(definesFile: str) -> {}:
    definesDict = {}
    with open(definesFile, 'r') as file:
        for line in file:
            if '#define ' in line:
                lineList = line.split()
                try:
                    definesDict[int(lineList[2])] = lineList[1]
                except:
                    try:
                        definesDict[int(lineList[2], 16)] = lineList[1]
                    except:
                        pass
    return definesDict


def ReverseDict(dictionary: {}):
    reverseDict = {}
    for key in dictionary:
        reverseDict[dictionary[key]] = key

    return reverseDict


def ChangeFileLine(filePath: str, lineToChange: int, replacement: str):
    with open(filePath) as file:
        lines = file.readlines()
    if not 1 <= lineToChange <= len(lines):
        raise ValueError("Line number outside file")
    lines[lineToChange - 1] = replacement
    with open(filePath, 'w') as file:
        file.writelines(lines)


SpeciesDict = DefinesDictMaker(SPECIES_DEFINES)
SPECIES_COUNT = max(SpeciesDict) + 1
ReverseSpeciesDict = ReverseDict(SpeciesDict)

if __name__ == '__main__':
    TMDataBuilder()
    TutorDataBuilder()
