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

import random
import itertools


def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    batch = tuple(itertools.islice(it, n))
    while batch:
        yield batch
        batch = tuple(itertools.islice(it, n))


def generateExamples(characters, ligatures, continuos_ligatures,
                     charactersByCodepoint):
    terminalOutput = 26 * "-" + " Monocraft " + 26 * "-"
    terminalOutput += "\n"
    terminalOutput += "\n".join(" ".join(l) for l in batched(
        (chr(c["codepoint"]) for c in characters if c["codepoint"] != 32),
        32,
    ))

    print(terminalOutput)

    characterOutput = "--- Monocraft ---\n\n"
    characterOutput += " ".join(map(chr, range(65, 91)))
    characterOutput += "\n"
    characterOutput += " ".join(map(chr, range(97, 123)))
    characterOutput += "\n" * 2
    characterOutput += " ".join(map(chr, range(48, 58)))
    characterOutput += "\n" * 2
    characterOutput += " ".join(
        chr(i) for i in itertools.chain(
            range(33, 48),
            range(58, 65),
            range(91, 97),
            range(123, 127),
        ))
    characterOutput += "\n"
    characterOutput += "\n".join(" ".join(l) for l in batched(
        (chr(i) for i in range(161, 382) if i in charactersByCodepoint),
        48,
    ))
    characterOutput += "\n"
    characterOutput += "\n".join(" ".join(l) for l in batched(
        (chr(i) for i in range(383, 1120) if i in charactersByCodepoint),
        48,
    ))
    characterOutput += "\n"
    characterOutput += "\n".join(" ".join(l) for l in batched(
        (chr(i) for i in range(1121, 8363) if i in charactersByCodepoint),
        48,
    ))
    characterOutput += "\n"
    characterOutput += "\n".join(" ".join(l) for l in batched(
        (chr(i) for i in range(8364, 65534) if i in charactersByCodepoint),
        48,
    ))

    ligatureOutput = "--- Ligatures ---"
    for ligature in ligatures:
        start = ''.join(
            map(lambda codepoint: ' ' + chr(codepoint), ligature['sequence']))
        start += (7 - len(ligature['sequence'])) * " "
        output = 5 * " " + ''.join(
            map(lambda codepoint: chr(codepoint), ligature['sequence']))
        ligatureOutput += "\n" + start + "->" + output

    continuosLigatureOutput = "--- Continuos Ligatures ---"
    r = random.Random(b"M1N3CR4F7")
    for continuos_ligature in continuos_ligatures:
        for i in range(2, 29):
            head = chr(r.choice(continuos_ligature["heads"])["char"])
            body = "".join(
                chr(r.choice(continuos_ligature["bodies"])["char"])
                for j in range(i))
            tail = chr(r.choice(continuos_ligature["tails"])["char"])
            continuosLigatureOutput += "\n" + head + body + tail

    f = open("../examples/glyphs.txt", "w", newline="\n")
    f.write(characterOutput + 2 * "\n" + ligatureOutput + "\n\n" +
            continuosLigatureOutput)
    f.close()
