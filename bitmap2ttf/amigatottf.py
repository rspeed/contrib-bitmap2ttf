#!/usr/bin/env python

# * Copyright 2013 Alistair Buxton <a.j.buxton@gmail.com>
# *
# * License: This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License as published
# * by the Free Software Foundation; either version 3 of the License, or (at
# * your option) any later version. This program is distributed in the hope
# * that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# * warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.

from struct import unpack

import click

from PIL import Image


class AmigaFont(object):

    def __init__(self, file):

        diskfont = file.read()

        # get textfont struct (32 bytes)
        textfont = diskfont[110:142]

        (self.ysize, self.style, self.flags, self.xsize,
         self.baseline, self.boldsmear, self.lochar, self.hichar,
         pchardata, self.modulo, pcharloc, pcharspace,
         pcharkern) = unpack(">HBBHHHxxBBLHLLL", textfont)

        self.numchars = 1 + self.hichar - self.lochar
        self.chardata = diskfont[32 + pchardata:32 + pchardata + (self.modulo * self.ysize)]
        self.charloc = diskfont[32 + pcharloc:32 + pcharloc + (self.numchars * 4)]
        self.charspace = diskfont[32 + pcharspace:32 + pcharspace + (self.numchars * 4)]
        self.charkern = diskfont[32 + pcharkern:32 + pcharkern + (self.numchars * 4)]

    def rasterize(self, byte, one=chr(255), zero=chr(0)):
        output = ""
        for i in range(8):
            if byte & (1 << i):
                output = one + output
            else:
                output = zero + output
        return output

    def bitmap(self, byte):
        c = byte - (self.lochar)
        d = self.charloc[c * 4:(c + 1) * 4]
        (offs, width) = unpack(">HH", d)
        data = b"".join(
            [self.rasterize(ord(self.chardata[(offs >> 3) + (n * self.modulo)])) for n in range(self.ysize)])
        return Image.fromstring("L", (width, self.ysize), data)

    def glyphs(self):
        g = {}
        for i in range(self.lochar, self.hichar + 1):
            g[i] = self.bitmap(i)
        return g


@click.command()
@click.argument('amigafont', type=click.File('rb'), required=True)
@click.argument('ttf', type=click.Path(exists=False), required=True)
def amigatottf(amigafont, ttf):
    from .convert import convert
    f = AmigaFont(amigafont)
    convert(f.glyphs(), ttf)
