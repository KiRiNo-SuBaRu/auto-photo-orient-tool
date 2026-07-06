# image_orient_tool.spec
import glob

qm_datas = [(f, 'i18n') for f in glob.glob('image_orient_tool/i18n/*.qm')]

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('image_orient_tool/resources/models/blazeface.onnx', 'resources/models'),
    ] + qm_datas,
    hiddenimports=['onnxruntime', 'cv2', 'PIL', 'shiboken6'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ImageOrientationTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='image_orient_tool/resources/icons/appicon.ico',
)