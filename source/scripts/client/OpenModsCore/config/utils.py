import BigWorld
import Keys
import traceback
from functools import partial

modSettingsContainers = {}


def smart_update(dict1, dict2):
    for k in dict1:
        if isinstance(dict1[k], dict):
            smart_update(dict1[k], dict2.get(k, {}))
        elif k in dict2:
            v = dict2[k]
            dict1[k] = v.encode('utf-8') if isinstance(v, unicode) else v


def readHotKeys(data):
    for key in data:
        for keyType in ('key', 'button'):
            if keyType not in key:
                continue
            data[key] = []
            for keySet in data.get(key.replace(keyType, keyType.capitalize()), []):
                if isinstance(keySet, list):
                    data[key].append([])
                    for hotKey in keySet:
                        hotKeyName = hotKey if 'KEY_' in hotKey else 'KEY_' + hotKey
                        data[key][-1].append(getattr(Keys, hotKeyName))
                else:
                    hotKeyName = keySet if 'KEY_' in keySet else 'KEY_' + keySet
                    data[key].append(getattr(Keys, hotKeyName))


def writeHotKeys(data):
    for key in data:
        for keyType in ('key', 'button'):
            if keyType.capitalize() not in key:
                continue
            data[key] = []
            for keySet in data[key.replace(keyType.capitalize(), keyType)]:
                if isinstance(keySet, list):
                    data[key].append([])
                    for hotKey in keySet:
                        hotKeyName = BigWorld.keyToString(hotKey)
                        data[key][-1].append(hotKeyName if 'KEY_' in hotKeyName else 'KEY_' + hotKeyName)
                else:
                    hotKeyName = BigWorld.keyToString(keySet)
                    data[key].append(hotKeyName if 'KEY_' in hotKeyName else 'KEY_' + hotKeyName)


def registerSettings(config, mode='full'):
    """
    Register a settings block in this mod's settings window.
    """
    try:
        from helpers import getClientLanguage
        newLang = str(getClientLanguage()).lower()
        if newLang != config.lang:
            config.lang = newLang
            config.loadLang()
    except StandardError:
        traceback.print_exc()
    try:
        # noinspection PyUnresolvedReferences
        from gui.vxSettingsApi import vxSettingsApi
        if config.modSettingsID not in modSettingsContainers:
            modSettingsContainers[config.modSettingsID] = config.containerClass(config.modSettingsID, config.configPath)
        msc = modSettingsContainers[config.modSettingsID]
        msc.onMSAPopulate += config.onMSAPopulate
        msc.onMSADestroy += config.onMSADestroy
        vxSettingsApi.onDataChanged += config.onDataChanged
        if mode == 'block':
            for blockID in config.blockIDs:
                vxSettingsApi.addMod(
                    config.modSettingsID, config.ID + blockID, partial(config.createTemplate, blockID),
                    config.getDataBlock(blockID), partial(config.onApplySettings, blockID), config.onButtonPress)
        else:
            vxSettingsApi.addMod(config.modSettingsID, config.ID, config.createTemplate, config.getData(),
                                 config.onApplySettings, config.onButtonPress)
    except ImportError:
        print '%s: no-GUI mode activated' % config.ID
    except StandardError:
        traceback.print_exc()
