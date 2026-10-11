#!/usr/bin/env python3

from glob import glob
from pathlib import Path
import os
import itertools
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from string import StringFileConverter
from tm_tutor import TMDataBuilder, TutorDataBuilder

if sys.platform.startswith('win'):
    PathVar = os.environ.get('Path', os.environ.get('PATH', ''))
    Paths = PathVar.split(';')
    PATH = ''
    for candidatePath in Paths:
        if 'devkitARM' in candidatePath:
            PATH = candidatePath
            break
    if PATH == '':
        print('DevKit does not exist in your Path variable.\nChecking default location.')
        PATH = 'C://devkitPro//devkitARM//bin'
        if os.path.isdir(PATH) is False:
            print('...\nDevkit not found.')
            sys.exit(1)
        else:
            print('Devkit found.')

    PREFIX = '/arm-none-eabi-'
    AS = PATH + PREFIX + 'as'
    CC = PATH + PREFIX + 'gcc'
    LD = PATH + PREFIX + 'ld'
    GR = 'deps/grit.exe'
    WAV2AGB = 'deps/wav2agb.exe'
    MID2AGB = 'deps/mid2agb.exe'
    OBJCOPY = PATH + PREFIX + 'objcopy'

else:  # Linux, OSX, etc.
    PREFIX = 'arm-none-eabi-'
    AS = PREFIX + 'as'
    CC = PREFIX + 'gcc'
    LD = PREFIX + 'ld'
    GR = "grit"
    WAV2AGB = 'wav2agb'
    MID2AGB = 'mid2agb'
    OBJCOPY = PREFIX + 'objcopy'

SRC = './src'
GRAPHICS = './graphics'
ASSEMBLY = './assembly'
STRINGS = './strings'
AUDIO = './audio'
BUILD = './build'
IMAGES = './Images'
ASFLAGS = ['-mthumb', '-I', ASSEMBLY]
LDFLAGS = ['BPRJ.ld', '-T', 'linker.ld']
CFLAGS = ['-mthumb', '-mno-thumb-interwork', '-mcpu=arm7tdmi', '-mtune=arm7tdmi',
          '-mno-long-calls', '-march=armv4t', '-Wall', '-Wextra', '-Os', '-fira-loop-pressure', '-fipa-pta']


class Master:
    @staticmethod
    def init():
        Master.printedCompilingImages = False
        Master.printedCompilingAudio = False
        Master.printedCompilingMusic = False

    @staticmethod
    def printCompilingImages():
        if not Master.printedCompilingImages:
            # Used to tell the script whether or not the string 'Compiling Images' has been printed
            Master.printedCompilingImages = True
            print('Compiling Images')

    @staticmethod
    def printCompilingAudio():
        if not Master.printedCompilingAudio:
            # Used to tell the script whether or not the string 'Compiling Audio' has been printed
            Master.printedCompilingAudio = True
            print('Compiling Audio')

    @staticmethod
    def printCompilingMusic():
        if not Master.printedCompilingMusic:
            # Used to tell the script whether or not the string 'Compiling Music' has been printed
            Master.printedCompilingMusic = True
            print('Compiling Music')


def RunCommand(cmd: [str]):
    """Runs the command line command."""
    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        try:
            print(e.output.decode(), file=sys.stderr)
        except:
            print(e)
        sys.exit(1)


def CreateOutputFile(fileName: str, newFileName: str) -> [str, bool]:
    """Helper function to produce object file output."""
    if not os.path.isfile(fileName):
        return [newFileName, False]

    fileExists = os.path.isfile(newFileName)

    # If the object file was created after the file was last modified
    dependencies = [fileName, 'scripts/build.py']
    if fileExists and all(os.path.getmtime(newFileName) > os.path.getmtime(path) for path in dependencies):
        return [newFileName, False]

    return [newFileName, True]


def MakeGeneralOutputFile(fileName: str) -> [str, bool]:
    """Return hash of filename to use as object filename."""
    m = hashlib.md5()
    m.update(fileName.encode())
    newFileName = os.path.join(BUILD, m.hexdigest() + '.o')

    return CreateOutputFile(fileName, newFileName)


def MakeOutputImageFile(assemblyFile: str) -> [str, bool]:
    """Return 'IMG_' + hash of filename to use as object filename."""
    m = hashlib.md5()
    m.update(assemblyFile.encode())
    objectFile = os.path.join(BUILD, 'IMG_' + m.hexdigest() + '.o')

    return CreateOutputFile(assemblyFile, objectFile)


