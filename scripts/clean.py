#!/usr/bin/env python3
"""Remove generated build files without changing the working directory."""

import hashlib
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'build'


def PutFileNameInRightFormat(filename):
    path = Path(filename.replace('\\', '/'))
    if path.is_absolute() or '..' in path.parts:
        raise ValueError("Expected a project-relative source path")
    parts = path.parts
    if not parts or parts[0].lower() not in {'src', 'assembly', 'graphics', 'strings', 'audio'}:
        raise ValueError("Unknown source directory")
    return './' + os.path.join(parts[0].lower(), *parts[1:])


def RemoveFile(path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def RemoveGeneratedDirectory(path):
    resolved = path.resolve()
    if ROOT not in resolved.parents:
        raise ValueError("Generated directory outside project")
    if path.exists():
        shutil.rmtree(path)


def TryRemoveGeneratedRepoints():
    RemoveFile(ROOT / 'generatedrepoints')


def TryRemoveGeneratedImageAssembly():
    RemoveGeneratedDirectory(ROOT / 'assembly' / 'generated')
    for path in (ROOT / 'graphics').rglob('*'):
        if path.is_file() and path.suffix in {'.h', '.s'}:
            RemoveFile(path)


def CleanFile(filename):
    formatted = PutFileNameInRightFormat(filename)
    source = Path(formatted)
    assembly = source.with_suffix('.s')
    assemblyName = os.path.splitext(formatted)[0] + '.s'
    candidates = [BUILD / (hashlib.md5(formatted.encode()).hexdigest() + '.o')]
    if source.suffix == '.string':
        candidates.append(BUILD / (hashlib.md5(assemblyName.encode()).hexdigest() + '.o'))
    elif source.suffix == '.png':
        RemoveFile(ROOT / assembly)
        for path in (ROOT / 'assembly' / 'generated').glob('*sprites.s*'):
            RemoveFile(path)
    elif source.suffix == '.wav':
        candidates.append(BUILD / ('SND_' + source.stem.split('gCry', 1)[-1] + '.o'))
    elif source.suffix == '.mid':
        candidates.append(BUILD / ('MUS_' + source.stem + '.o'))
    removed = False
    for path in candidates:
        if path.is_file():
            RemoveFile(path)
            removed = True
    if source.suffix != '.png' and not removed:
        raise FileNotFoundError("No cached build for " + filename)


def main(args=None):
    args = sys.argv[1:] if args is None else args
    mode = args[0].upper() if args else 'DEFAULT'
    if mode not in {'DEFAULT', 'ALL', 'BUILD', 'GRAPHICS', 'AUDIO', 'FILE'}:
        raise ValueError("Expected ALL, BUILD, GRAPHICS, AUDIO or FILE <path>")
    if mode == 'FILE':
        if len(args) != 2:
            raise ValueError("Expected FILE <path>")
        CleanFile(args[1])
        print('Build for "' + args[1] + '" removed successfully!')
        return
    if len(args) > 1:
        raise ValueError("Unexpected cleaning arguments")
    RemoveFile(ROOT / 'test.gba')
    RemoveFile(ROOT / 'offsets.ini')
    if mode in {'DEFAULT', 'ALL'}:
        TryRemoveGeneratedRepoints()
    if mode == 'ALL':
        RemoveGeneratedDirectory(BUILD)
        TryRemoveGeneratedImageAssembly()
    else:
        if mode == 'GRAPHICS':
            TryRemoveGeneratedImageAssembly()
        for path in BUILD.rglob('*'):
            if not path.is_file():
                continue
            image = path.name.startswith('IMG_')
            audio = path.name.startswith(('SND_', 'MUS_'))
            if ((mode == 'GRAPHICS' and image) or (mode == 'AUDIO' and audio)
                    or (mode in {'DEFAULT', 'BUILD'} and not image and not audio)):
                RemoveFile(path)
    print("Directory cleaned!")


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        sys.exit(1)
