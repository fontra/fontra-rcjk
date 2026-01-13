import asyncio
import json
import logging
import traceback
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from random import random
from typing import Any, Awaitable, Callable

from fontra.core.classes import (
    Axes,
    Font,
    FontInfo,
    FontSource,
    Kerning,
    OpenTypeFeatures,
    VariableGlyph,
    structure,
    unstructure,
)
from fontra.core.instancer import mapLocationFromUserToSource
from fontra.core.protocols import WritableFontBackend

from .base import (
    GLIFGlyph,
    TimedCache,
    buildLayerGlyphsFromVariableGlyph,
    buildVariableGlyphFromLayerGlyphs,
    standardCustomDataItems,
    structureDesignspaceData,
    unstructureDesignspaceData,
)

logger = logging.getLogger(__name__)


_glyphTypes = [
    # (typeCode, typeName)
    ("AE", "atomic_elements"),
    ("DC", "deep_components"),
    ("CG", "character_glyphs"),
]

_baseGlyphMethods = {
    "AE": "atomic_element_",
    "DC": "deep_component_",
    "CG": "character_glyph_",
}


class RCJKEditError(Exception):
    pass


@dataclass
class RCJKGlyphInfo:
    typeCode: str
    glyphID: int
    updated: str


class RCJKMySQLBackend:
    @classmethod
    def fromRCJKClient(cls, client, fontUID, cacheDir=None) -> WritableFontBackend:
        return cls(client, fontUID, cacheDir)

    def __init__(self, client, fontUID, cacheDir=None):
        self.client = client
        self.fontUID = fontUID
        if cacheDir is not None:
            cacheDir = cacheDir / fontUID
        self.cacheDir = cacheDir
        self.pollExternalChangesInterval = 6
        self._rcjkGlyphInfo = None
        self._glyphCache = LRUCache()
        self._tempFontItemsCache = TimedCache()
        self._lastPolledForChanges = None
        self._writingChanges = 0
        self._glyphTimeStamps = {}
        self._pollNowEvent = asyncio.Event()
        self._glyphMap = None
        self._glyphMapTask = None
        self._defaultLocation = None
        self.watcherCallbacks = []
        self.watcherTask = None

    async def aclose(self):
        self._tempFontItemsCache.cancel()
        if self.watcherTask is not None:
            self.watcherTask.cancel()

    async def getGlyphMap(self) -> dict[str, list[int]]:
        await self._ensureGlyphMap()
        return dict(self._glyphMap)

    async def putGlyphMap(self, value: dict[str, list[int]]) -> None:
        pass

    def _ensureGlyphMap(self) -> asyncio.Task:
        # Prevent multiple concurrent queries by using a single task
        if self._glyphMapTask is None:
            self._glyphMapTask = asyncio.create_task(self._ensureGlyphMapTask())
        return self._glyphMapTask

    async def _ensureGlyphMapTask(self) -> None:
        if self._glyphMap is not None:
            return
        rcjkGlyphInfo = {}
        glyphMap = {}
        response = await self.client.glif_list(self.fontUID)
        if self._lastPolledForChanges is None:
            self._lastPolledForChanges = response["server_datetime"]
        for typeCode, typeName in _glyphTypes:
            for glyphInfo in response["data"][typeName]:
                glyphMap[glyphInfo["name"]] = _codePointsFromGlyphInfo(glyphInfo)
                rcjkGlyphInfo[glyphInfo["name"]] = RCJKGlyphInfo(
                    typeCode, glyphInfo["id"], getUpdatedTimeStamp(glyphInfo)
                )
        self._glyphMap = glyphMap
        self._rcjkGlyphInfo = rcjkGlyphInfo

    async def _getMiscFontItems(self) -> None:
        if not hasattr(self, "_getMiscFontItemsTask"):

            async def taskFunc():
                font_data = await self.client.font_get(self.fontUID)
                self._tempFontItemsCache["designspace"] = structureDesignspaceData(
                    font_data["data"].get("designspace", {})
                )
                self._tempFontItemsCache["features"] = font_data["data"].get(
                    "features", ""
                )
                self._tempFontItemsCache["customData"] = (
                    standardCustomDataItems | font_data["data"].get("fontlib", {})
                )
                self._tempFontItemsCache.updateTimeOut()
                del self._getMiscFontItemsTask

            self._getMiscFontItemsTask = asyncio.create_task(taskFunc())
        await self._getMiscFontItemsTask

    async def _getDesignspace(self) -> Font:
        await self._getMiscFontItems()
        designspace = self._tempFontItemsCache["designspace"]
        self._updateDefaultLocation(designspace)
        return designspace

    def _updateDefaultLocation(self, designspace):
        userLoc = {axis.name: axis.defaultValue for axis in designspace.axes.axes}
        self._defaultLocation = mapLocationFromUserToSource(
            userLoc, designspace.axes.axes
        )

    async def getFontInfo(self) -> FontInfo:
        designspace = await self._getDesignspace()
        return deepcopy(designspace.fontInfo)

    async def putFontInfo(self, fontInfo: FontInfo):
        designspace = await self._getDesignspace()
        designspace.fontInfo = deepcopy(fontInfo)
        await self._writeDesignspace(designspace)

    async def getSources(self) -> dict[str, FontSource]:
        designspace = await self._getDesignspace()
        return deepcopy(designspace.sources)

    async def putSources(self, sources: dict[str, FontSource]) -> None:
        designspace = await self._getDesignspace()
        designspace.sources = deepcopy(sources)
        await self._writeDesignspace(designspace)

    async def getAxes(self) -> Axes:
        designspace = await self._getDesignspace()
        return deepcopy(designspace.axes)

    async def putAxes(self, axes: Axes) -> None:
        designspace = await self._getDesignspace()
        designspace.axes = deepcopy(axes)
        self._updateDefaultLocation(designspace)
        await self._writeDesignspace(designspace)

    async def _writeDesignspace(self, designspace) -> None:
        _ = await self.client.font_update(
            self.fontUID, designspace=unstructureDesignspaceData(designspace)
        )

    async def getDefaultLocation(self) -> dict[str, float]:
        if self._defaultLocation is None:
            _ = await self.getAxes()
        assert self._defaultLocation is not None
        return self._defaultLocation

    async def getUnitsPerEm(self) -> int:
        designspace = await self._getDesignspace()
        return designspace.unitsPerEm

    async def putUnitsPerEm(self, value: int) -> None:
        designspace = await self._getDesignspace()
        designspace.unitsPerEm = value
        await self._writeDesignspace(designspace)

    async def getKerning(self) -> dict[str, Kerning]:
        return {}

    async def putKerning(self, kerning: dict[str, Kerning]) -> None:
        logger.warning("writing kerning is not yet supported")

    async def getFeatures(self) -> OpenTypeFeatures:
        await self._getMiscFontItems()
        featureText = self._tempFontItemsCache["features"]
        return OpenTypeFeatures(text=featureText)

    async def putFeatures(self, features: OpenTypeFeatures) -> None:
        if features.language != "fea":
            logger.warning(
                f"skip writing features in unsupported language: {features.language!r}"
            )
            return

        await self._getMiscFontItems()
        self._tempFontItemsCache["features"] = features.text
        _ = await self.client.font_update(self.fontUID, features=features.text)

    async def getCustomData(self) -> dict[str, Any]:
        customData = self._tempFontItemsCache.get("customData")
        if customData is None:
            await self._getMiscFontItems()
            customData = self._tempFontItemsCache["customData"]
        return deepcopy(customData)

    async def putCustomData(self, customData: dict[str, Any]) -> None:
        await self._getMiscFontItems()
        self._tempFontItemsCache["customData"] = deepcopy(customData)
        _ = await self.client.font_update(self.fontUID, fontlib=customData)

    def _readGlyphFromCacheDir(self, glyphName: str) -> VariableGlyph | None:
        if self.cacheDir is None:
            return None
        glyphInfo = self._rcjkGlyphInfo[glyphName]
        fileName = f"{glyphInfo.glyphID}-{glyphInfo.updated}.json"
        path = self.cacheDir / fileName
        if not path.exists():
            return None
        try:
            return structure(
                json.loads(path.read_text(encoding="utf-8")), VariableGlyph
            )
        except Exception as e:
            logger.exception(f"error reading {glyphName!r} from local cache: {e!r}")
            return None

    def _writeGlyphToCacheDir(self, glyphName: str, glyph: VariableGlyph) -> None:
        if self.cacheDir is None:
            return
        glyphInfo = self._rcjkGlyphInfo[glyphName]
        globPattern = f"{glyphInfo.glyphID}-*.json"
        for stalePath in self.cacheDir.glob(globPattern):
            stalePath.unlink()
        fileName = f"{glyphInfo.glyphID}-{glyphInfo.updated}.json"
        path = self.cacheDir / fileName
        try:
            self.cacheDir.mkdir(exist_ok=True, parents=True)
            path.write_text(
                json.dumps(unstructure(glyph), separators=(",", ":")), encoding="utf-8"
            )
        except Exception as e:
            logger.exception(f"error writing {glyphName!r} to local cache: {e!r}")

    def _deleteGlyphFromCacheDir(self, glyphName: str) -> None:
        if self.cacheDir is None:
            return
        glyphInfo = self._rcjkGlyphInfo.get(glyphName)
        if glyphInfo is None:
            return
        globPattern = f"{glyphInfo.glyphID}-*.json"
        for stalePath in self.cacheDir.glob(globPattern):
            stalePath.unlink()

    async def getGlyph(self, glyphName: str) -> VariableGlyph | None:
        await self._ensureGlyphMap()
        if glyphName not in self._glyphMap:
            return None
        glyph = self._readGlyphFromCacheDir(glyphName)
        if glyph is None:
            designspace = await self._getDesignspace()
            layerGlyphs = await self._getLayerGlyphs(glyphName)
            glyph = buildVariableGlyphFromLayerGlyphs(
                layerGlyphs, designspace.axes.axes
            )
            self._writeGlyphToCacheDir(glyphName, glyph)
        return glyph

    async def _getLayerGlyphs(self, glyphName):
        layerGlyphs = self._glyphCache.get(glyphName)
        if layerGlyphs is None:
            glyphInfo = self._rcjkGlyphInfo[glyphName]
            getMethodName = _getFullMethodName(glyphInfo.typeCode, "get")
            method = getattr(self.client, getMethodName)
            response = await method(
                self.fontUID,
                glyphInfo.glyphID,
                return_layers=True,
                return_made_of=True,
                return_used_by=False,
            )
            if self._lastPolledForChanges is None:
                self._lastPolledForChanges = response["server_datetime"]

            glyphData = response["data"]
            self._populateGlyphCache(glyphName, glyphData)
            layerGlyphs = self._glyphCache[glyphName]
        return layerGlyphs

    def _populateGlyphCache(self, glyphName, glyphData):
        if glyphName in self._glyphCache:
            return
        self._glyphCache[glyphName] = buildLayerGlyphsFromResponseData(glyphData)
        timeStamp = getUpdatedTimeStamp(glyphData)
        self._glyphTimeStamps[glyphName] = timeStamp
        self._rcjkGlyphInfo[glyphName].updated = timeStamp
        for subGlyphData in glyphData.get("made_of", ()):
            subGlyphName = subGlyphData["name"]
            glyphInfo = self._rcjkGlyphInfo[subGlyphName]
            assert glyphInfo.typeCode == subGlyphData["type_code"]
            assert glyphInfo.glyphID == subGlyphData["id"]
            self._populateGlyphCache(subGlyphName, subGlyphData)

    async def putGlyph(
        self, glyphName: str, glyph: VariableGlyph, codePoints: list[int]
    ) -> None:
        await self._ensureGlyphMap()
        logger.info(f"Start writing {glyphName}")
        self._writingChanges += 1
        try:
            return await self._putGlyph(glyphName, glyph, codePoints)
        finally:
            self._writingChanges -= 1
            logger.info(f"Done writing {glyphName}")

    async def _putGlyph(
        self, glyphName: str, glyph: VariableGlyph, codePoints: list[int]
    ) -> None:
        defaultLocation = await self.getDefaultLocation()

        if glyphName not in self._rcjkGlyphInfo:
            await self._newGlyph(glyphName, codePoints)
            existingLayerGlyphs = {}
        else:
            existingLayerGlyphs = await self._getLayerGlyphs(glyphName)

        existingLayerData = {k: v.asGLIFData() for k, v in existingLayerGlyphs.items()}

        layerGlyphs = buildLayerGlyphsFromVariableGlyph(
            glyphName, glyph, codePoints, defaultLocation, existingLayerGlyphs
        )

        self._glyphMap[glyphName] = codePoints

        lockResponse = await self._callGlyphMethod(glyphName, "lock", return_data=False)

        error = False

        try:
            glyphTimeStamp = self._glyphTimeStamps[glyphName]
            currentTimeStamp = getUpdatedTimeStamp(lockResponse["data"])
            if glyphTimeStamp != currentTimeStamp:
                raise RCJKEditError("Someone else made an edit just before you.")

            for layerName, layerGlyph in layerGlyphs.items():
                xmlData = layerGlyph.asGLIFData()
                existingXMLData = existingLayerData.get(layerName)
                if xmlData == existingXMLData:
                    # There was no change in the xml data, skip the update
                    continue
                if layerName == "foreground":
                    args = [glyphName, "update", xmlData]
                else:
                    methodName = "layer_update"
                    if existingXMLData is None:
                        logger.info(f"Creating layer {layerName} of {glyphName}")
                        methodName = "layer_create"
                    args = [glyphName, methodName, layerName, xmlData]
                await self._callGlyphMethod(
                    *args,
                    return_data=False,
                    return_layers=False,
                )
            for layerName in set(existingLayerData) - set(layerGlyphs):
                logger.info(f"Deleting layer {layerName} of {glyphName}")
                await self._callGlyphMethod(
                    glyphName,
                    "layer_delete",
                    layerName,
                )
            self._glyphCache[glyphName] = layerGlyphs
        except Exception:
            error = True
            raise
        finally:
            unlockResponse = await self._callGlyphMethod(
                glyphName, "unlock", return_data=False
            )
            if error:
                asyncio.get_running_loop().call_soon(self._pollNowEvent.set)

        timeStamp = getUpdatedTimeStamp(unlockResponse["data"])
        self._glyphTimeStamps[glyphName] = timeStamp
        self._rcjkGlyphInfo[glyphName].updated = timeStamp
        self._writeGlyphToCacheDir(glyphName, glyph)

    async def _newGlyph(self, glyphName: str, codePoints: list[int]) -> None:
        # In _newGlyph() we create a new character glyph in the database.
        # _putGlyph will immediately overwrite it with the real glyph data,
        # with a lock acquired. Our dummy glyph has to have a glyph name, but
        # we're setting .width to an arbitrary positive value so we can still
        # see it if anything goes wrong.
        logger.info(f"Creating new glyph '{glyphName}'")
        dummyGlyph = GLIFGlyph()
        dummyGlyph.name = glyphName
        dummyGlyph.unicodes = codePoints
        dummyGlyph.width = 314  # arbitrary positive value
        xmlData = dummyGlyph.asGLIFData()
        response = await self.client.character_glyph_create(
            self.fontUID, xmlData, return_data=False
        )
        glyphID = response["data"]["id"]
        self._glyphMap[glyphName] = codePoints
        timeStamp = getUpdatedTimeStamp(response["data"])
        self._rcjkGlyphInfo[glyphName] = RCJKGlyphInfo("CG", glyphID, timeStamp)
        self._glyphTimeStamps[glyphName] = timeStamp

    async def deleteGlyph(self, glyphName: str) -> None:
        await self._ensureGlyphMap()
        if glyphName not in self._rcjkGlyphInfo:
            logger.debug(f"Can't delete unknown glyph '{glyphName}'")
            return

        logger.info(f"Deleting glyph '{glyphName}'")

        _ = await self._callGlyphMethod(glyphName, "lock", return_data=False)
        try:
            _ = await self._callGlyphMethod(glyphName, "delete")
        except Exception:
            _ = await self._callGlyphMethod(glyphName, "unlock", return_data=False)
            raise

        # We set the time stamp to None so we can later distinguish "we deleted this
        # glyph" from "this glyph was externally deleted"
        self._deleteGlyphFromCacheDir(glyphName)
        self._glyphTimeStamps[glyphName] = None
        del self._rcjkGlyphInfo[glyphName]
        del self._glyphMap[glyphName]
        self._glyphCache.pop(glyphName, None)

    async def findGlyphsThatUseGlyph(self, glyphName: str) -> list[str]:
        glyphInfo = self._rcjkGlyphInfo.get(glyphName)
        if glyphInfo is None:
            return []
        getMethodName = _getFullMethodName(glyphInfo.typeCode, "get")
        method = getattr(self.client, getMethodName)
        response = await method(
            self.fontUID,
            glyphInfo.glyphID,
            return_data=False,
            return_related=False,
            return_layers=False,
            return_made_of=False,
            return_used_by=True,
        )
        data = response["data"]
        assert data["name"] == glyphName
        return [item["name"] for item in data.get("used_by", [])]

    async def _callGlyphMethod(self, glyphName, methodName, *args, **kwargs):
        glyphInfo = self._rcjkGlyphInfo[glyphName]
        apiMethodName = _getFullMethodName(glyphInfo.typeCode, methodName)
        method = getattr(self.client, apiMethodName)
        return await method(self.fontUID, glyphInfo.glyphID, *args, **kwargs)

    async def watchExternalChanges(
        self, callback: Callable[[Any, Any], Awaitable[None]]
    ) -> None:
        self.watcherCallbacks.append(callback)
        if self.watcherTask is None:
            self.watcherTask = asyncio.create_task(self._watchExternalChangesLoop())

    async def _watchExternalChangesLoop(self):
        await self._ensureGlyphMap()
        errorDelay = 30
        while True:
            try:
                reloadPattern = await self._pollOnceForChanges()
            except Exception as e:
                logger.error("error while polling for changes: %r", e)
                traceback.print_exc()
                logger.info(f"pausing the poll loop for {errorDelay} seconds")
                await asyncio.sleep(errorDelay)
            else:
                if reloadPattern:
                    for callback in self.watcherCallbacks:
                        await callback(reloadPattern)

    async def _pollOnceForChanges(self) -> dict[str, Any] | None:
        try:
            await asyncio.wait_for(
                self._pollNowEvent.wait(),
                timeout=self.pollExternalChangesInterval + 2 * random(),
            )
        except asyncio.TimeoutError:
            pass

        self._pollNowEvent.clear()
        if self._lastPolledForChanges is None:
            # No glyphs have been requested, so there's nothing to update
            return None
        if self._writingChanges:
            # We're in the middle of writing changes, let's skip a round
            return None
        response = await self.client.glif_list(
            self.fontUID,
            updated_since=fudgeTimeStamp(self._lastPolledForChanges),
        )
        responseData = response["data"]
        glyphNames = set()
        haveGlyphMapUpdates = False
        latestTimeStamp = ""  # less than any timestamp string

        for glyphInfo in responseData.get("deleted_glifs", []):
            glyphName = glyphInfo["name"]
            if not glyphInfo["group_name"]:
                if self._glyphTimeStamps.get(glyphName) is None:
                    # We made this change ourselves
                    continue
                storedGlyphInfo = self._rcjkGlyphInfo[glyphName]
                if glyphInfo["glif_id"] != storedGlyphInfo.glyphID:
                    # The glyph was recreated in the meantime, ignore
                    continue

                logger.info(f"Found deleted glyph {glyphName}")
                haveGlyphMapUpdates = True
                del self._glyphMap[glyphName]
                del self._rcjkGlyphInfo[glyphName]
                latestTimeStamp = max(latestTimeStamp, glyphInfo["deleted_at"])
            # else:
            # A layer got deleted, but we also receive that glyph as a regular changed
            # glyph, via its layers_updated_at timestamp -- we should ignore here.

        for typeCode, typeName in _glyphTypes:
            for glyphInfo in responseData[typeName]:
                glyphName = glyphInfo["name"]
                glyphUpdatedAt = getUpdatedTimeStamp(glyphInfo)
                latestTimeStamp = max(latestTimeStamp, glyphUpdatedAt)

                if glyphUpdatedAt == self._glyphTimeStamps.get(glyphName):
                    # We made this change, or otherwise we already saw it
                    continue

                if glyphName not in self._rcjkGlyphInfo:
                    assert glyphName not in self._glyphMap
                    logger.info(f"New glyph {glyphName}")
                else:
                    assert glyphName in self._glyphMap, f"glyph not found: {glyphName}"

                self._glyphTimeStamps[glyphName] = glyphUpdatedAt
                self._rcjkGlyphInfo[glyphName] = RCJKGlyphInfo(
                    typeCode, glyphInfo["id"], glyphUpdatedAt
                )

                codePoints = _codePointsFromGlyphInfo(glyphInfo)
                if codePoints != self._glyphMap.get(glyphName):
                    self._glyphMap[glyphName] = codePoints
                    haveGlyphMapUpdates = True

                glyphNames.add(glyphName)
                self._glyphCache.pop(glyphName, None)

        if not latestTimeStamp:
            latestTimeStamp = response["server_datetime"]

        self._lastPolledForChanges = latestTimeStamp

        reloadPattern: dict[str, Any] = (
            {"glyphs": dict.fromkeys(glyphNames)} if glyphNames else {}
        )

        if haveGlyphMapUpdates:
            reloadPattern["glyphMap"] = None

        return reloadPattern


