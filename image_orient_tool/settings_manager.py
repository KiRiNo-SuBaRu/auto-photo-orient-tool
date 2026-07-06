# image_orient_tool/settings_manager.py
from PySide6.QtCore import QSettings

class SettingsManager:
    def __init__(self):
        self.settings = QSettings("ImageOrientTool", "Settings")
    
    def load_theme_settings(self):
        follow_system = self.settings.value("theme/follow_system", True, type=bool)
        dark_mode = self.settings.value("theme/dark_mode", False, type=bool)
        return follow_system, dark_mode
    
    def save_theme_settings(self, follow_system: bool, dark_mode: bool):
        self.settings.setValue("theme/follow_system", follow_system)
        self.settings.setValue("theme/dark_mode", dark_mode)
    
    def load_window_geometry(self):
        return self.settings.value("window/geometry")
    
    def save_window_geometry(self, geometry):
        self.settings.setValue("window/geometry", geometry)

    def load_language(self) -> str:
        """
        言語設定を取得する

        Returns:
            言語コード ("auto", "ja", "en", "ko", "de", "ru", "fr")
            "auto" の場合はOSの言語設定に自動追従する
        """
        return self.settings.value("locale/language", "auto", type=str)

    def save_language(self, language_code: str):
        """
        言語設定を保存する

        Args:
            language_code: "auto", "ja", "en", "ko", "de", "ru", "fr" のいずれか
        """
        self.settings.setValue("locale/language", language_code)