#!/usr/bin/env python3
"""
创建测试用的MIDI文件
用于测试示例脚本
"""

import mido

def create_test_midi():
    """创建一个简单的测试MIDI文件"""
    # 创建MIDI文件（类型1，多轨道同步）
    midi = mido.MidiFile(type=1)
    
    # 创建音轨1: 元数据
    track1 = mido.MidiTrack()
    midi.tracks.append(track1)
    
    # 添加元事件
    track1.append(mido.MetaMessage('track_name', name='Meta Track', time=0))
    track1.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120), time=0))
    track1.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    track1.append(mido.MetaMessage('key_signature', key='C', time=0))
    
    # 创建音轨2: 旋律
    track2 = mido.MidiTrack()
    midi.tracks.append(track2)
    track2.append(mido.MetaMessage('track_name', name='Melody Track', time=0))
    
    # 添加乐器变更（钢琴）
    track2.append(mido.Message('program_change', program=0, time=0))
    
    # 简单的C大调琶音
    notes = [60, 62, 64, 65, 67, 69, 71, 72]  # C4到C5
    
    for i, note in enumerate(notes):
        # 音符开启
        track2.append(mido.Message('note_on', note=note, velocity=64, time=480 if i > 0 else 0))
        # 音符关闭
        track2.append(mido.Message('note_off', note=note, velocity=64, time=480))
    
    # 添加结束标记
    track2.append(mido.MetaMessage('end_of_track', time=0))
    
    # 保存文件
    output_file = "example.mid"
    midi.save(output_file)
    print(f"测试MIDI文件创建成功: {output_file}")
    print(f"文件格式: {midi.type}")
    print(f"轨道数量: {len(midi.tracks)}")
    print(f"时间分辨率: {midi.ticks_per_beat} ticks/beat")
    
    return output_file

if __name__ == "__main__":
    create_test_midi()
