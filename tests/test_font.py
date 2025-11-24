import contextlib
import json
import pathlib
import shutil
from importlib.metadata import entry_points

import pytest

from fontra.backends import getFileSystemBackend, newFileSystemBackend
from fontra.backends.copy import copyFont
from fontra.core.classes import (
    Anchor,
    Axes,
    Component,
    FontAxis,
    GlyphAxis,
    GlyphSource,
    Layer,
    OpenTypeFeatures,
    PackedPath,
    StaticGlyph,
    VariableGlyph,
    structure,
    unstructure,
)
from fontra_rcjk.base import makeSafeLayerName, standardCustomDataItems

dataDir = pathlib.Path(__file__).resolve().parent / "data"


getGlyphTestData = [
    (
        "rcjk",
        {
            "axes": [
                {"defaultValue": 0.0, "maxValue": 1.0, "minValue": 0.0, "name": "HLON"},
                {"defaultValue": 0.0, "maxValue": 1.0, "minValue": 0.0, "name": "WGHT"},
            ],
            "name": "one_00",
            "sources": [
                {
                    "name": "<default>",
                    "location": {},
                    "layerName": "foreground",
                    "customData": {"fontra.development.status": 0},
                },
                {
                    "name": "longbar",
                    "location": {"HLON": 1.0},
                    "layerName": "longbar",
                    "customData": {"fontra.development.status": 0},
                },
                {
                    "name": "bold",
                    "location": {"WGHT": 1.0},
                    "layerName": "bold",
                    "customData": {"fontra.development.status": 0},
                },
            ],
            "layers": {
                "foreground": {
                    "glyph": {
                        "path": {
                            "coordinates": [
                                105,
                                0,
                                134,
                                0,
                                134,
                                600,
                                110,
                                600,
                                92,
                                600,
                                74,
                                598,
                                59,
                                596,
                                30,
                                592,
                                30,
                                572,
                                105,
                                572,
                            ],
                            "pointTypes": [0, 0, 0, 8, 2, 2, 8, 0, 0, 0],
                            "contourInfo": [{"endPoint": 9, "isClosed": True}],
                        },
                        "components": [],
                        "xAdvance": 229,
                    },
                },
                "bold": {
                    "glyph": {
                        "path": {
                            "coordinates": [
                                135,
                                0,
                                325,
                                0,
                                325,
                                600,
                                170,
                                600,
                                152,
                                600,
                                135,
                                598,
                                119,
                                596,
                                20,
                                582,
                                20,
                                457,
                                135,
                                457,
                            ],
                            "pointTypes": [0, 0, 0, 8, 2, 2, 8, 0, 0, 0],
                            "contourInfo": [{"endPoint": 9, "isClosed": True}],
                        },
                        "components": [],
                        "xAdvance": 450,
                    },
                },
                "longbar": {
                    "glyph": {
                        "path": {
                            "coordinates": [
                                175,
                                0,
                                204,
                                0,
                                204,
                                600,
                                180,
                                600,
                                152,
                                600,
                                124,
                                598,
                                99,
                                597,
                                0,
                                592,
                                0,
                                572,
                                175,
                                572,
                            ],
                            "pointTypes": [0, 0, 0, 8, 2, 2, 8, 0, 0, 0],
                            "contourInfo": [{"endPoint": 9, "isClosed": True}],
                        },
                        "components": [],
                        "xAdvance": 369,
                    },
                },
            },
        },
    ),
    (
        "rcjk",
        {
            "axes": [
                {"defaultValue": 0.0, "maxValue": 1.0, "minValue": 0.0, "name": "wght"}
            ],
            "name": "uni0031",
            "sources": [
                {
                    "name": "<default>",
                    "location": {},
                    "layerName": "foreground",
                    "customData": {"fontra.development.status": 0},
                },
                {
                    "name": "wght",
                    "location": {"wght": 1},
                    "layerName": "wght",
                    "customData": {"fontra.development.status": 0},
                },
            ],
            "layers": {
                "foreground": {
                    "glyph": {
                        "path": {
                            "contourInfo": [],
                            "coordinates": [],
                            "pointTypes": [],
                        },
                        "components": [
                            {
                                "name": "DC_0031_00",
                                "transformation": {
                                    "rotation": 0,
                                    "scaleX": 1,
                                    "scaleY": 1,
                                    "tCenterX": 0,
                                    "tCenterY": 0,
                                    "translateX": -1,
                                    "translateY": 0,
                                },
                                "location": {"T_H_lo": 0, "X_X_bo": 0},
                            }
                        ],
                        "xAdvance": 350,
                    },
                },
                "wght": {
                    "glyph": {
                        "path": {
                            "contourInfo": [],
                            "coordinates": [],
                            "pointTypes": [],
                        },
                        "components": [
                            {
                                "name": "DC_0031_00",
                                "transformation": {
                                    "rotation": 0,
                                    "scaleX": 0.93,
                                    "scaleY": 1,
                                    "tCenterX": 0,
                                    "tCenterY": 0,
                                    "translateX": -23.0,
                                    "translateY": 0.0,
                                },
                                "location": {"T_H_lo": 0, "X_X_bo": 0.7},
                            }
                        ],
                        "xAdvance": 350,
                    },
                },
            },
        },
    ),
    (
        "rcjk",
        {
            "axes": [
                {
                    "defaultValue": 0.0,
                    "maxValue": 1.0,
                    "minValue": 0.0,
                    "name": "X_X_bo",
                },
                {
                    "defaultValue": 0.0,
                    "maxValue": 1.0,
                    "minValue": 0.0,
                    "name": "X_X_la",
                },
            ],
            "name": "DC_0030_00",
            "sources": [
                {
                    "name": "<default>",
                    "location": {},
                    "layerName": "foreground",
                    "customData": {"fontra.development.status": 0},
                },
                {
                    "name": "X_X_bo",
                    "location": {"X_X_bo": 1.0},
                    "layerName": "X_X_bo",
                    "customData": {"fontra.development.status": 0},
                },
                {
                    "name": "X_X_la",
                    "location": {"X_X_la": 1.0},
                    "layerName": "X_X_la",
                    "customData": {"fontra.development.status": 0},
                },
            ],
            "layers": {
                "foreground": {
                    "glyph": {
                        "path": {
                            "contourInfo": [],
                            "coordinates": [],
                            "pointTypes": [],
                        },
                        "components": [
                            {
                                "location": {"WDTH": 0.33, "WGHT": 0.45},
                                "name": "zero_00",
                                "transformation": {
                                    "rotation": 0,
                                    "scaleX": 1,
                                    "scaleY": 1,
                                    "tCenterX": 0,
                                    "tCenterY": 0,
                                    "translateX": 0,
                                    "translateY": 0,
                                },
                            }
                        ],
                        "xAdvance": 600,
                    },
                },
                "X_X_bo": {
                    "glyph": {
                        "path": {
                            "contourInfo": [],
                            "coordinates": [],
                            "pointTypes": [],
                        },
                        "components": [
                            {
                                "location": {"WDTH": 0.33, "WGHT": 1.0},
                                "name": "zero_00",
                                "transformation": {
                                    "rotation": 0,
                                    "scaleX": 1,
                                    "scaleY": 1,
                                    "tCenterX": 0,
                                    "tCenterY": 0,
                                    "translateX": 0,
                                    "translateY": 0,
                                },
                            }
                        ],
                        "xAdvance": 600,
                    },
                },
                "X_X_la": {
                    "glyph": {
                        "path": {
                            "contourInfo": [],
                            "coordinates": [],
                            "pointTypes": [],
                        },
                        "components": [
                            {
                                "location": {"WDTH": 1.0, "WGHT": 0.45},
                                "name": "zero_00",
                                "transformation": {
                                    "rotation": 0,
                                    "scaleX": 1,
                                    "scaleY": 1,
                                    "tCenterX": 0,
                                    "tCenterY": 0,
                                    "translateX": 0,
                                    "translateY": 0,
                                },
                            }
                        ],
                        "xAdvance": 600,
                    },
                },
            },
        },
    ),
]


