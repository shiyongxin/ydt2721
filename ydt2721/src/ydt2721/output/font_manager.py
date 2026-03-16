"""
中文字体管理器
支持下载、缓存和使用开源中文字体
"""

import os
import sys
import platform
import shutil
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import urlopen
from urllib.error import URLError
import hashlib


class FontManager:
    """开源中文字体管理器"""

    # 字体存储目录
    FONT_DIR = Path.home() / '.ydt2721' / 'fonts'

    # 开源中文字体配置 (Source Han Sans / 思源黑体)
    FONTS = {
        'SourceHanSans': {
            'name': 'Source Han Sans CN (思源黑体)',
            'normal': {
                'url': 'https://github.com/adobe-fonts/source-han-sans/raw/release/SubsetOTF/CN/SourceHanSansCN-Regular.otf',
                'filename': 'SourceHanSansCN-Regular.otf',
                'register_name': 'SourceHanSansCN',
            },
            'bold': {
                'url': 'https://github.com/adobe-fonts/source-han-sans/raw/release/SubsetOTF/CN/SourceHanSansCN-Bold.otf',
                'filename': 'SourceHanSansCN-Bold.otf',
                'register_name': 'SourceHanSansCN-Bold',
            },
        }
    }

    # 系统字体路径（作为备用）
    SYSTEM_FONTS = {
        'Darwin': {  # macOS
            'normal': [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/Library/Fonts/Arial Unicode.ttf',
            ],
            'bold': [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Medium.ttc',
            ],
        },
        'Windows': {  # Windows
            'normal': [
                'C:/Windows/Fonts/msyh.ttc',  # 微软雅黑
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                'C:/Windows/Fonts/simsun.ttc',  # 宋体
            ],
            'bold': [
                'C:/Windows/Fonts/msyhbd.ttc',  # 微软雅黑粗体
                'C:/Windows/Fonts/simhei.ttf',
            ],
        },
        'Linux': {  # Linux
            'normal': [
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            ],
            'bold': [
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
                '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
            ],
        },
    }

    _font_cache = {}

    @classmethod
    def get_font_dir(cls) -> Path:
        """获取字体存储目录"""
        font_dir = cls.FONT_DIR
        font_dir.mkdir(parents=True, exist_ok=True)
        return font_dir

    @classmethod
    def _download_file(cls, url: str, dest_path: Path, description: str = "字体文件") -> bool:
        """
        下载文件到指定路径

        Args:
            url: 下载URL
            dest_path: 目标路径
            description: 文件描述

        Returns:
            是否下载成功
        """
        try:
            print(f"正在下载 {description}...")
            print(f"  URL: {url}")
            print(f"  目标: {dest_path}")

            # 下载文件
            with urlopen(url, timeout=30) as response:
                total_size = int(response.headers.get('content-length', 0))
                chunk_size = 8192
                downloaded = 0

                with open(dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = downloaded / total_size * 100
                            print(f"\r  进度: {progress:.1f}%", end='', file=sys.stderr)

            print(f"\r✅ 下载完成: {dest_path.name}", file=sys.stderr)
            return True

        except URLError as e:
            print(f"\n❌ 下载失败: {e}")
            return False
        except Exception as e:
            print(f"\n❌ 下载失败: {e}")
            # 删除不完整的文件
            if dest_path.exists():
                dest_path.unlink()
            return False

    @classmethod
    def _verify_font_file(cls, font_path: Path) -> bool:
        """
        验证字体文件是否有效

        Args:
            font_path: 字体文件路径

        Returns:
            是否有效
        """
        try:
            # 检查文件大小
            if font_path.stat().st_size < 1024:  # 小于1KB可能无效
                return False

            # 尝试读取文件头
            with open(font_path, 'rb') as f:
                header = f.read(4)

            # 检查字体文件签名
            # TrueType/OpenType: 0x00010000 或 'OTTO'
            # TrueType Collection: 'ttcf'
            valid_signatures = [b'\x00\x01\x00\x00', b'OTTO', b'ttcf']
            return header in valid_signatures

        except Exception:
            return False

    @classmethod
    def download_font(cls, font_key: str = 'SourceHanSans', force: bool = False) -> bool:
        """
        下载开源中文字体

        Args:
            font_key: 字体键名
            force: 是否强制重新下载

        Returns:
            是否下载成功
        """
        if font_key not in cls.FONTS:
            print(f"❌ 未找到字体: {font_key}")
            return False

        font_config = cls.FONTS[font_key]
        font_dir = cls.get_font_dir()

        success = True

        # 下载普通字体
        normal_config = font_config['normal']
        normal_path = font_dir / normal_config['filename']

        if force or not normal_path.exists() or not cls._verify_font_file(normal_path):
            if not cls._download_file(normal_config['url'], normal_path, f"{font_config['name']} (普通)"):
                success = False

        # 下载粗体字体
        bold_config = font_config['bold']
        bold_path = font_dir / bold_config['filename']

        if force or not bold_path.exists() or not cls._verify_font_file(bold_path):
            if not cls._download_file(bold_config['url'], bold_path, f"{font_config['name']} (粗体)"):
                success = False

        return success

    @classmethod
    def _find_system_font(cls, font_type: str = 'normal') -> Optional[Tuple[str, int]]:
        """
        查找系统中的中文字体

        Args:
            font_type: 字体类型 ('normal' 或 'bold')

        Returns:
            (字体路径, subfontIndex) 或 None
        """
        system_name = platform.system()

        if system_name not in cls.SYSTEM_FONTS:
            return None

        font_paths = cls.SYSTEM_FONTS[system_name].get(font_type, [])

        for font_path in font_paths:
            if os.path.exists(font_path):
                # TTC 文件需要指定子字体索引
                if font_path.endswith('.ttc'):
                    # macOS PingFang: 0=SC, 1=TC
                    # Windows 微软雅黑: 0=正常, 1=粗体
                    if font_type == 'bold':
                        return (font_path, 1)
                    return (font_path, 0)
                return (font_path, None)

        return None

    @classmethod
    def get_font_path(cls, font_type: str = 'normal') -> Optional[Tuple[str, Optional[int]]]:
        """
        获取中文字体路径

        优先使用已下载的开源字体，如果没有则使用系统字体

        Args:
            font_type: 字体类型 ('normal' 或 'bold')

        Returns:
            (字体路径, subfontIndex) 或 None
        """
        # 检查缓存
        cache_key = f'{platform.system()}_{font_type}'
        if cache_key in cls._font_cache:
            return cls._font_cache[cache_key]

        font_dir = cls.get_font_dir()

        # 尝试使用下载的开源字体
        for font_key, font_config in cls.FONTS.items():
            config = font_config.get(font_type)
            if config:
                font_path = font_dir / config['filename']
                if font_path.exists() and cls._verify_font_file(font_path):
                    result = (str(font_path), None)
                    cls._font_cache[cache_key] = result
                    return result

        # 回退到系统字体
        result = cls._find_system_font(font_type)
        if result:
            cls._font_cache[cache_key] = result
            return result

        return None

    @classmethod
    def get_font_info(cls) -> dict:
        """
        获取字体状态信息

        Returns:
            字体状态字典
        """
        font_dir = cls.get_font_dir()
        system = platform.system()

        info = {
            'system': system,
            'font_dir': str(font_dir),
            'downloaded_fonts': [],
            'system_fonts': {
                'normal': cls._find_system_font('normal') is not None,
                'bold': cls._find_system_font('bold') is not None,
            },
        }

        # 检查已下载的字体
        for font_key, font_config in cls.FONTS.items():
            for font_type in ['normal', 'bold']:
                config = font_config.get(font_type)
                if config:
                    font_path = font_dir / config['filename']
                    info['downloaded_fonts'].append({
                        'key': f"{font_key}_{font_type}",
                        'path': str(font_path),
                        'exists': font_path.exists(),
                        'valid': font_path.exists() and cls._verify_font_file(font_path),
                    })

        return info

    @classmethod
    def clear_cache(cls) -> bool:
        """
        清除字体缓存

        Returns:
            是否成功
        """
        cls._font_cache.clear()
        return True

    @classmethod
    def remove_downloaded_fonts(cls) -> bool:
        """
        删除已下载的字体文件

        Returns:
            是否成功
        """
        font_dir = cls.get_font_dir()

        try:
            for font_key, font_config in cls.FONTS.items():
                for font_type in ['normal', 'bold']:
                    config = font_config.get(font_type)
                    if config:
                        font_path = font_dir / config['filename']
                        if font_path.exists():
                            font_path.unlink()

            # 尝试删除空目录
            try:
                if font_dir.exists() and not list(font_dir.iterdir()):
                    font_dir.rmdir()
                    parent = font_dir.parent
                    if parent.exists() and not list(parent.iterdir()):
                        parent.rmdir()
            except OSError:
                pass

            cls.clear_cache()
            return True

        except Exception as e:
            print(f"❌ 删除字体失败: {e}")
            return False


def setup_chinese_fonts(force: bool = False) -> bool:
    """
    设置中文字体（首次使用时调用）

    Args:
        force: 是否强制重新下载

    Returns:
        是否成功
    """
    print("=" * 50)
    print("YDT 2721 中文字体设置")
    print("=" * 50)

    info = FontManager.get_font_info()
    print(f"\n系统: {info['system']}")
    print(f"字体目录: {info['font_dir']}")

    # 检查系统字体
    has_system_font = info['system_fonts']['normal'] or info['system_fonts']['bold']
    if has_system_font:
        print("✓ 检测到系统中文字体")

    # 检查已下载字体
    downloaded = [f for f in info['downloaded_fonts'] if f['exists'] and f['valid']]
    if downloaded and not force:
        print(f"✓ 已下载 {len(downloaded)} 个字体文件")
        print("\n使用现有字体，无需重新下载。")
        return True

    if force:
        print("\n强制重新下载字体...")

    # 下载字体
    print("\n开始下载开源中文字体...")
    success = FontManager.download_font(force=force)

    if success:
        print("\n✅ 字体设置完成！")
    else:
        print("\n⚠️ 字体下载失败，将使用系统字体（如果可用）。")

    return success


if __name__ == '__main__':
    # 命令行测试
    import argparse

    parser = argparse.ArgumentParser(description='YDT 2721 中文字体管理器')
    parser.add_argument('--setup', action='store_true', help='下载并设置中文字体')
    parser.add_argument('--force', action='store_true', help='强制重新下载')
    parser.add_argument('--info', action='store_true', help='显示字体信息')
    parser.add_argument('--remove', action='store_true', help='删除已下载的字体')

    args = parser.parse_args()

    if args.setup or args.force:
        setup_chinese_fonts(force=args.force)
    elif args.info:
        info = FontManager.get_font_info()
        print("\n字体状态:")
        print(f"  系统: {info['system']}")
        print(f"  字体目录: {info['font_dir']}")
        print(f"  系统字体: 正常={info['system_fonts']['normal']}, 粗体={info['system_fonts']['bold']}")
        print("\n已下载字体:")
        for font in info['downloaded_fonts']:
            status = "✓" if font['valid'] else "✗"
            print(f"  {status} {font['key']}: {font['path']}")
    elif args.remove:
        if FontManager.remove_downloaded_fonts():
            print("✅ 已删除下载的字体文件")
        else:
            print("❌ 删除失败")
    else:
        parser.print_help()
