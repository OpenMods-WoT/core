import traceback
from functools import partial

import Event
from OpenModsCore import loadJson, overrideMethod
from OpenModsCore.config import smart_update

__all__ = ['g_modsListApi']


def try_import():
    try:
        from gui.modsListApi import g_modsListApi as modsListApi
    except ImportError:
        print 'OpenModsCore: ModsListApi package not found, ModsSettingsApi check skipped'

        class ModsList(object):
            @staticmethod
            def addModification(*_, **__):
                return NotImplemented

            @staticmethod
            def updateModification(*_, **__):
                return NotImplemented

            @staticmethod
            def removeModification(*_, **__):
                return NotImplemented

            @staticmethod
            def alertModification(*_, **__):
                return NotImplemented

            @staticmethod
            def clearModificationAlert(*_, **__):
                return NotImplemented

        modsListApi = ModsList()
        return modsListApi, None, None
    try:
        from gui.modsSettingsApi.api import ModsSettingsApi as _MSA_Orig
        from gui.modsSettingsApi.context_menu import HotkeyContextMenuHandler
        from gui.modsSettingsApi.hotkeys import HotkeysController
        from gui.modsSettingsApi.l10n import l10n
        from gui.modsSettingsApi.view import loadView, ModsSettingsApiWindow
        from gui.modsSettingsApi._constants import VIEW_ALIAS, HOTKEY_CONTEXT_MENU_HANDLER_ALIAS
        from gui.Scaleform.framework.managers.context_menu import ContextMenuManager
        from gui.shared.personality import ServicesLocator as SL
        from gui.shared.utils.functions import makeTooltip
        from gui.Scaleform.framework.entities.View import ViewKey
    except ImportError as e:
        print 'OpenModsCore: ModsSettingsApi package not loaded:', e
        return modsListApi, None, None
    ModsSettingsApiWindow.api = None
    HotkeyContextMenuHandler.api = None

    @overrideMethod(ModsSettingsApiWindow, '__init__')
    def new_init(base, self, ctx, *args, **kwargs):
        self.api = ctx
        return base(self, ctx, *args, **kwargs)

    @overrideMethod(ContextMenuManager, 'requestOptions')
    def new_requestOptions(base, self, handlerType, ctx, *args, **kwargs):
        base(self, handlerType, ctx, *args, **kwargs)
        if handlerType == HOTKEY_CONTEXT_MENU_HANDLER_ALIAS:
            self._ContextMenuManager__currentHandler.api = SL.appLoader.getDefLobbyApp(
            ).containerManager.getViewByKey(ViewKey(VIEW_ALIAS)).api

    class _ModsSettings(_MSA_Orig):
        def __init__(self, modsGroup, ID, langID, i18n):
            self.modsGroup = modsGroup
            self.ID = ID
            self.lang = langID
            self.isMSAWindowOpen = False
            self.activeMods = set()
            self.state = {'templates': {}, 'settings': {}}
            self.settingsListeners = {}
            self.buttonListeners = {}
            self.hotkeys = HotkeysController(self)
            self.onWindowOpened = Event.Event()
            self.onWindowClosed = Event.Event()
            self.onHotkeysUpdated = Event.Event()
            self.onSettingsChanged = Event.Event()
            self.onButtonClicked = Event.Event()
            self.userSettings = {
                'modsListApiName': l10n('name'),
                'modsListApiDescription': l10n('description'),
                'modsListApiIcon': '../mods/configs/%s/%s/icon.png' % (self.modsGroup, self.ID),
                'windowTitle': l10n('name'),
                'enableButtonTooltip': makeTooltip(l10n('stateswitcher/tooltip/header'), l10n('stateswitcher/tooltip/body')),
            }
            smart_update(self.userSettings, i18n)
            self.loadSettings()
            self.loadState()
            modsListApi.addModification(
                id=ID,
                name=self.userSettings['modsListApiName'],
                description=self.userSettings['modsListApiDescription'],
                icon=self.userSettings['modsListApiIcon'],
                enabled=True,
                login=True,
                lobby=True,
                callback=self.MSAPopulate
            )
            self.onWindowClosed += self.MSADispose

        def MSAPopulate(self):
            self.isMSAWindowOpen = True
            self.onWindowOpened()
            loadView(self)

        def MSADispose(self):
            self.isMSAWindowOpen = False

        def MSAApply(self, alias, *a, **kw):
            self.settingsListeners[alias](*a, **kw)

        def MSAButton(self, alias, *a, **kw):
            self.buttonListeners[alias](*a, **kw)

        def loadSettings(self):
            smart_update(self.userSettings, loadJson(
                self.ID, self.lang, self.userSettings, 'mods/configs/%s/%s/i18n/' % (self.modsGroup, self.ID)))

        def loadState(self):
            pass

        def saveState(self):
            pass

        def setModTemplate(self, linkage, template, callback, buttonHandler):
            self.settingsListeners[linkage] = callback
            self.buttonListeners[linkage] = buttonHandler
            return super(_ModsSettings, self).setModTemplate(linkage, template, self.MSAApply, self.MSAButton)

    return modsListApi, _MSA_Orig, _ModsSettings


g_modsListApi, MSA_Orig, ModsSettings = try_import()


def registerSettings(config):
    """
    Register a settings block in this mod's settings window.
    """
    newLangID = config.lang
    try:
        from helpers import getClientLanguage
        newLangID = str(getClientLanguage()).lower()
        if newLangID != config.lang:
            config.lang = newLangID
            config.loadLang()
    except StandardError:
        traceback.print_exc()
    if MSA_Orig is None:
        print config.LOG, 'no-GUI mode activated'
        return
    if config.modSettingsID not in config.modSettingsContainers:
        config.modSettingsContainers[config.modSettingsID] = ModsSettings(
            config.modsGroup, config.modSettingsID, newLangID, config.container_i18n)
    msc = config.modSettingsContainers[config.modSettingsID]
    msc.onWindowOpened += config.onMSAPopulate
    msc.onWindowClosed += config.onMSADestroy
    if not hasattr(config, 'blockIDs'):
        msc.setModTemplate(config.ID, config.template, config.onApplySettings, config.onButtonPress)
        return
    templates = config.template
    [msc.setModTemplate(
        config.ID + ID, templates[ID], partial(config.onApplySettings, blockID=ID), partial(config.onButtonPress, blockID=ID))
        for ID in config.blockIDs]
