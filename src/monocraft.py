# Monocraft, a monospaced font for developers who like Minecraft a bit too much.
# Copyright (C) 2022-2023 Idrees Hassan
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import fontforge
import json
import math
from generate_diacritics import generateDiacritics
from generate_examples import generateExamples
from polygonizer import PixelImage, generatePolygons
from generate_continuous_ligatures import generate_continuous_ligatures

PIXEL_SIZE = 120

characters = json.load(open("./characters.json"))
diacritics = json.load(open("./diacritics.json"))
ligatures = json.load(open("./ligatures.json"))
continuous_ligatures = json.load(open("./continuous_ligatures.json"))

characters = generateDiacritics(characters, diacritics)
charactersByCodepoint = {}

spacersByCodepoint = set()


def generateFont():
    fontList = [fontforge.font() for _ in range(3)]
    for font in fontList:
        font.fontname = "Monocraft"
        font.familyname = "Monocraft"
        font.fullname = "Monocraft"
        font.copyright = "Idrees Hassan, https://github.com/IdreesInc/Monocraft"
        font.encoding = "UnicodeFull"
        font.version = "3.0"
        font.weight = "Regular"
        font.ascent = PIXEL_SIZE * 8
        font.descent = PIXEL_SIZE
        font.em = PIXEL_SIZE * 9
        font.upos = -PIXEL_SIZE  # Underline position
        font.addLookup("ligatures", "gsub_ligature", (),
                       (("liga", (("dflt", ("dflt")), ("latn", ("dflt")))), ))
        font.addLookupSubtable("ligatures", "ligatures-subtable")

    font = fontList[0]
    font.os2_stylemap = font.macstyle = 0
    font = fontList[1]
    font.fontname = "Monocraft-Bold"
    font.fullname = "Monocraft Bold"
    font.weight = "Bold"
    font.os2_stylemap = font.macstyle = 1
    font = fontList[2]
    font.fontname = "Monocraft-Italic"
    font.fullname = "Monocraft Italic"
    font.os2_stylemap = font.macstyle = 2
    font.italicangle = -15

    for character in characters:
        charactersByCodepoint[character["codepoint"]] = character
        image, kw = generateImage(character)
        createChar(fontList, character["codepoint"], character["name"], image,
                   **kw)
    print(f"Generated {len(characters)} characters")

    outputDir = "../dist/"
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    fontList[0].generate(outputDir + "Monocraft-no-ligatures.ttf")
    fontList[1].generate(outputDir + "Monocraft-bold-no-ligatures.ttf")
    fontList[2].generate(outputDir + "Monocraft-italic-no-ligatures.ttf")

    for ligature in ligatures:
        image, kw = generateImage(ligature)
        name = ligature["name"].translate(str.maketrans(" ", "_"))

        createChar(
            fontList,
            -1,
            name,
            image,
            width=6 * PIXEL_SIZE * len(ligature["sequence"]),
            glyphclass="baseligature",
            **kw,
        )

        for font in fontList:
            lig = font[name]
            lig.addPosSub(
                "ligatures-subtable",
                tuple(charactersByCodepoint[cp]["name"]
                      for cp in ligature["sequence"]),
            )
    print(f"Generated {len(ligatures)} ligatures")

    temp_class = tuple(charactersByCodepoint[i]["name"]
                       for i in range(33, 127))

    temp = False
    head_rules = []
    body_rules = []
    tail_rules = []
    for ligature in continuous_ligatures:
        name = ligature["name"]

        head_table = f"head-table-{name}"
        for font in fontList:
            font.addLookup(head_table, "gsub_single", (), ())
            font.addLookupSubtable(head_table, f"{head_table}-subtable")
        heads = []
        for head in ligature["heads"]:
            image = imageFromArray(head["pixels"])
            cname = charactersByCodepoint[head['char']]['name']
            name_ = f"{cname}_{name}_head"
            createChar(fontList, -1, name_, image)
            for font in fontList:
                font[cname].addPosSub(f"{head_table}-subtable", name_)
            heads.append((cname, name_))

            if not temp:
                chr = fontList[0][cname]
                print(chr.manualHints, chr.dhints, chr.hhints, chr.vhints)
                temp = True

        body_table = f"body-table-{name}"
        for font in fontList:
            font.addLookup(body_table, "gsub_single", (), ())
            font.addLookupSubtable(body_table, f"{body_table}-subtable")
        bodies = []
        for body in ligature["bodies"]:
            image = imageFromArray(body["pixels"])
            cname = charactersByCodepoint[body['char']]['name']
            name_ = f"{cname}_{name}_body"
            createChar(fontList, -1, name_, image)
            for font in fontList:
                font[cname].addPosSub(f"{body_table}-subtable", name_)
            bodies.append((cname, name_))

        tail_table = f"tail-table-{name}"
        for font in fontList:
            font.addLookup(tail_table, "gsub_single", (), ())
            font.addLookupSubtable(tail_table, f"{tail_table}-subtable")
        tails = []
        for tail in ligature["tails"]:
            image = imageFromArray(tail["pixels"])
            cname = charactersByCodepoint[tail['char']]['name']
            name_ = f"{cname}_{name}_tail"
            createChar(fontList, -1, name_, image)
            for font in fontList:
                font[cname].addPosSub(f"{tail_table}-subtable", name_)
            tails.append((cname, name_))

        head_cov = "[" + " ".join(i[0] for i in heads) + "]"
        body_cov = "[" + " ".join(i[0] for i in bodies) + "]"
        tail_cov = "[" + " ".join(i[0] for i in tails) + "]"
        maybe_tail_cov = "[" + " ".join(
            frozenset(i[0] for a in [bodies, tails] for i in a)) + "]"
        head_process_cov = "[" + " ".join(i[1] for i in heads) + "]"
        body_process_cov = "[" + " ".join(i[1] for i in bodies) + "]"

        head_rules.append(
            f"| {head_cov} @<{head_table}> {body_cov} @<{body_table}> {body_cov} @<{body_table}> | {maybe_tail_cov}"
        )
        body_rules.append(
            f"{body_process_cov} | {body_cov} @<{body_table}> | {maybe_tail_cov}"
        )
        tail_rules.append(f"{body_process_cov} | {tail_cov} @<{tail_table}> |")

    for font in fontList:
        font.addLookup(
            "cont-liga",
            "gsub_contextchain",
            (),
            (("calt", (("dflt", ("dflt")), ("latn", ("dflt")))), ),
        )
    for n, i in enumerate(i for a in [head_rules, tail_rules, body_rules]
                          for i in reversed(a)):
        for font in fontList:
            font.addContextualSubtable(
                "cont-liga",
                f"cont-{n}-subtable",
                "coverage",
                i,
            )

    print(f"Generated {len(continuous_ligatures)} continuous ligatures chain")

    fontList[0].generate(outputDir + "Monocraft.ttf")
    fontList[0].generate(outputDir + "Monocraft.otf")
    fontList[1].generate(outputDir + "Monocraft-bold.ttf")
    fontList[1].generate(outputDir + "Monocraft-bold.otf")
    fontList[2].generate(outputDir + "Monocraft-italic.ttf")
    fontList[2].generate(outputDir + "Monocraft-italic.otf")


