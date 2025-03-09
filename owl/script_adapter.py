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
    
    # 加载脚本模块
    module_name = script_path.stem
    try:
        # 将脚本目录添加到sys.path
        script_dir = script_path.parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        
        # 读取脚本内容
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查脚本是否有main函数
        has_main = re.search(r'def\s+main\s*\(\s*\)\s*:', content) is not None
        
        if has_main:
            # 如果有main函数，加载模块并调用main
            module = load_module_from_path(module_name, script_path)
            
            # 修改模块中的question变量
            if hasattr(module, "question"):
                setattr(module, "question", question)
            
            # 调用main函数
            if hasattr(module, "main"):
                module.main()
            else:
                print(f"错误: 脚本 {script_path} 中没有main函数")
                sys.exit(1)
        else:
            # 如果没有main函数，直接执行脚本内容
            # 替换question变量
            modified_content = re.sub(
                r'question\s*=\s*["\'].*?["\']', 
                f'question = "{question}"', 
                content
            )
            
            # 执行修改后的脚本
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