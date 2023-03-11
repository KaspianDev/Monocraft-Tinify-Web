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

PIXEL_SIZE = 120

characters = json.load(open("./characters.json"))
diacritics = json.load(open("./diacritics.json"))
ligatures = json.load(open("./ligatures.json"))
continuous_ligatures = json.load(open("./continuos_ligatures.json"))

characters = generateDiacritics(characters, diacritics)
charactersByCodepoint = {}

spacersByCodepoint = {}


def generateFont():
    monocraft = fontforge.font()
    monocraft.fontname = "Monocraft"
    monocraft.familyname = "Monocraft"
    monocraft.fullname = "Monocraft"
    monocraft.copyright = "Idrees Hassan, https://github.com/IdreesInc/Monocraft"
    monocraft.encoding = "UnicodeFull"
    monocraft.version = "2.5"
    monocraft.weight = "Regular"
    monocraft.ascent = PIXEL_SIZE * 8
    monocraft.descent = PIXEL_SIZE
    monocraft.em = PIXEL_SIZE * 9
    monocraft.upos = -PIXEL_SIZE  # Underline position
    monocraft.addLookup("multi", "gsub_multiple", (),
                        (("ccmp", (("dflt", ("dflt")), ("latn", ("dflt")))), ))
    monocraft.addLookupSubtable("multi", "multi-subtable")
    monocraft.addLookup("ligatures", "gsub_ligature", (),
                        (("liga", (("dflt", ("dflt")), ("latn", ("dflt")))), ))
    monocraft.addLookupSubtable("ligatures", "ligatures-subtable")

    for character in characters:
        charactersByCodepoint[character["codepoint"]] = character
        monocraft.createChar(character["codepoint"], character["name"])
        pen = monocraft[character["name"]].glyphPen()
        top = 0
        drawn = character

        image, kw = generateImage(character)
        drawImage(image, pen, **kw)
        monocraft[character["name"]].width = PIXEL_SIZE * 6
    print(f"Generated {len(characters)} characters")

    outputDir = "../dist/"
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    monocraft.generate(outputDir + "Monocraft-no-ligatures.ttf")

    for ligature in ligatures:
        image, kw = generateImage(ligature)
        name = ligature["name"].translate(str.maketrans(" ", "_"))

        lig = monocraft.createChar(-1, f'{name}_liga')
        pen = lig.glyphPen()
        image_ = PixelImage(
            x=6 - 6 * len(ligature["sequence"]),
            y=image.y,
            width=image.width,
            height=image.height,
            data=image.data,
        )
        drawImage(image_, pen, **kw)
        lig.width = PIXEL_SIZE * 6

        for cp in ligature["sequence"][:-1]:
            if cp not in spacersByCodepoint:
                spacer = monocraft.createChar(
                    -1, charactersByCodepoint[cp]["name"] + "_spacer")
                spacer.width = PIXEL_SIZE * 6
                spacersByCodepoint[cp] = spacer

        lig = monocraft.createChar(-1, name)
        lig.width = PIXEL_SIZE * 6
        lig.addPosSub(
            "ligatures-subtable",
            tuple(charactersByCodepoint[cp]["name"]
                  for cp in ligature["sequence"]))
        lig.addPosSub("multi-subtable",
                      (*(charactersByCodepoint[cp]["name"] + "_spacer"
                         for cp in ligature["sequence"][:-1]), f'{name}_liga'))
    print(f"Generated {len(ligatures)} ligatures")

    for ligature in reversed(continuous_ligatures):
        name = ligature["name"]

        head_table = f"head-table-{name}"
        monocraft.addLookup(head_table, "gsub_single", (), ())
        monocraft.addLookupSubtable(head_table, f"{head_table}-subtable")
        heads = []
        for head in ligature["heads"]:
            image = imageFromArray(head["pixels"])
            cname = charactersByCodepoint[head['char']]['name']
            name_ = f"{cname}_{name}_head"
            char = monocraft.createChar(-1, name_)
            drawImage(image, char.glyphPen())
            char.width = PIXEL_SIZE * 6
            monocraft[cname].addPosSub(f"{head_table}-subtable", name_)
            heads.append((cname, name_))

        body_table = f"body-table-{name}"
        monocraft.addLookup(body_table, "gsub_single", (), ())
        monocraft.addLookupSubtable(body_table, f"{body_table}-subtable")
        bodies = []
        for body in ligature["bodies"]:
            image = imageFromArray(body["pixels"])
            cname = charactersByCodepoint[body['char']]['name']
            name_ = f"{cname}_{name}_body"
            char = monocraft.createChar(-1, name_)
            drawImage(image, char.glyphPen())
            char.width = PIXEL_SIZE * 6
            monocraft[cname].addPosSub(f"{body_table}-subtable", name_)
            bodies.append((cname, name_))

        tail_table = f"tail-table-{name}"
        monocraft.addLookup(tail_table, "gsub_single", (), ())
        monocraft.addLookupSubtable(tail_table, f"{tail_table}-subtable")
        tails = []
        for tail in ligature["tails"]:
            image = imageFromArray(tail["pixels"])
            cname = charactersByCodepoint[tail['char']]['name']
            name_ = f"{cname}_{name}_tail"
            char = monocraft.createChar(-1, name_)
            drawImage(image, char.glyphPen())
            char.width = PIXEL_SIZE * 6
            monocraft[cname].addPosSub(f"{tail_table}-subtable", name_)
            tails.append((cname, name_))

        head_cov = "[" + " ".join(i[0] for i in heads) + "]"
        body_cov = "[" + " ".join(i[0] for i in bodies) + "]"
        tail_cov = "[" + " ".join(i[0] for i in tails) + "]"
        maybe_tail_cov = "[" + " ".join(
            frozenset(i[0] for a in [bodies, tails] for i in a)) + "]"
        head_process_cov = "[" + " ".join(i[1] for i in heads) + "]"
        nontail_process_cov = "[" + " ".join(
            frozenset(i[1] for a in [heads, bodies] for i in a)) + "]"

        monocraft.addLookup(
            f"cont-{name}",
            "gsub_contextchain",
            (),
            (("calt", (("dflt", ("dflt")), ("latn", ("dflt")))), ),
        )
        monocraft.addContextualSubtable(
            f"cont-{name}",
            f"cont-{name}-tail-subtable",
            "coverage",
            f"{nontail_process_cov} | {tail_cov} @<{tail_table}> |",
        )
        monocraft.addContextualSubtable(
            f"cont-{name}",
            f"cont-{name}-head-subtable",
            "coverage",
            f"| {head_cov} @<{head_table}> | {body_cov} {body_cov} {maybe_tail_cov}",
        )
        monocraft.addContextualSubtable(
            f"cont-{name}",
            f"cont-{name}-body-subtable",
            "coverage",
            f"{nontail_process_cov} | {body_cov} @<{body_table}> | {maybe_tail_cov}",
        )

    print(f"Generated {len(continuous_ligatures)} continuous ligatures chain")

    monocraft.generate(outputDir + "Monocraft.ttf")
    monocraft.generate(outputDir + "Monocraft.otf")


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


def drawImage(image, pen, *, dx=0, dy=0):
    for polygon in generatePolygons(image):
        start = True
        for x, y in polygon:
            x = (x + dx) * PIXEL_SIZE
            y = (y + dy) * PIXEL_SIZE
            if start:
                pen.moveTo(x, y)
                start = False
            else:
                pen.lineTo(x, y)
        pen.closePath()


generateFont()
generateExamples(characters, ligatures, charactersByCodepoint)