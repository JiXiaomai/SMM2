# expressions for noexs have been included, too, in case you want to use them with it instead.

def expressions(binary=None):
    if binary == None:
        return None
    else:
        expressions = {
            "timer": [[[[[binary+0x2BEBA08], 0x18], 0x8], 0x10], 0x14], # [[[[main+2BEBA08] + 18] + 08] + 10] + 14
            "overworld_enemy_count": [[[[[binary+0x2A5A918], 0x18], 0x10], 0x8], 0xBFC], # [[[[main+2A5A918] + 18] + 10] + 08] + BFC
            "subworld_enemy_count": [[binary+0x2B2A610], 0x188C], # [main+2B2A610] + 188C
            "overworld_item_count": [[[[[binary+0x2A5A918], 0x18], 0x10], 0x8], 0xC00], # [[[[main+2A5A918] + 18] + 10] + 08] + C00
            "subworld_item_count": [[binary+0x2B2A610], 0x1890], # [main+2B2A610] + 188C
            "overworld_block_count": [[[[[binary+0x2A5A918], 0x18], 0x10], 0x8], 0xC04], # [[[[main+2A5A918] + 18] + 10] + 08] + C04
            "subworld_block_count": [[binary+0x2B2A610], 0x1894], # [main+2B2A610] + 188C
            "overworld_tile_count": [[[[[binary+0x2A5A918], 0x18], 0x10], 0x8], 0xC08], # [[[[main+2A5A918] + 18] + 10] + 08] + C08
            "subworld_tile_count": [[binary+0x2B2A610], 0x1898], # [main+2B2A610] + 188C
            "newest_overworld_actor": [[[[[binary+0x2B2A610], 0x10], 0x8], 0x10], -0x28], # [[[[main+2B2A610] + 10] + 08] + 10] - 28
            "newest_subworld_actor": [[binary+0x2B2A610], 0xC90] # [main+2B2A610] + C90
        }
        return expressions
