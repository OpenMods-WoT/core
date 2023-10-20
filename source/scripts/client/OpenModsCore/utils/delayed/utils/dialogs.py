from gui.shared.view_helpers.blur_manager import _BlurManager
from ... import overrideMethod

__all__ = ()


@overrideMethod(_BlurManager, '_setLayerBlur')
def _setLayerBlur(base, self, blur, *args, **kwargs):
    if self._battle is None:
        return base(self, blur, *args, **kwargs)
    self._battle.blurBackgroundViews(blur.ownLayer, blur.blurAnimRepeatCount)