def MakeOutputAudioFile(assemblyFile: str) -> [str, bool]:
    """Return "SND_" + hash of filename to use as object filename."""
    objectFile = os.path.join(BUILD, 'SND_' + assemblyFile.split("gCry")[1].split(".s")[0] + '.o')
    return CreateOutputFile(assemblyFile, objectFile)


def MakeOutputMusicFile(assemblyFile: str) -> [str, bool]:
    """Return "MUS_" + hash of filename to use as object filename."""
    if sys.platform.startswith('win'):  # Windows
        objectFile = os.path.join(BUILD, 'MUS_'
                                  + assemblyFile.split('\\')[len(assemblyFile.split('\\')) - 1].split(".s")[0] + '.o')
    else:  # Linux, OSX, etc.
        objectFile = os.path.join(BUILD, 'MUS_'
                                  + assemblyFile.split('/')[len(assemblyFile.split('/')) - 1].split(".s")[0] + '.o')

    return CreateOutputFile(assemblyFile, objectFile)


def DoMiddleManAssembly(originalFile: str, assemblyFile: str, flagFile: str, flags: [str],
                        cmd: [str], func, printingFunc, isMusic: bool) -> str:
    """Process assembly files generated by things like grit, wav2agb, or mid2agb."""
    objectFile = func(assemblyFile)[0]
    fileExists = os.path.isfile(objectFile)
    flagFileExists = os.path.isfile(flagFile)

    manifestFile = objectFile + '.json'
    dependencies = [originalFile, 'scripts/build.py', cmd[0]]
    if flagFileExists:
        dependencies.append(flagFile)
    manifest = {'flags': flags, 'command': cmd,
                'files': [[path, os.stat(path).st_mtime_ns, os.stat(path).st_size] for path in dependencies if os.path.isfile(path)]}
    try:
        with open(manifestFile) as file:
            previous = json.load(file)
    except (FileNotFoundError, ValueError):
        previous = None
    if fileExists and manifest == previous:
        return objectFile
    printingFunc()
    RunCommand(cmd)

    if isMusic:  # Try to update the voicegroup manually
        counter = 0
        lineToChange = ''
        with open(assemblyFile, 'r') as file:
            for line in file:
                counter += 1
                if '_grp,' in line:
                    lineToChange = line.split('voicegroup')[0]
                    break

        if flags != [] and lineToChange != '' and '-G' in flags:
            ChangeFileLine(assemblyFile, counter, lineToChange + flags[flags.index('-G') + 1] + '\n')

    cmd = [AS] + ASFLAGS + ['-c', assemblyFile, '-o', objectFile]
    RunCommand(cmd)
    os.remove(assemblyFile)
    with open(manifestFile, 'w') as file:
        json.dump(manifest, file)
    return objectFile


def ProcessAssembly(assemblyFile: str) -> str:
    """Assemble."""
    objectFile, regenerateObjectFile = MakeGeneralOutputFile(assemblyFile)
    if regenerateObjectFile is False:
        return objectFile  # No point in recompiling file

    try:
        print('Assembling %s' % assemblyFile)
        cmd = [AS] + ASFLAGS + ['-c', assemblyFile, '-o', objectFile]
        RunCommand(cmd)

    except FileNotFoundError:
        print('Error! The assembler could not be located.\n'
              + 'Are you sure you set up your path to devkitPro/devkitARM/bin correctly?')
        sys.exit(1)

    return objectFile


def ProcessC(cFile: str) -> str:
    """Compile C."""
    objectFile, regenerateObjectFile = MakeGeneralOutputFile(cFile)
    headers = glob(os.path.join('include', '**/*.h'), recursive=True) + glob(os.path.join(SRC, '**/*.h'), recursive=True)
    if os.path.isfile(objectFile) and any(os.path.getmtime(header) >= os.path.getmtime(objectFile) for header in headers):
        regenerateObjectFile = True
    if regenerateObjectFile is False:
        return objectFile  # No point in recompiling file

    try:
        print('Compiling %s' % cFile)
        cmd = [CC] + CFLAGS + ['-c', cFile, '-o', objectFile]
        RunCommand(cmd)

    except FileNotFoundError:
        print('Error! The C compiler could not be located.\n'
              + 'Are you sure you set up your path to devkitPro/devkitARM/bin correctly?')
        sys.exit(1)

    return objectFile


