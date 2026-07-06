# image_orient_tool/i18n_support.py
"""
多言語対応（QTranslator）用のヘルパーモジュール

ソース言語（tr()に直接書かれている文字列）は日本語。
対応する翻訳先言語:
    英語(en), 韓国語(ko), ドイツ語(de), ロシア語(ru), フランス語(fr),
    簡体字中国語(zh_CN), 繁体字中国語/台湾(zh_TW)

翻訳ファイルの作り方:
    1. pyside6-lupdate でソースコードから .ts ファイルを生成/更新
       pyside6-lupdate image_orient_tool/main_window.py image_orient_tool/app.py ^
           image_orient_tool/ui/preview.py image_orient_tool/ui/toast.py ^
           -ts image_orient_tool/i18n/app_en.ts
    2. Qt Linguist (pyside6-linguist) で翻訳内容を確認・編集
    3. pyside6-lrelease で .qm (バイナリ) に変換
       pyside6-lrelease image_orient_tool/i18n/app_en.ts -qm image_orient_tool/i18n/app_en.qm
    ※ build_translations.py で 1回コマンド実行するだけでも 1〜3 をまとめて実行できます。
"""
from PySide6.QtCore import QTranslator, QLocale, QCoreApplication
from PySide6.QtWidgets import QApplication
from .util.paths import resource_path

# サポートしている言語コードと表示名（"auto"はOS言語への自動追従）
# 中国語はSimplified(zh_CN)/Traditional(zh_TW)で文字体系そのものが異なるため、
# 他言語と違い「2文字コード」ではなくロケール全体("zh_CN"/"zh_TW")をコードとして扱う
SUPPORTED_LANGUAGES = {
    "auto": "OSの言語設定に従う (System Default)",
    "ja": "日本語",
    "en": "English",
    "ko": "한국어",
    "de": "Deutsch",
    "ru": "Русский",
    "fr": "Français",
    "zh_CN": "简体中文",
    "zh_TW": "繁體中文（台灣）",
}

# ソース言語（tr()に直書きされている言語）
SOURCE_LANGUAGE = "ja"

# QTranslatorファイルが存在する言語（ソース言語には不要）
TRANSLATABLE_LANGUAGES = ["en", "ko", "de", "ru", "fr", "zh_CN", "zh_TW"]

# OSロケール名(QLocale.system().name())から言語コードへの対応表。
# 中国語圏は地域によって簡体字/繁体字が分かれるため個別にマッピングする。
#   zh_CN, zh_SG (シンガポール): 簡体字
#   zh_TW, zh_HK, zh_MO (香港・マカオ): 繁体字（台湾の表記に統一）
_ZH_REGION_MAP = {
    "zh_CN": "zh_CN",
    "zh_SG": "zh_CN",
    "zh_TW": "zh_TW",
    "zh_HK": "zh_TW",
    "zh_MO": "zh_TW",
}


def resolve_language_code(saved_code: str) -> str:
    """
    設定値("auto"含む)から、実際に使用する言語コードを決定する

    Args:
        saved_code: SettingsManager.load_language() の返り値

    Returns:
        "ja" / "en" / "ko" / "de" / "ru" / "fr" / "zh_CN" / "zh_TW" のいずれか
        (auto指定時はOSの言語から最も近いものを選び、該当なしなら"ja")
    """
    if saved_code and saved_code != "auto" and saved_code in SUPPORTED_LANGUAGES:
        return saved_code

    # OSのロケールから判定 (例: "ja_JP" -> "ja", "zh_TW" -> "zh_TW")
    system_locale = QLocale.system().name()  # 例: "ja_JP", "en_US", "zh_CN", "zh_TW"

    # 中国語は地域(_CN/_TW/_HK/_MO/_SG)まで見て簡体字/繁体字を判定
    if system_locale in _ZH_REGION_MAP:
        return _ZH_REGION_MAP[system_locale]

    lang_prefix = system_locale.split("_")[0].lower()

    # 中国語だが上記マップに無い地域の場合は簡体字をデフォルトにする
    if lang_prefix == "zh":
        return "zh_CN"

    if lang_prefix in SUPPORTED_LANGUAGES:
        return lang_prefix

    return SOURCE_LANGUAGE  # フォールバック: 日本語


def install_translator(app: QApplication, language_code: str) -> QTranslator:
    """
    指定した言語のQTranslatorをQApplicationにインストールする

    Args:
        app: QApplicationインスタンス
        language_code: resolve_language_code() で解決済みの言語コード

    Returns:
        インストールしたQTranslatorインスタンス（保持しておかないとGCされるため、
        呼び出し側でどこかに参照を保持すること）
    """
    translator = QTranslator(app)

    if language_code in TRANSLATABLE_LANGUAGES:
        qm_path = resource_path(f"i18n/app_{language_code}.qm")
        if qm_path.exists():
            translator.load(str(qm_path))
            app.installTranslator(translator)
        else:
            print(
                f"⚠ 翻訳ファイルが見つかりません: {qm_path}\n"
                f"  build_translations.py を実行して .qm ファイルを生成してください。\n"
                f"  日本語表示のまま起動します。"
            )

    return translator
