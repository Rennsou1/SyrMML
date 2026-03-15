#!/usr/bin/env python3

import re

def extract_numbers_from_string(input_string):
    """
    从字符串中提取特定字符后面的数字
    
    参数:
    input_string -- 输入的字符串
    
    返回:
    list -- 提取的数字列表
    """
    # 正则表达式：匹配a, b, c, d, e, f, g, r, +后面的数字
    # 匹配规则：[abcdefgr+]后面跟着一个或多个数字
    pattern = r'[abcdefgr+](\d+)'
    
    # 查找所有匹配
    matches = re.findall(pattern, input_string, re.IGNORECASE)
    
    # 转换为浮点数
    numbers = [float(match) for match in matches]
    
    return numbers

def calculate_reciprocal_sum_reciprocal(numbers):
    """
    计算一系列数字的倒数的和的倒数
    
    参数:
    numbers -- 数字列表
    
    返回:
    float -- 倒数的和的倒数
    """
    if not numbers:
        raise ValueError("输入中没有提取到有效的数字")
    
    # 计算每个数字的倒数，并检查是否为零
    reciprocals = []
    for num in numbers:
        if num == 0:
            raise ZeroDivisionError("提取的数字中包含零，无法计算倒数")
        reciprocals.append(1 / num)
    
    # 计算倒数的和
    sum_reciprocals = sum(reciprocals)
    
    # 计算和的倒数
    result = 1 / sum_reciprocals
    
    return result

def main():
    """
    主函数，处理用户输入和输出
    """
    print("欢迎使用倒数的和的倒数计算器")
    print("请输入包含字母a,b,c,d,e,f,g,r,+及数字的字符串")
    print("例如: a1b2c3d4 或 f12+34g56r78")
    print("将提取这些字符后面的数字，计算倒数的和的倒数")
    
    while True:
        user_input = input("\n请输入字符串 (输入 'exit' 退出): ")
        
        if user_input.lower() == 'exit':
            print("谢谢使用，再见！")
            break
        
        try:
            # 从字符串中提取数字
            numbers = extract_numbers_from_string(user_input)
            
            if not numbers:
                print("错误: 未从输入中提取到任何有效数字")
                print("请确保输入包含a,b,c,d,e,f,g,r,+后面跟着数字")
                continue
            
            # 计算结果
            result = calculate_reciprocal_sum_reciprocal(numbers)
            reciprocal_sum = sum(1/num for num in numbers)
            
            # 输出结果，保留6位小数
            print(f"\n输入字符串: {user_input}")
            print(f"提取的数字: {numbers}")
            print(f"倒数的和: {reciprocal_sum:.6f}")
            print(f"倒数的和的倒数: {result:.6f}")
            
        except ValueError as e:
            print(f"错误: {e}")
        except ZeroDivisionError as e:
            print(f"错误: {e}")
        except Exception as e:
            print(f"意外错误: {e}")

if __name__ == "__main__":
    main()