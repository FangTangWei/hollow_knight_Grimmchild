# -*- mode: python ; coding: utf-8 -*-
# =============================================================
#  Grimmchild 桌面宠物 打包配置（PyInstaller spec）
#  产物: 单文件 exe，约 23MB，无控制台窗口，图标 FlameConsumed.ico
#  用法: python -m PyInstaller Grimmchild.spec --clean --noconfirm
# =============================================================
import os

# 项目根目录（注意: 含中文/空格路径时本文件必须用 UTF-8 编码保存）
ROOT = r'需要打包的文件所在路径'

a = Analysis(
    [os.path.join(ROOT, 'Grimmchild.py')],   # 入口脚本
    pathex=[ROOT],
    binaries=[],
    datas=[                                   # 程序运行时需要的资源目录
        (os.path.join(ROOT, 'Grimmchild Anim'), 'Grimmchild Anim'),
        (os.path.join(ROOT, 'AudioClip'), 'AudioClip'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[                                # 排除用不到的 Python 模块（省体积）
        # 仅被 urllib/email 等 stdlib 链间接引用，程序运行时从不 import
        'ssl', '_ssl', 'hashlib', '_hashlib',
        'urllib.request', 'http.client', 'smtplib', 'ftplib', 'poplib', 'imaplib',
        'nntplib', 'telnetlib', 'email',
    ],
    noarchive=False,
    optimize=0,
)

# =============================================================
#  体积裁剪: 纯 Widgets 桌面宠物用不到的 DLL / 插件 / 翻译全部过滤
#  原理: Analysis 收集完后，在组装 EXE 之前手工过滤 a.binaries / a.datas
# =============================================================

_BAD_BINARY_FRAGMENTS = (
    # Qt 的 OpenGL/ANGLE 软件渲染库（~27MB），Widgets 应用用不到
    'opengl32sw.dll', 'libegl.dll', 'libglesv2.dll', 'd3dcompiler',
    # OpenSSL（Qt 的 + Python 的），本地文件播放用不到 SSL
    'libcrypto', 'libssl',
    # 被已删除插件的依赖链带进来的 Qt 模块
    'qt5quick.dll', 'qt5qml.dll', 'qt5qmlmodels.dll',
    'qt5svg.dll', 'qt5websockets.dll', 'qt5dbus.dll',
    # 图片格式插件（PNG 已内置于 Qt5Gui.dll，无需外部插件）
    'plugins/imageformats/',
    'plugins/iconengines/',
    # 多余的平台插件，只保留 qwindows.dll
    'plugins/platforms/qminimal.dll',
    'plugins/platforms/qoffscreen.dll',
    'plugins/platforms/qwebgl.dll',
    # 其它用不到的功能插件
    'plugins/audio/',            # QAudioOutput 用不到（QMediaPlayer 走 mediaservice）
    'plugins/generic/',
    'plugins/geometryloaders/', 'plugins/sceneparsers/',
    'plugins/assetimporters/', 'plugins/geoservices/', 'plugins/position/',
    'plugins/renderers/', 'plugins/sensors/', 'plugins/sensorgestures/',
    'plugins/sqldrivers/', 'plugins/texttospeech/', 'plugins/webview/',
    'plugins/platformthemes/', 'plugins/playlistformats/',
)

def _drop_binary(entry):
    """entry 形如 (目标路径, 源文件路径, 类型码)"""
    dest = entry[0].lower().replace('\\', '/')
    return any(frag in dest for frag in _BAD_BINARY_FRAGMENTS)

def _drop_data(entry):
    # 翻译文件: 程序没有安装 QTranslator，全部 .qm 都是死重（~8MB）
    dest = entry[0].lower().replace('\\', '/')
    return dest.startswith('pyqt5/qt5/translations/')

a.binaries = [b for b in a.binaries if not _drop_binary(b)]
a.datas = [d for d in a.datas if not _drop_data(d)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Grimmchild',                        # 生成的 exe 文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                                # 本方案不依赖 UPX（PyInstaller 6.x 自带 zlib 压缩）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                            # 关键: False = 窗口程序，无命令提示符窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(ROOT, 'FlameConsumed.ico')],   # exe 图标
)