def generateImage(character):
    image = PixelImage()
    kw = {}
    if "pixels" in character:
        arr = character["pixels"]
        leftMargin = character["leftMargin"] if "leftMargin" in character else 0
        x = math.floor(leftMargin)
        kw['dx'] = leftMargin - x
        descent = -character["descent"] if "descent" in character else 0
        y = math.floor(descent)
        kw['dy'] = descent - y
        image = image | imageFromArray(arr, x, y)
    if "reference" in character:
        other = generateImage(charactersByCodepoint[character["reference"]])
        kw.update(other[1])
        image = image | other[0]
    if "diacritic" in character:
        diacritic = diacritics[character["diacritic"]]
        arr = diacritic["pixels"]
        x = image.x
        y = findHighestY(image) + 1
        if "diacriticSpace" in character:
            y += int(character["diacriticSpace"])
        image = image | imageFromArray(arr, x, y)
    return (image, kw)


def findHighestY(image):
    for y in range(image.y_end - 1, image.y, -1):
        for x in range(image.x, image.x_end):
            if image[x, y]:
                return y
    return image.y


def imageFromArray(arr, x=0, y=0):
    return PixelImage(
        x=x,
        y=y,
        width=len(arr[0]),
        height=len(arr),
        data=bytes(x for a in reversed(arr) for x in a),
    )


def drawPolygon(poly, pen):
    for polygon in poly:
        start = True
        for x, y in polygon:
            x = int(math.floor(x * PIXEL_SIZE))
            y = int(math.floor(y * PIXEL_SIZE))
            if start:
                pen.moveTo(x, y)
                start = False
            else:
                pen.lineTo(x, y)
        pen.closePath()


BOLD_DIST = 0.2
ITALIC_RATIO = math.tan(math.radians(15))


def createChar(fontList,
               code,
               name,
               image=None,
               *,
               width=None,
               dx=0,
               dy=0,
               glyphclass=None):
    if image is not None:
        poly = [[(x + dx, y + dy) for x, y in p]
                for p in generatePolygons(image)]
    for font in fontList:
        char = font.createChar(code, name)
        if glyphclass is not None:
            char.glyphclass = glyphclass
        if image is None:
            char.width = width if width is not None else PIXEL_SIZE * 6
            continue

        p = poly
        if font.macstyle & 1 != 0:

            def f(p):
                l = len(p)
                for i, (x, y) in enumerate(p):
                    x_, y_ = x, y
                    px, py = p[i - 1]
                    if px < x:
                        y_ += BOLD_DIST
                    elif px > x:
                        y_ -= BOLD_DIST
                    elif py < y:
                        x_ -= BOLD_DIST
                    else:
                        x_ += BOLD_DIST
                    px, py = p[(i + 1) % l]
                    if px < x:
                        y_ -= BOLD_DIST
                    elif px > x:
                        y_ += BOLD_DIST
                    elif py < y:
                        x_ += BOLD_DIST
                    else:
                        x_ -= BOLD_DIST
                    yield (x_, y_)

            p = (f(p) for p in generatePolygons(image, join_polygons=False))
        elif font.macstyle & 2 != 0:
            p = (((x + y * ITALIC_RATIO, y) for x, y in p) for p in poly)

        drawPolygon(p, char.glyphPen())
        char.width = width if width is not None else PIXEL_SIZE * 6


generateFont()
generateExamples(characters, ligatures, continuous_ligatures,
                 charactersByCodepoint)
