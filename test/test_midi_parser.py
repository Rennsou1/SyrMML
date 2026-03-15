#!/usr/bin/env python3
"""
MIDI Parser测试脚本
用于验证MIDI_parser的基本功能
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_midi_parser():
    """测试MIDI_parser的基本功能"""
    print("=== MIDI Parser 测试脚本 ===")
    
    try:
        # 测试导入
        from midi_parser import MidiReader, EventProcessor, MMLConverter, MidiVisualizer, FileUtils
        print("✓ 成功导入所有模块")
        
        # 测试FileUtils
        print("\n=== 测试FileUtils ===")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        midi_files = FileUtils.get_midi_files(current_dir)
        mml_files = FileUtils.get_mml_files(current_dir)
        
        print(f"当前目录MIDI文件数量: {len(midi_files)}")
        print(f"当前目录MML文件数量: {len(mml_files)}")
        
        # 显示找到的MIDI和MML文件
        if midi_files:
            print("找到的MIDI文件:")
            for midi_file in midi_files[:3]:  # 只显示前3个
                print(f"  - {midi_file}")
        
        if mml_files:
            print("找到的MML文件:")
            for mml_file in mml_files[:3]:  # 只显示前3个
                print(f"  - {mml_file}")
        
        print("✓ FileUtils测试通过")
        
        # 测试版本信息
        from midi_parser import __version__, __author__, __description__
        print(f"\n=== 版本信息 ===")
        print(f"版本: {__version__}")
        print(f"作者: {__author__}")
        print(f"描述: {__description__}")
        
        print("\n✓ 所有基本测试通过!")
        print("\n使用示例:")
        print("  python -m midi_parser.examples.basic_parse")
        print("  python -m midi_parser.examples.advanced_analysis")
        print("  python -m midi_parser.examples.midi_to_mml")
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_midi_parser()
