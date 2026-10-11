#include "defines.h"

/*
 * SuperCard SD の試しの絵（2026-10-07）: DPE の LoadSpecialPokePic から CFRU の src/hack_scsd.c の HackSdPic_LoadPic を呼ぶつなぎ。
 * DPE は CFRU のあとに別に組み立てるので、CFRU の関数の番地は直に書けない。gHackSdBridge（assembly/hack_sd_bridge.s・ROM）に
 * tools/build/build_rom.py が DPE を組み立てたあと番地を書く。0 なら何もしない。
 */

extern const u32 gHackSdBridge[1];

bool8 HackSdBridge_LoadPic(void *dest, u16 species, u32 personality, bool8 isFrontPic)
{
	bool8 (*fn)(void *, u16, u32, bool8) = (void *) gHackSdBridge[0];

	if (fn == 0)
		return FALSE;
	return fn(dest, species, personality, isFrontPic);
}