testFontPaths = {
    "rcjk": dataDir / "figArnaud.rcjk",
}


def getBackendClassByName(backendName):
    backendEntryPoints = entry_points(group="fontra.filesystem.backends")
    return backendEntryPoints[backendName].load()


def getTestFont(backendName):
    cls = getBackendClassByName(backendName)
    return cls.fromPath(testFontPaths[backendName])


getGlyphNamesTestData = [
    ("rcjk", 82, ["DC_0030_00", "DC_0031_00", "DC_0032_00", "DC_0033_00"]),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "backendName, numGlyphs, firstFourGlyphNames", getGlyphNamesTestData
)
async def test_getGlyphNames(backendName, numGlyphs, firstFourGlyphNames):
    font = getTestFont(backendName)
    async with contextlib.aclosing(font):
        glyphNames = sorted(await font.getGlyphMap())
        assert numGlyphs == len(glyphNames)
        assert firstFourGlyphNames == sorted(glyphNames)[:4]


getGlyphMapTestData = [
    ("rcjk", 82, {"uni0031": [ord("1")]}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("backendName, numGlyphs, testMapping", getGlyphMapTestData)
async def test_getGlyphMap(backendName, numGlyphs, testMapping):
    font = getTestFont(backendName)
    async with contextlib.aclosing(font):
        glyphMap = await font.getGlyphMap()
        assert numGlyphs == len(glyphMap)
        for glyphName, codePoints in testMapping.items():
            assert glyphMap[glyphName] == codePoints


@pytest.mark.asyncio
@pytest.mark.parametrize("backendName, expectedGlyph", getGlyphTestData)
async def test_getGlyph(backendName, expectedGlyph):
    expectedGlyph = structure(expectedGlyph, VariableGlyph)
    font = getTestFont(backendName)
    async with contextlib.aclosing(font):
        glyph = await font.getGlyph(expectedGlyph.name)
        assert unstructure(glyph) == unstructure(expectedGlyph)
        assert glyph == expectedGlyph


@pytest.mark.asyncio
async def test_getGlyphUnknownGlyph():
    font = getTestFont("rcjk")
    async with contextlib.aclosing(font):
        glyph = await font.getGlyph("a-glyph-that-does-not-exist")
        assert glyph is None


getGlobalAxesTestData = [
    (
        "rcjk",
        Axes(
            axes=[
                FontAxis(
                    label="Weight",
                    name="wght",
                    tag="wght",
                    minValue=400,
                    defaultValue=400,
                    maxValue=700,
                ),
            ]
        ),
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("backendName, expectedGlobalAxes", getGlobalAxesTestData)
async def test_getAxes(backendName, expectedGlobalAxes):
    font = getTestFont(backendName)
    globalAxes = await font.getAxes()
    assert expectedGlobalAxes == globalAxes


@pytest.mark.asyncio
@pytest.mark.parametrize("backendName, expectedLibLen", [("rcjk", 5)])
async def test_getCustomData(backendName, expectedLibLen):
    font = getTestFont(backendName)
    lib = await font.getCustomData()
    assert expectedLibLen == len(lib)


@pytest.mark.asyncio
@pytest.mark.parametrize("backendName, expectedUnitsPerEm", [("rcjk", 1000)])
async def test_getUnitsPerEm(backendName, expectedUnitsPerEm):
    font = getTestFont(backendName)
    unitsPerEm = await font.getUnitsPerEm()
    assert expectedUnitsPerEm == unitsPerEm


@pytest.fixture
def writableTestFont(tmpdir):
    sourcePath = testFontPaths["rcjk"]
    destPath = tmpdir / sourcePath.name
    shutil.copytree(sourcePath, destPath)
    return getBackendClassByName("rcjk").fromPath(destPath)


@pytest.fixture
def mutatorTestFont():
    sourcePath = dataDir / "MutatorSansLocationBase.rcjk"
    return getBackendClassByName("rcjk").fromPath(sourcePath)


glyphData_a_before = [
    "<?xml version='1.0' encoding='UTF-8'?>",
    '<glyph name="a" format="2">',
    '  <advance width="500"/>',
    '  <unicode hex="0061"/>',
    "  <note>",
    "some note",
    "</note>",
    '  <guideline x="360" y="612" angle="0"/>',
    '  <anchor x="250" y="700" name="top"/>',
    "  <outline>",
    "    <contour>",
    '      <point x="50" y="0" type="line"/>',
    '      <point x="250" y="650" type="line"/>',
    '      <point x="450" y="0" type="line"/>',
    "    </contour>",
    "  </outline>",
    "  <lib>",
    "    <dict>",
    "      <key>robocjk.status</key>",
    "      <integer>0</integer>",
    "      <key>robocjk.variationGlyphs</key>",
    "      <array>",
    "        <dict>",
    "          <key>layerName</key>",
    "          <string>bold</string>",
    "          <key>location</key>",
    "          <dict>",
    "            <key>wght</key>",
    "            <integer>700</integer>",
    "          </dict>",
    "          <key>on</key>",
    "          <true/>",
    "          <key>sourceName</key>",
    "          <string>bold</string>",
    "          <key>status</key>",
    "          <integer>0</integer>",
    "        </dict>",
    "      </array>",
    "      <key>xyz.fontra.something.nothing</key>",
    "      <string>test</string>",
    "    </dict>",
    "  </lib>",
    "</glyph>",
]

glyphData_a_after = [
    "<?xml version='1.0' encoding='UTF-8'?>",
    '<glyph name="a" format="2">',
    '  <advance width="500"/>',
    '  <unicode hex="0061"/>',
    "  <note>",
    "some note",
    "</note>",
    '  <guideline x="360" y="612" angle="0"/>',
    '  <anchor x="250" y="700" name="top"/>',
    "  <outline>",
    "    <contour>",
    '      <point x="80" y="100" type="line"/>',
    '      <point x="250" y="650" type="line"/>',
    '      <point x="450" y="0" type="line"/>',
    "    </contour>",
    "  </outline>",
    "  <lib>",
    "    <dict>",
    "      <key>robocjk.status</key>",
    "      <integer>0</integer>",
    "      <key>robocjk.variationGlyphs</key>",
    "      <array>",
    "        <dict>",
    "          <key>layerName</key>",
    "          <string>bold</string>",
    "          <key>location</key>",
    "          <dict>",
    "            <key>wght</key>",
    "            <integer>700</integer>",
    "          </dict>",
    "          <key>on</key>",
    "          <true/>",
    "          <key>sourceName</key>",
    "          <string>bold</string>",
    "          <key>status</key>",
    "          <integer>0</integer>",
    "        </dict>",
    "      </array>",
    "      <key>xyz.fontra.something.nothing</key>",
    "      <string>test</string>",
    "    </dict>",
    "  </lib>",
    "</glyph>",
]


async def test_putGlyph(writableTestFont):
    async with contextlib.aclosing(writableTestFont):
        glyphMap = await writableTestFont.getGlyphMap()
        glyph = await writableTestFont.getGlyph("a")
        assert len(glyph.axes) == 0
        assert len(glyph.sources) == 2
        assert len(glyph.layers) == 2
        glifPath = writableTestFont.path / "characterGlyph" / "a.glif"
        glifData_before = glifPath.read_text().splitlines()
        assert glifData_before == glyphData_a_before

        coords = glyph.layers["foreground"].glyph.path.coordinates
        coords[0] = 80
        coords[1] = 100
        await writableTestFont.putGlyph(glyph.name, glyph, glyphMap["a"])
        glifData_after = glifPath.read_text().splitlines()
        assert glifData_after == glyphData_a_after


glyphData_a_after_delete_source = [
    "<?xml version='1.0' encoding='UTF-8'?>",
    '<glyph name="a" format="2">',
    '  <advance width="500"/>',
    '  <unicode hex="0061"/>',
    "  <note>",
    "some note",
    "</note>",
    '  <guideline x="360" y="612" angle="0"/>',
    '  <anchor x="250" y="700" name="top"/>',
    "  <outline>",
    "    <contour>",
    '      <point x="50" y="0" type="line"/>',
    '      <point x="250" y="650" type="line"/>',
    '      <point x="450" y="0" type="line"/>',
    "    </contour>",
    "  </outline>",
    "  <lib>",
    "    <dict>",
    "      <key>robocjk.status</key>",
    "      <integer>0</integer>",
    "      <key>xyz.fontra.something.nothing</key>",
    "      <string>test</string>",
    "    </dict>",
    "  </lib>",
    "</glyph>",
]


async def test_delete_source_layer(writableTestFont):
    async with contextlib.aclosing(writableTestFont):
        glifPathBold = writableTestFont.path / "characterGlyph" / "bold" / "a.glif"
        assert glifPathBold.exists()

        glyphMap = await writableTestFont.getGlyphMap()
        glyph = await writableTestFont.getGlyph("a")
        del glyph.sources[1]
        del glyph.layers["bold"]

        await writableTestFont.putGlyph(glyph.name, glyph, glyphMap["a"])

        glifPath = writableTestFont.path / "characterGlyph" / "a.glif"
        glifData = glifPath.read_text().splitlines()
        assert glifData == glyphData_a_after_delete_source
        assert not glifPathBold.exists()


newGlyphTestData = [
    "<?xml version='1.0' encoding='UTF-8'?>",
    '<glyph name="b" format="2">',
    '  <unicode hex="0062"/>',
    "  <outline>",
    "    <contour>",
    '      <point x="0" y="0" type="line"/>',
    "    </contour>",
    "  </outline>",
    "  <lib>",
    "    <dict>",
    "      <key>robocjk.axes</key>",
    "      <array>",
    "        <dict>",
    "          <key>defaultValue</key>",
    "          <integer>400</integer>",
    "          <key>maxValue</key>",
    "          <integer>700</integer>",
    "          <key>minValue</key>",
    "          <integer>100</integer>",
    "          <key>name</key>",
    "          <string>wght</string>",
    "        </dict>",
    "      </array>",
    "      <key>robocjk.status</key>",
    "      <integer>0</integer>",
    "      <key>robocjk.variationGlyphs</key>",
    "      <array>",
    "        <dict>",
    "          <key>layerName</key>",
    "          <string>bold</string>",
    "          <key>location</key>",
    "          <dict/>",
    "          <key>on</key>",
    "          <true/>",
    "          <key>sourceName</key>",
    "          <string>bold</string>",
    "          <key>status</key>",
    "          <integer>0</integer>",
    "        </dict>",
    "      </array>",
    "    </dict>",
    "  </lib>",
    "</glyph>",
]


def makeTestPath():
    return PackedPath.fromUnpackedContours(
        [{"points": [{"x": 0, "y": 0}], "isClosed": True}]
    )


async def test_new_glyph(writableTestFont):
    async with contextlib.aclosing(writableTestFont):
        glyph = VariableGlyph(
            name="b",
            axes=[GlyphAxis(name="wght", minValue=100, defaultValue=400, maxValue=700)],
            sources=[
                GlyphSource(name="default", layerName="default"),
                GlyphSource(name="bold", layerName="bold"),
            ],
            layers={
                "default": Layer(glyph=StaticGlyph(path=makeTestPath())),
                "bold": Layer(glyph=StaticGlyph(path=makeTestPath())),
            },
        )
        await writableTestFont.putGlyph(glyph.name, glyph, [ord("b")])

        glifPath = writableTestFont.path / "characterGlyph" / "b.glif"
        glifData = glifPath.read_text().splitlines()
        assert glifData == newGlyphTestData


async def test_add_new_layer(writableTestFont):
    async with contextlib.aclosing(writableTestFont):
        glyphName = "a"
        glyphMap = await writableTestFont.getGlyphMap()
        glyph = await writableTestFont.getGlyph(glyphName)
        newLayerName = "new_layer_name"

        layerPath = writableTestFont.path / "characterGlyph" / newLayerName
        assert not layerPath.exists()

        glyph.sources.append(GlyphSource(name=newLayerName, layerName=newLayerName))
        glyph.layers[newLayerName] = Layer(
            glyph=StaticGlyph(xAdvance=500, path=makeTestPath())
        )

        await writableTestFont.putGlyph(glyph.name, glyph, glyphMap[glyphName])

        assert layerPath.exists()
        layerGlifPath = layerPath / f"{glyphName}.glif"
        assert layerGlifPath.exists()


@pytest.mark.parametrize("glyphName", ["a", "uni0030"])
async def test_write_roundtrip(writableTestFont, glyphName):
    async with contextlib.aclosing(writableTestFont):
        glyphMap = await writableTestFont.getGlyphMap()
        glyph = await writableTestFont.getGlyph(glyphName)

        layerGlifPath = writableTestFont.path / "characterGlyph" / f"{glyphName}.glif"

        existingLayerData = layerGlifPath.read_text()
        await writableTestFont.putGlyph(glyph.name, glyph, glyphMap[glyphName])
        # Write the glyph again to ensure a write bug that would duplicate the
        # components doesn't resurface
        await writableTestFont.putGlyph(glyph.name, glyph, glyphMap[glyphName])
        newLayerData = layerGlifPath.read_text()

        assert existingLayerData == newLayerData


layerNameMappingTestData = [
    "<?xml version='1.0' encoding='UTF-8'?>",
    '<glyph name="a" format="2">',
    '  <advance width="500"/>',
    '  <unicode hex="0061"/>',
    "  <note>",
    "some note",
    "</note>",
    '  <guideline x="360" y="612" angle="0"/>',
    '  <anchor x="250" y="700" name="top"/>',
    "  <outline>",
    "    <contour>",
    '      <point x="50" y="0" type="line"/>',
    '      <point x="250" y="650" type="line"/>',
    '      <point x="450" y="0" type="line"/>',
    "    </contour>",
    "  </outline>",
    "  <lib>",
    "    <dict>",
    "      <key>fontra.layerNames</key>",
    "      <dict>",
    "        <key>cpppp_ppppme.be065888921b</key>",
    "        <string>cpppp/ppppme</string>",
    "        <key>cpppp_ppppmecpppp_ppppmecpppp_ppppmec.9e80c135accd</key>",
    "        <string>cpppp/ppppmecpppp/ppppmecpppp/ppppmecpppp/ppppmecpppp/ppppme</string>",
    "      </dict>",
    "      <key>robocjk.status</key>",
    "      <integer>0</integer>",
    "      <key>robocjk.variationGlyphs</key>",
    "      <array>",
    "        <dict>",
    "          <key>layerName</key>",
    "          <string>bold</string>",
    "          <key>location</key>",
    "          <dict>",
    "            <key>wght</key>",
    "            <integer>700</integer>",
    "          </dict>",
    "          <key>on</key>",
    "          <true/>",
    "          <key>sourceName</key>",
    "          <string>bold</string>",
    "          <key>status</key>",
    "          <integer>0</integer>",
    "        </dict>",
    "        <dict>",
    "          <key>layerName</key>",
    "          <string>good-layer-name-with-source</string>",
    "          <key>location</key>",
    "          <dict/>",
    "          <key>on</key>",
    "          <true/>",
    "          <key>sourceName</key>",
    "          <string>good-layer-name-with-source</string>",
    "          <key>status</key>",
    "          <integer>0</integer>",
    "        </dict>",
    "        <dict>",
    "          <key>fontraLayerName</key>",
    "          <string>boooo/oooold</string>",
    "          <key>layerName</key>",
    "          <string>boooo_oooold.75e003ed2da2</string>",
    "          <key>location</key>",
    "          <dict/>",
    "          <key>on</key>",
    "          <true/>",
    "          <key>sourceName</key>",
    "          <string>boooo/oooold</string>",
    "          <key>status</key>",
    "          <integer>0</integer>",
    "        </dict>",
    "        <dict>",
    "          <key>fontraLayerName</key>",
    "          <string>boooo/ooooldboooo/ooooldboooo/ooooldboooo/ooooldboooo/oooold</string>",
    "          <key>layerName</key>",
    "          <string>boooo_ooooldboooo_ooooldboooo_ooooldb.360a3fdd78e6</string>",
    "          <key>location</key>",
    "          <dict/>",
    "          <key>on</key>",
    "          <true/>",
    "          <key>sourceName</key>",
    "          <string>boooo/ooooldboooo/ooooldboooo/ooooldboooo/ooooldboooo/oooold</string>",
    "          <key>status</key>",
    "          <integer>0</integer>",
    "        </dict>",
    "      </array>",
    "      <key>xyz.fontra.something.nothing</key>",
    "      <string>test</string>",
    "    </dict>",
    "  </lib>",
    "</glyph>",
]


async def test_bad_layer_name(writableTestFont):
    async with contextlib.aclosing(writableTestFont):
        glyphName = "a"
        glyphMap = await writableTestFont.getGlyphMap()
        glyph = await writableTestFont.getGlyph(glyphName)

        layerPaths = []

        for doAddSource, badLayerName in [
            (True, "good-layer-name-with-source"),
            (False, "good-layer-name-without-source"),
            (True, "boooo/oooold"),
            (True, "boooo/oooold" * 5),
            (False, "cpppp/ppppme"),
            (False, "cpppp/ppppme" * 5),
        ]:
            safeLayerName = makeSafeLayerName(badLayerName)

            layerPath = writableTestFont.path / "characterGlyph" / safeLayerName
            assert not layerPath.exists()
            layerPaths.append(layerPath)

            if doAddSource:
                glyph.sources.append(
                    GlyphSource(
                        name=badLayerName,
                        layerName=badLayerName,
                        customData={"fontra.development.status": 0},
                    )
                )
            glyph.layers[badLayerName] = Layer(
                glyph=StaticGlyph(xAdvance=500, path=makeTestPath())
            )

        await writableTestFont.putGlyph(glyph.name, glyph, glyphMap[glyphName])

        for layerPath in layerPaths:
            assert layerPath.exists()
            layerGlifPath = layerPath / f"{glyphName}.glif"
            assert layerGlifPath.exists()

        mainGlifPath = writableTestFont.path / "characterGlyph" / f"{glyphName}.glif"
        glifData = mainGlifPath.read_text()
        assert glifData.splitlines() == layerNameMappingTestData

    reopenedFont = getFileSystemBackend(writableTestFont.path)
    async with contextlib.aclosing(reopenedFont):
        reopenedGlyph = await reopenedFont.getGlyph(glyphName)
        assert reopenedGlyph == glyph


async def test_bad_layer_name_issue242(writableTestFont):
    # https://github.com/fontra/fontra-rcjk/issues/242
    glyphName = "test"
    sourceName = "aaaa/bbbb"

    sources = [
        GlyphSource(
            name="<default>",
            layerName="foreground",
            customData={
                "fontra.development.status": 0,
            },
        ),
        GlyphSource(
            name=sourceName,
            layerName=sourceName,
            customData={
                "fontra.development.status": 0,
            },
        ),
    ]

    layerGlyph = StaticGlyph(
        xAdvance=500,
        path=makeTestPath(),
        components=[Component(name="uni0037")],
    )

    layers = {
        "foreground": Layer(glyph=layerGlyph),
        sourceName: Layer(glyph=layerGlyph),
    }

    glyph = VariableGlyph(name=glyphName, sources=sources, layers=layers)

    async with contextlib.aclosing(writableTestFont):
        await writableTestFont.putGlyph(glyph.name, glyph, [])

    reopenedFont = getFileSystemBackend(writableTestFont.path)
    async with contextlib.aclosing(reopenedFont):
        reopenedGlyph = await reopenedFont.getGlyph(glyphName)
        assert reopenedGlyph == glyph


deleteItemsTestData = [
    "<?xml version='1.0' encoding='UTF-8'?>",
    '<glyph name="uni0030" format="2">',
    '  <advance width="600"/>',
    '  <unicode hex="0030"/>',
    '  <guideline x="360" y="612" angle="0" identifier="gRMeb2PVEQ"/>',
    '  <guideline x="307" y="600" angle="0" identifier="386e1cIMnm"/>',
    '  <guideline x="305" y="-12" angle="0" identifier="xMdDy12pWP"/>',
    "  <outline>",
    "  </outline>",
    "  <lib>",
    "    <dict>",
    "      <key>public.markColor</key>",
    "      <string>1,0,0,1</string>",
    "      <key>robocjk.status</key>",
    "      <integer>0</integer>",
    "      <key>xyz.fontra.test</key>",
    "      <string>test</string>",
    "    </dict>",
    "  </lib>",
    "</glyph>",
]


async def test_delete_items(writableTestFont):
    async with contextlib.aclosing(writableTestFont):
        glyphName = "uni0030"
        glyphMap = await writableTestFont.getGlyphMap()
        glyph = await writableTestFont.getGlyph(glyphName)

        glyph.axes = []
        glyph.sources = [glyph.sources[0]]
        layerName = glyph.sources[0].layerName
        layer = glyph.layers[layerName]
        layer.glyph.components = []
        glyph.layers = {layerName: layer}

        await writableTestFont.putGlyph(glyph.name, glyph, glyphMap[glyphName])

        mainGlifPath = writableTestFont.path / "characterGlyph" / f"{glyphName}.glif"
        glifData = mainGlifPath.read_text()
        assert glifData.splitlines() == deleteItemsTestData


expectedReadMixedComponentTestData = {
    "name": "b",
    "sources": [
        {
            "name": "<default>",
            "layerName": "foreground",
            "customData": {"fontra.development.status": 0},
        }
    ],
    "layers": {
        "foreground": {
            "glyph": {
                "components": [
                    {"name": "a"},
                    {
                        "name": "DC_0033_00",
                        "transformation": {"translateX": 30},
                        "location": {"X_X_bo": 0, "X_X_la": 0},
                    },
                ],
                "xAdvance": 500,
            },
        }
    },
}


async def test_readMixClassicAndVariableComponents():
    font = getTestFont("rcjk")
    async with contextlib.aclosing(font):
        glyph = await font.getGlyph("b")
        assert expectedReadMixedComponentTestData == unstructure(glyph)


expectedWriteMixedComponentTestData = [
    "<?xml version='1.0' encoding='UTF-8'?>",
    '<glyph name="b" format="2">',
    '  <advance width="500"/>',
    '  <unicode hex="0062"/>',
    "  <outline>",
    "  </outline>",
    "  <lib>",
    "    <dict>",
    "      <key>robocjk.deepComponents</key>",
    "      <array>",
    "        <dict>",
    "          <key>coord</key>",
    "          <dict/>",
    "          <key>name</key>",
    "          <string>a</string>",
    "          <key>transform</key>",
    "          <dict>",
    "            <key>rotation</key>",
    "            <real>0.0</real>",
    "            <key>scalex</key>",
    "            <real>1.0</real>",
    "            <key>scaley</key>",
    "            <real>1.0</real>",
    "            <key>tcenterx</key>",
    "            <integer>0</integer>",
    "            <key>tcentery</key>",
    "            <integer>0</integer>",
    "            <key>x</key>",
    "            <integer>0</integer>",
    "            <key>y</key>",
    "            <integer>0</integer>",
    "          </dict>",
    "        </dict>",
    "        <dict>",
    "          <key>coord</key>",
    "          <dict>",
    "            <key>X_X_bo</key>",
    "            <integer>0</integer>",
    "            <key>X_X_la</key>",
    "            <integer>0</integer>",
    "          </dict>",
    "          <key>name</key>",
    "          <string>DC_0033_00</string>",
    "          <key>transform</key>",
    "          <dict>",
    "            <key>rotation</key>",
    "            <integer>0</integer>",
    "            <key>scalex</key>",
    "            <integer>1</integer>",
    "            <key>scaley</key>",
    "            <integer>1</integer>",
    "            <key>tcenterx</key>",
    "            <integer>0</integer>",
    "            <key>tcentery</key>",
    "            <integer>0</integer>",
    "            <key>x</key>",
    "            <integer>30</integer>",
    "            <key>y</key>",
    "            <integer>0</integer>",
    "          </dict>",
    "        </dict>",
    "      </array>",
    "      <key>robocjk.status</key>",
    "      <integer>0</integer>",
    "    </dict>",
    "  </lib>",
    "</glyph>",
]


async def test_writeMixClassicAndVariableComponents(writableTestFont):
    async with contextlib.aclosing(writableTestFont):
        glyphMap = await writableTestFont.getGlyphMap()
        glyph = await writableTestFont.getGlyph("b")
        await writableTestFont.putGlyph("b", glyph, glyphMap["b"])
        mainGlifPath = writableTestFont.path / "characterGlyph" / "b.glif"
        glifData = mainGlifPath.read_text()
        assert expectedWriteMixedComponentTestData == glifData.splitlines()


async def test_deleteGlyph(writableTestFont):
    glyphName = "eight_00"
    async with contextlib.aclosing(writableTestFont):
        glyphMap = await writableTestFont.getGlyphMap()
        assert glyphName in glyphMap
        glyphPaths = list(writableTestFont.path.glob(f"**/{glyphName}.glif"))
        assert len(glyphPaths) == 3

        await writableTestFont.deleteGlyph(glyphName)

        glyphMap = await writableTestFont.getGlyphMap()
        assert glyphName not in glyphMap
        glyphPaths = list(writableTestFont.path.glob(f"**/{glyphName}.glif"))
        assert len(glyphPaths) == 0


async def test_deleteGlyphRaisesKeyError(writableTestFont):
    glyphName = "A.doesnotexist"
    async with contextlib.aclosing(writableTestFont):
        with pytest.raises(KeyError, match="Glyph 'A.doesnotexist' does not exist"):
            await writableTestFont.deleteGlyph(glyphName)


async def test_variableComponentInNonSourceLayer(writableTestFont):
    async with contextlib.aclosing(writableTestFont):
        glyph = VariableGlyph(
            name="b",
            axes=[GlyphAxis(name="testing", minValue=0, defaultValue=0, maxValue=100)],
            sources=[
                GlyphSource(
                    name="<default>",
                    layerName="foreground",
                    customData={"fontra.development.status": 0},
                ),
                GlyphSource(
                    name="testing",
                    location={"testing": 100},
                    layerName="testing",
                    customData={"fontra.development.status": 0},
                ),
            ],
            layers={
                "foreground": Layer(
                    glyph=StaticGlyph(
                        xAdvance=500,
                        path=makeTestPath(),
                        components=[Component(name="a")],
                    )
                ),
                "testing": Layer(
                    glyph=StaticGlyph(xAdvance=500, components=[Component(name="a")])
                ),
                "testing^background": Layer(
                    glyph=StaticGlyph(xAdvance=500, components=[Component(name="a")])
                ),
            },
        )
        await writableTestFont.putGlyph(glyph.name, glyph, [ord("b")])

    reopenedFont = getFileSystemBackend(writableTestFont.path)
    async with contextlib.aclosing(reopenedFont):
        reopenedGlyph = await reopenedFont.getGlyph("b")
        assert reopenedGlyph == glyph


async def test_putUnitsPerEm(writableTestFont):
    async with contextlib.aclosing(writableTestFont):
        assert 1000 == await writableTestFont.getUnitsPerEm()
        await writableTestFont.putUnitsPerEm(2000)
        assert 2000 == await writableTestFont.getUnitsPerEm()


async def test_getFeatures(writableTestFont):
    font = getTestFont("rcjk")
    features = await font.getFeatures()
    assert "languagesystem DFLT dflt" in features.text


async def test_putFeatures(writableTestFont):
    featureText = "# feature text"
    async with contextlib.aclosing(writableTestFont):
        await writableTestFont.putFeatures(OpenTypeFeatures(text=featureText))
        assert (await writableTestFont.getFeatures()).text == featureText


async def test_read_write_anchors(writableTestFont):
    async with contextlib.aclosing(writableTestFont):
        glyph = await writableTestFont.getGlyph("a")
        assert glyph.layers[glyph.sources[0].layerName].glyph.anchors[0].y == 700
        glyph.layers[glyph.sources[0].layerName].glyph.anchors[0].y = 750
        await writableTestFont.putGlyph("a", glyph, [ord("a")])

    reopenedFont = getFileSystemBackend(writableTestFont.path)
    async with contextlib.aclosing(reopenedFont):
        glyph = await reopenedFont.getGlyph("a")
    assert glyph.layers[glyph.sources[0].layerName].glyph.anchors[0].y == 750


async def test_read_write_anchors_composite_glyph(writableTestFont):
    glyphName = "uni0030"
    codePoint = 0x30
    async with contextlib.aclosing(writableTestFont):
        glyph = await writableTestFont.getGlyph(glyphName)
        for layer in glyph.layers.values():
            assert not layer.glyph.anchors
            layer.glyph.anchors.append(Anchor(name="top", x=200, y=700))
        await writableTestFont.putGlyph(glyphName, glyph, [codePoint])

    reopenedFont = getFileSystemBackend(writableTestFont.path)
    async with contextlib.aclosing(reopenedFont):
        reopenedGlyph = await reopenedFont.getGlyph(glyphName)
    assert glyph == reopenedGlyph


async def test_read_write_glyph_customData(writableTestFont):
    glyphName = "uni0030"
    codePoint = 0x20
    async with contextlib.aclosing(writableTestFont):
        glyph = await writableTestFont.getGlyph(glyphName)
        glyph.customData["fontra.glyph.locked"] = True
        await writableTestFont.putGlyph(glyphName, glyph, [codePoint])

    reopenedFont = getFileSystemBackend(writableTestFont.path)
    async with contextlib.aclosing(reopenedFont):
        reopenedGlyph = await reopenedFont.getGlyph(glyphName)
    assert glyph == reopenedGlyph


async def test_statusFieldDefinitions(writableTestFont):
    customData = await writableTestFont.getCustomData()
    statusDefinitions = customData["fontra.sourceStatusFieldDefinitions"]
    assert (
        standardCustomDataItems["fontra.sourceStatusFieldDefinitions"]
        == statusDefinitions
    )
    newStatusDef = {
        "color": [0, 0, 0, 1],
        "label": "Rejected",
        "value": 5,
    }
    statusDefinitions.append(newStatusDef)

    editedCustomData = customData | {
        "fontra.sourceStatusFieldDefinitions": statusDefinitions
    }
    await writableTestFont.putCustomData(editedCustomData)

    newCustomData = await writableTestFont.getCustomData()
    newStatusDefinitions = newCustomData["fontra.sourceStatusFieldDefinitions"]

    assert newStatusDefinitions[5] == newStatusDef

    fontLibPath = writableTestFont.path / "fontLib.json"
    fontLib = json.loads(fontLibPath.read_text())

    assert editedCustomData == fontLib


async def test_round_trip_locationBase(mutatorTestFont, tmpdir):
    tmpdir = pathlib.Path(tmpdir)
    destPath = tmpdir / "test.rcjk"

    destFont = newFileSystemBackend(destPath)

    async with contextlib.aclosing(mutatorTestFont):
        async with contextlib.aclosing(destFont):
            await copyFont(mutatorTestFont, destFont)

        reopenedFont = getFileSystemBackend(destPath)
        async with contextlib.aclosing(reopenedFont):
            for glyphName in ["A", "B"]:
                sourceGlyph = await mutatorTestFont.getGlyph(glyphName)
                destGlyph = await reopenedFont.getGlyph(glyphName)
                assert sourceGlyph == destGlyph
                assert all(source.locationBase for source in sourceGlyph.sources)
