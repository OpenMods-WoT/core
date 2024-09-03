from gui.shared.view_helpers.blur_manager import _BlurManager
from realm import CURRENT_REALM
from ... import overrideMethod

__all__ = ()


@overrideMethod(_BlurManager, '_setLayerBlur')
def _setLayerBlur(base, self, blur, *args, **kwargs):
    if self._battle is None:
        return base(self, blur, *args, **kwargs)
    if CURRENT_REALM != 'RU':
        self._battle.blurBackgroundViews(blur.ownLayer, blur.blurAnimRepeatCount, blur.uiBlurRadius)
    else:
        self._battle.blurBackgroundViews(blur.ownLayer, blur.blurAnimRepeatCount)