def ProcessString(stringFile: str) -> str:
    """Build and assemble strings."""
    assemblyFile = stringFile.split('.string')[0] + '.s'
    objectFile = MakeGeneralOutputFile(assemblyFile)[0]
    fileExists = os.path.isfile(objectFile)

    dependencies = [stringFile, 'charmap.tbl', 'scripts/string.py', 'scripts/insert.py']
    dependencies += glob('include/**/*.h', recursive=True) + glob(SRC + '/**/*.h', recursive=True)
    if fileExists and all(os.path.getmtime(objectFile) > os.path.getmtime(path) for path in dependencies):
        # If the .o file was created after the string file was last modified
        return objectFile

    print('Building Strings %s' % stringFile)
    StringFileConverter(stringFile)

    cmd = [AS] + ASFLAGS + ['-c', assemblyFile, '-o', objectFile]
    RunCommand(cmd)
    os.remove(assemblyFile)
    return objectFile


def GetFlagsFromFlagFile(filePath: str) -> [str]:
    try:
        with open(filePath, "r") as file:
            line = file.readline()  # Only needs the first line
            flags = line.split()
    except FileNotFoundError:
        print('"{}" could not be found.'.format(filePath))
        sys.exit(1)

    return flags


def ProcessSpriteSet(fileListing: [str], flags: [str], outputFile: str, title: str):
    fileListing = sorted(fileListing)
    if not fileListing:
        raise ValueError("No sprites found for " + title)
    assembledFile = os.path.join(ASSEMBLY, 'generated', outputFile)
    manifestFile = assembledFile + '.json'
    manifest = {'flags': flags, 'files': [[path, os.stat(path).st_mtime_ns, os.stat(path).st_size] for path in fileListing]}
    try:
        with open(manifestFile) as file:
            previous = json.load(file)
    except (FileNotFoundError, ValueError):
        previous = {}
    if os.path.isfile(assembledFile) and manifest == previous:
        return
    print("Processing {}.".format(title))
    with open(assembledFile, 'w') as combinedFile:
        combinedFile.write('@THIS IS A GENERATED FILE! DO NOT MODIFY IT!\n')
        for sprite in fileListing:
            assembled = os.path.splitext(sprite)[0] + '.s'
            if (not os.path.isfile(assembled) or previous.get('flags') != flags
                    or os.path.getmtime(sprite) >= os.path.getmtime(assembled)):
                RunCommand([GR, sprite] + flags + ['-o', assembled])
            with open(assembled) as tempFile:
                combinedFile.write(tempFile.read())
    with open(manifestFile, 'w') as file:
        json.dump(manifest, file)


def ProcessSpriteGraphics():
    frontFlags = GetFlagsFromFlagFile(GRAPHICS + "/frontspriteflags.grit")
    backFlags = GetFlagsFromFlagFile(GRAPHICS + "/backspriteflags.grit")
    iconFlags = GetFlagsFromFlagFile(GRAPHICS + "/iconspriteflags.grit")
    castformFlags = GetFlagsFromFlagFile(GRAPHICS + "/castform/gritflags.txt")

    backsprites = [file for file in glob(GRAPHICS + "/backspr/" + "**/*.png", recursive=True)]
    frontsprites = [file for file in glob(GRAPHICS + "/frontspr/" + "**/*.png", recursive=True)]
    iconsprites = [file for file in glob(GRAPHICS + "/pokeicon/" + "**/*.png", recursive=True)]
    castformsprites = [file for file in glob(GRAPHICS + "/castform/" + "**/*.png", recursive=True)]

    ProcessSpriteSet(frontsprites, frontFlags, 'frontsprites.s', "Front Sprites")
    ProcessSpriteSet(backsprites, backFlags, 'backsprites.s', "Back Sprites")
    ProcessSpriteSet(iconsprites, iconFlags, 'iconsprites.s', "Icon Sprites")
    ProcessSpriteSet(castformsprites, castformFlags, 'castformsprites.s', "Castform Sprites")


