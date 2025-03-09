import os
import sys
import importlib.util
import re
from pathlib import Path

def load_module_from_path(module_name, file_path):
    """从文件路径加载Python模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def run_script_with_env_question(script_name):
    """使用环境变量中的问题运行脚本"""
    # 获取环境变量中的问题
    question = os.environ.get("OWL_QUESTION")
    if not question:
        print("错误: 未设置OWL_QUESTION环境变量")
        sys.exit(1)
    
    # 脚本路径
    script_path = Path(script_name).resolve()
    if not script_path.exists():
        print(f"错误: 脚本 {script_path} 不存在")
        sys.exit(1)
    
    # 读取脚本内容
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查脚本是否有main函数
    has_main = re.search(r'def\s+main\s*\(\s*\)\s*:', content) is not None
    
    # 尝试查找并替换question变量
    # 匹配多种可能的question定义模式
    patterns = [
        r'question\s*=\s*["\'].*?["\']',  # 简单字符串赋值
        r'question\s*=\s*\(\s*["\'].*?["\']\s*\)',  # 带括号的字符串赋值
        r'question\s*=\s*f["\'].*?["\']',  # f-string赋值
        r'question\s*=\s*r["\'].*?["\']',  # 原始字符串赋值
    ]
    
    question_replaced = False
    for pattern in patterns:
        if re.search(pattern, content):
            # 转义问题中的特殊字符
            escaped_question = question.replace("\\", "\\\\").replace("\"", "\\\"").replace("'", "\\'")
            # 替换问题
            modified_content = re.sub(
                pattern, 
                f'question = "{escaped_question}"', 
                content
            )
            question_replaced = True
            break
    
    if not question_replaced:
        # 如果没有找到question变量，尝试在main函数前插入
        if has_main:
            # 在main函数前插入question变量
            main_match = re.search(r'def\s+main\s*\(\s*\)\s*:', content)
            if main_match:
                insert_pos = main_match.start()
                # 转义问题中的特殊字符
                escaped_question = question.replace("\\", "\\\\").replace("\"", "\\\"").replace("'", "\\'")
                modified_content = content[:insert_pos] + f'\n# 用户输入的问题\nquestion = "{escaped_question}"\n\n' + content[insert_pos:]
                question_replaced = True
    
    if not question_replaced:
        # 如果仍然无法替换，尝试在文件末尾添加代码来使用用户的问题
        modified_content = content + f'\n\n# 用户输入的问题\nquestion = "{question}"\n\n'
        modified_content += '''
# 如果脚本中有construct_society函数，使用用户问题运行
if "construct_society" in globals():
    try:
        society = construct_society(question)
        from utils import run_society
        answer, chat_history, token_count = run_society(society)
        print(f"Answer: {answer}")
    except Exception as e:
        print(f"运行时出错: {e}")
        import traceback
        traceback.print_exc()
'''
    
    # 执行修改后的脚本
    try:
        # 将脚本目录添加到sys.path
        script_dir = script_path.parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        
        if has_main:
            # 如果有main函数，加载模块并调用main
            # 创建临时文件
            temp_script_path = script_path.with_name(f"temp_{script_path.name}")
            with open(temp_script_path, "w", encoding="utf-8") as f:
                f.write(modified_content)
            
            try:
                # 加载临时模块
                module_name = f"temp_{script_path.stem}"
                module = load_module_from_path(module_name, temp_script_path)
                
                # 调用main函数
                if hasattr(module, "main"):
                    module.main()
                else:
                    print(f"错误: 脚本 {script_path} 中没有main函数")
                    sys.exit(1)
            finally:
                # 删除临时文件
                if temp_script_path.exists():
                    temp_script_path.unlink()
        else:
            # 如果没有main函数，直接执行修改后的脚本
            exec(modified_content, {"__file__": str(script_path)})
    
    except Exception as e:
        print(f"执行脚本时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python script_adapter.py <script_path>")
        sys.exit(1)
    
    # 运行指定的脚本
    run_script_with_env_question(sys.argv[1]) 