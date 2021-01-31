def get_expressions(*args):
    return {
        # 0: TIMER: [[[[main+2BECB08]+18]+08]+10]+14
        0: [[[[[args[0]+0x2BECB08], 0x18], 0x08], 0x10], 0x14],

        # 1: OVERWORLD ENEMY COUNT: [[[main+2B2B710]+18]]+C0C
        1: [[[[args[0]+0x2B2B710], 0x18], 0x0], 0xC0C],

        # 2: SUBWORLD ENEMY COUNT: [[[[[main+2B2B710]+18]]+10]+08]+186C
        2: [[[[[[args[0]+0x2B2B710], 0x18], 0x0], 0x10], 0x08], 0x186C],

        # 3: OVERWORLD ITEM COUNT: [[[main+2B2B710]+18]]+C10
        3: [[[[args[0]+0x2B2B710], 0x18], 0x0], 0xC10],

        # 4: SUBWORLD ITEM COUNT: [[[[[main+2B2B710]+18]]+10]+08]+1870
        4: [[[[[[args[0]+0x2B2B710], 0x18], 0x0], 0x10], 0x08], 0x1870],

        # 5: OVERWORLD BLOCK COUNT: [[[main+2B2B710]+18]]+C14
        5: [[[[args[0]+0x2B2B710], 0x18], 0x0], 0xC14],

        # 6: SUBWORLD BLOCK COUNT: [[[[[main+2B2B710]+18]]+10]+08]+1874
        6: [[[[[[args[0]+0x2B2B710], 0x18], 0x0], 0x10], 0x08], 0x1874],

        # 7: OVERWORLD TILE COUNT: [[[main+2B2B710]+18]]+C18
        7: [[[[args[0]+0x2B2B710], 0x18], 0x0], 0xC18],

        # 8: SUBWORLD TILE COUNT: [[[[[main+2B2B710]+18]]+10]+08]+1878
        8: [[[[[[args[0]+0x2B2B710], 0x18], 0x0], 0x10], 0x08], 0x1878],

        # 9: NEWEST ACTOR PLACED IN THE OVERWORLD: [[[[[main+2A5BA18]+10]+08]+08]+10]-28
        9: [[[[[[args[0]+0x2A5BA18], 0x10], 0x08], 0x08], 0x10], -0x28],

        # 10: NEWEST ACTOR PLACED IN THE SUBWORLD: [[[[[main+2A5BA18]+18]+18]]+C70]-38
        10: [[[[[[args[0]+0x2A5BA18], 0x18], 0x18], 0x0], 0xC70], -0x38],

        # 11: X POSITION OF THE PLAYER IN EDIT MODE: [[[[main+2B23730]+10]]]+158
        11: [[[[[args[0]+0x2B23730], 0x10], 0x0], 0x0], 0x158],

        # 12: Y POSITION OF THE PLAYER IN EDIT MODE: [[[[main+2B23730]+10]]]+15C
        12: [[[[[args[0]+0x2B23730], 0x10], 0x0], 0x0], 0x15C],

        # 13: X POSITION OF THE PLAYER IN PLAY MODE: [[[[main+2C19288]+1D0]+84]+90]+188
        13: [[[[[args[0]+0x2C19288], 0x1D0], 0x84], 0x90], 0x188],

        # 14: Y POSITION OF THE PLAYER IN PLAY MODE: [[[[main+2C19288]+1D0]+84]+90]+18C
        14: [[[[[args[0]+0x2C19288], 0x1D0], 0x84], 0x90], 0x18C]
    }