def ProcessAudio(audioFile: str) -> str:
    """Compile audio."""
    assemblyFile = audioFile.split('.wav')[0] + '.s'

    flags = []
    flagFile = audioFile.split('.wav')[0] + '_flags.txt'

    try:
        with open(flagFile, 'r') as file:
            line = file.readline()  # Only needs the first line
            flags = line.strip().split()
    except FileNotFoundError:
        pass

    cmd = [WAV2AGB, audioFile, assemblyFile] + flags

    return DoMiddleManAssembly(audioFile, assemblyFile, flagFile, flags, cmd,
                               MakeOutputAudioFile, Master.printCompilingAudio, False)


def ProcessMusic(midiFile: str) -> str:
    """Compile audio."""
    assemblyFile = midiFile.split('.mid')[0] + '.s'

    flags = []
    flagFile = midiFile.split('.mid')[0] + '_flags.txt'

    try:
        with open(flagFile, 'r') as file:
            line = file.readline()  # Only needs the first line
            flags = line.strip().split()
    except FileNotFoundError:
        pass

    cmd = [MID2AGB, midiFile, assemblyFile] + flags

    return DoMiddleManAssembly(midiFile, assemblyFile, flagFile, flags, cmd,
                               MakeOutputMusicFile, Master.printCompilingMusic, True)


def LinkObjects(objects: itertools.chain) -> str:
    """Link objects into one binary."""
    linked = 'build/linked.o'
    cmd = [LD] + LDFLAGS + ['-o', linked] + list(objects)
    RunCommand(cmd)
    return linked


def Objcopy(binary: str):
    """Run the objcopy."""
    cmd = [OBJCOPY, '-O', 'binary', binary, 'build/output.bin']
    RunCommand(cmd)


def RunGlob(globString: str, fn) -> map:
    """Glob recursively and run the processor function on each file in result."""
    if globString == '**/*.png' or globString == '**/*.bmp':  # Search the GRAPHICS location
        directory = GRAPHICS
    elif globString == '**/*.s':
        directory = ASSEMBLY
    elif globString == '**/*.string':
        directory = STRINGS
    elif globString == '**/*.wav' or globString == '**/*.mid':
        directory = AUDIO
    else:
        directory = SRC

    if sys.version_info > (3, 4):
        try:
            files = sorted(glob(os.path.join(directory, globString), recursive=True))
            return map(fn, files)

        except TypeError:
            print('Error compiling. Please make sure Python has been updated to the latest version.')
            sys.exit(1)
    else:
        files = Path(directory).glob(globString)
        return map(fn, map(str, files))


def main():
    Master.init()
    startTime = datetime.now()
    globs = {
        '**/*.s': ProcessAssembly,
        '**/*.c': ProcessC,
        '**/*.string': ProcessString,
        # '**/*.png': ProcessImage,
        # '**/*.bmp': ProcessImage,
        '**/*.wav': ProcessAudio,
        '**/*.mid': ProcessMusic,
    }

    # Create output directory
    try:
        os.makedirs(BUILD)
    except FileExistsError:
        pass

    try:
        try:
            os.makedirs(ASSEMBLY + "/generated")
        except FileExistsError:
            pass

        ProcessSpriteGraphics()
        TMDataBuilder()
        TutorDataBuilder()

        # Gather source files and process them
        objects = itertools.starmap(RunGlob, globs.items())

        # Link and extract raw binary
        linked = LinkObjects(itertools.chain.from_iterable(objects))
        Objcopy(linked)

    except Exception as e:
        print("There was an error compiling the engine: {}".format(e))
        sys.exit(1)

    # Build special_inserts.asm
    if os.path.isfile('special_inserts.asm'):
        if not os.path.isfile('build/special_inserts.bin') \
                or os.path.getmtime('build/special_inserts.bin') < max(os.path.getmtime('special_inserts.asm'), os.path.getmtime(linked)):
            print('Assembling special_inserts.asm')
            cmd = [AS] + ASFLAGS + ['-c', 'special_inserts.asm', '-o', 'build/special_inserts.o']
            RunCommand(cmd)

            cmd = [LD, '--just-symbols=' + linked, '-Ttext=0', '-e', '0', '-o', 'build/special_inserts.elf', 'build/special_inserts.o']
            RunCommand(cmd)

            cmd = [OBJCOPY, '-O', 'binary', 'build/special_inserts.elf', 'build/special_inserts.bin']
            RunCommand(cmd)

    print('Built in ' + str(datetime.now() - startTime) + '.')


if __name__ == '__main__':
    main()
