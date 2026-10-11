.thumb
.align 2

.pool
@0x800ECF2 with r4
LoadSpecialPokePicHook:
	mov r7, r8
	push {r7}
	ldr r4, [sp, #0x18]
	sub sp, #0x4
	str r4, [sp, #0x0]
	bl LoadSpecialPokePic
	add sp, #0x4
	pop {r7}
	mov r8, r7
	pop {r4-r7}
	pop {r0}
	bx r0

.pool
@0x8080344E4 with r0
BattleLoadPlayerMonSpriteGfxHook:
	mov r0, r5
	mov r1, r4
	bl TryGetFemaleGenderedSpecies
	mov r5, r0
@Prep return
	mov r0, r6
	mov r1, #0x1 @;Trainer Id
	ldr r2, =GetMonData
	bl bxr2
	ldr r1, =0x08033C60 | 1
	bx r1

.pool
@0x803436C with r0
BattleLoadOpponentMonSpriteGfxHook:
	mov r0, r5
	mov r1, r6
	bl TryGetFemaleGenderedSpecies
	mov r5, r0
@Prep return
	mov r0, r4
	mov r1, #0x1 @;Trainer Id
	ldr r2, =GetMonData
	bl bxr2
	ldr r1, =0x08033AE8 | 1
bxr1:
	bx r1

/*
.pool
@0x80747B4 with r0
GetBattlerSpriteFinalYHook:
	lsl r2, r2, #0x18
	lsr r7, r2, #0x18
	mov r0, r6
	lsr r1, r1, #0x10
	bl TryGetFemaleGenderedSpeciesFromBank

	mov r0, r6
	ldr r1, =0x80747BC | 1
	bx r1
*/

.pool
@0x8096E38 with r2
GenderedMonIconHook:
	lsr r7, r3, #0x10
	lsl r0, #0x18
	lsr r0, #0x18
	mov r9, r0

	mov r0, r4
	ldr r1, [sp, #0x50] @Personality
	bl HackMoemon_IconHookSpecies @[hack] Moemon icons (patches/0221)
	mov r4, r0

	ldr r1, [sp, #0x50] @Personality
	ldr r0, =0x809686C | 1
	bx r0

.pool
@0x8073EE4 with r1
@[hack] Moemon battle sprite height (patches/0222)
HackMoemonYDeltaHook:
	mov r1, r5 @battler
	mov r2, r7 @species
	bl HackMoemon_BattlerYDelta
	pop {r4-r7}
	pop {r1}
	bx r1

.pool
@0x8139DDC with r1
SummaryScreenIconPalHook:
	mov r4, r0
	mov r1, r0
	mov r0, r5
	bl TryGetFemaleGenderedSpecies
	mov r5, r0
	ldr r1, =SafeLoadMonIconPalette
	bl bxr1
	ldr r0, =0x813A5BC | 1
	bx r0

.pool
@0x808398C with r1
CreateMonSprite_PicBoxHook:
	mov r4, r0
	mov r1, #0x0
	mov r2, #0x80
	lsl r2, #0x8 @0x8000
	bl GetMonSpritePalStructFromOtIdPersonality
	mov r1, r0
	mov r0, r4
	mov r4, r1 @Backup palette struct
	ldrh r1, [r4, #0x4] @Tag
	mov r3, #0x80
	lsl r3, #0x8 @0x8000
	ldr r2, =0x8083580 | 1
bxr2:
	bx r2

.pool
@0x80CDF10 with r1
EvolutionSceneHook1:
	mov r10, r0
	mov r0, r5 @currSpecies
	mov r1, r10 @personality
	bl HackMoemon_EvoFrontSheet @[hack] patches/0218 Moémon の絵（無ければ &gMonFrontPicTable[TryGetFemaleGenderedSpecies]）
	ldr r2, =0x80CF070 | 1
	bx r2

.pool
@0x80CDF88 with r2
EvolutionSceneHook2:
	strb r0, [r1]
	mov r0, r9 @speciesToEvolve
	mov r1, r10 @personality
	bl HackMoemon_EvoFrontSheet @[hack] patches/0218
	ldr r2, =0x80CF0EA | 1
	bx r2

.pool
@0x80CE1C0 with r2
EvolutionSceneHook3:
	strb r0, [r1]
	mov r0, r5 @postEvoSpecies
	mov r1, r6 @personality
	bl HackMoemon_EvoFrontSheet @[hack] patches/0218
	ldr r2, =0x80CF320 | 1
	bx r2

.pool
@[hack] patches/0303 通信進化も Moémon の絵（ユーザー「moemon を通信進化させると進化後のグラフィックがおかしい」）。
@0x80CF580 with r1: CB2_TradeEvolutionSceneLoadGraphics（r6 = 進化後の種族・r4 = 性格値）。上書き = lsl/ldr 表/add/ldr gMonSpritesGfxPtr
TradeEvolutionLoadGraphicsHook:
	mov r0, r6
	mov r1, r4
	bl HackMoemon_EvoFrontSheet
	ldr r1, =0x02023F7C @gMonSpritesGfxPtr
	ldr r2, =0x80CF588 | 1
	bx r2

.pool
@0x80CF714 with r1: TradeEvolutionScene（r5 = 進化後の種族・r7 = 性格値）。上書き = lsl/ldr 表/add/ldr gMonSpritesGfxPtr
TradeEvolutionSceneHook:
	mov r0, r5
	mov r1, r7
	bl HackMoemon_EvoFrontSheet
	ldr r1, =0x02023F7C @gMonSpritesGfxPtr
	ldr r2, =0x80CF71C | 1
	bx r2

.pool
@0x8103B0C with r1
NationalPokeDexPrintFix:
	mov r1, #0x0
	ldr r2, =0x83DD4FF
	mov r3, #0x0
	ldr r6, =0x8105584 | 1
	bl bxr6
	ldr r1, =0x8103B16 | 1
	bx r1

bxr6:
	bx r6