def _codePointsFromGlyphInfo(glyphInfo: dict) -> list[int]:
    return glyphInfo.get("unicodes", [])


def getUpdatedTimeStamp(info: dict) -> str:
    timeStamp = info["updated_at"]
    layers_updated_at = info.get("layers_updated_at")
    if layers_updated_at:
        timeStamp = max(timeStamp, layers_updated_at)
    return timeStamp


def buildLayerGlyphsFromResponseData(glyphData: dict) -> dict[str, GLIFGlyph]:
    layerGLIFData = [("foreground", glyphData["data"])]
    layerGLIFData.extend(
        (layer["group_name"], layer["data"]) for layer in glyphData.get("layers", ())
    )
    layerGlyphs = {}
    for layerName, glifData in layerGLIFData:
        layerGlyphs[layerName] = GLIFGlyph.fromGLIFData(glifData)
    return layerGlyphs


def _getFullMethodName(typeCode, methodName):
    return _baseGlyphMethods[typeCode] + methodName


class LRUCache(dict):
    """A quick and dirty Least Recently Used cache, which leverages the fact
    that dictionaries keep their insertion order.
    """

    def __init__(self, maxSize=128):
        assert isinstance(maxSize, int)
        assert maxSize > 0
        self._maxSize = maxSize

    def get(self, key, default=None):
        # Override so we get our custom __getitem__ behavior
        try:
            value = self[key]
        except KeyError:
            value = default
        return value

    def __getitem__(self, key):
        value = super().__getitem__(key)
        # Move key/value to the end
        del self[key]
        self[key] = value
        return value

    def __setitem__(self, key, value):
        if key in self:
            # Ensure key/value get inserted at the end
            del self[key]
        super().__setitem__(key, value)
        while len(self) > self._maxSize:
            del self[next(iter(self))]


def fudgeTimeStamp(isoString: str) -> str:
    """Add one millisecond to the timestamp, so we can account for differences
    in the microsecond range.
    """
    one_millisecond = timedelta(milliseconds=1)
    d = datetime.fromisoformat(isoString)
    d = d + one_millisecond
    return d.isoformat()
