# image_orient_tool/app.py
from PySide6.QtWidgets import QApplication
import sys
from .theme.palette import apply_dark_palette, apply_light_palette
from .settings_manager import SettingsManager
from . import i18n_support as i18n

def create_app():
    app = QApplication(sys.argv)
    app.setApplicationName("ImageOrientationTool")
    app.setOrganizationName("ImageOrientTool")
    
    settings = SettingsManager()
    follow_system, dark_mode = settings.load_theme_settings()
    
    if dark_mode:
        apply_dark_palette(app)
    else:
        apply_light_palette(app)

    # 言語設定を読み込んでQTranslatorをインストール
    # (translatorインスタンスはappにぶら下げてGCされないようにする)
    saved_language = settings.load_language()
    resolved_language = i18n.resolve_language_code(saved_language)
    app._translator = i18n.install_translator(app, resolved_language)
    app._current_language = resolved_language

    return app, settings