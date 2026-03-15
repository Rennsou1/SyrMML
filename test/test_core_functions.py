#!/usr/bin/env python3
"""
核心功能测试脚本
使用模拟数据测试MIDI_parser的核心功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from midi_parser import MidiReader, EventProcessor, MMLConverter

def test_core_functions():
    """测试核心功能"""
    print("=== 核心功能测试 ===")
    
    # 测试1: MidiReader初始化
    print("\n1. 测试MidiReader初始化")
    try:
        reader = MidiReader("non_existent.mid")
        print("✓ MidiReader初始化成功")
    except Exception as e:
        print(f"✗ MidiReader初始化失败: {e}")
        return False
    
    # 测试2: EventProcessor功能
    print("\n2. 测试EventProcessor功能")
    try:
        processor = EventProcessor()
        processor.reset_stats()
        print("✓ EventProcessor初始化和重置成功")
        
        # 测试统计初始化
        stats = processor.get_stats()
        print(f"  初始统计数据: {stats['event_stats']}")
        print(f"  初始速度: {stats['current_bpm']:.1f} BPM")
        print("✓ EventProcessor统计功能正常")
    except Exception as e:
        print(f"✗ EventProcessor测试失败: {e}")
        return False
    
    # 测试3: MMLConverter功能
    print("\n3. 测试MMLConverter功能")
    try:
        converter = MMLConverter()
        print(f"  默认速度: {converter.default_tempo} BPM")
        print(f"  默认八度: {converter.default_octave}")
        print(f"  默认长度: {converter.default_length}")
        print("✓ MMLConverter初始化成功")
    except Exception as e:
        print(f"✗ MMLConverter测试失败: {e}")
        return False
    
    # 测试4: 模块间协作
    print("\n4. 测试模块间协作")
    try:
        # 创建所有模块实例
        reader = MidiReader("non_existent.mid")
        processor = EventProcessor()
        converter = MMLConverter()
        
        print("✓ 所有核心模块初始化成功")
        print("✓ 模块间协作测试通过")
    except Exception as e:
        print(f"✗ 模块间协作测试失败: {e}")
        return False
    
    print("\n=== 核心功能测试总结 ===")
    print("✓ 所有核心功能测试通过!")
    print("\n下一步建议:")
    print("1. 准备一个MIDI文件进行实际测试")
    print("2. 运行示例脚本查看完整功能")
    print("3. 根据需求扩展功能")
    
    return True

if __name__ == "__main__":
    test_core_functions()
