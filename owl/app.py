import os
import sys
import gradio as gr
import subprocess
import threading
import time
from datetime import datetime
import queue
import re
from pathlib import Path
import json

# 设置日志队列
log_queue = queue.Queue()

# 脚本选项
SCRIPTS = {
    "Qwen Mini (中文)": "run_qwen_mini_zh.py",
    "Qwen": "run_qwen.py",
    "Mini": "run_mini.py",
    "DeepSeek": "run_deepseek.py",
    "默认": "run.py",
    "GAIA Roleplaying": "run_gaia_roleplaying.py"
}

# 脚本描述
SCRIPT_DESCRIPTIONS = {
    "Qwen Mini (中文)": "使用阿里云Qwen模型的中文版本，适合中文问答和任务",
    "Qwen": "使用阿里云Qwen模型，支持多种工具和功能",
    "Mini": "轻量级版本，使用OpenAI GPT-4o模型",
    "DeepSeek": "使用DeepSeek模型，适合复杂推理任务",
    "默认": "默认OWL实现，使用OpenAI GPT-4o模型和全套工具",
    "GAIA Roleplaying": "GAIA基准测试实现，用于评估模型能力"
}

def get_script_info(script_name):
    """获取脚本的详细信息"""
    return SCRIPT_DESCRIPTIONS.get(script_name, "无描述信息")

def run_script(script_dropdown, question, progress=gr.Progress()):
    """运行选定的脚本并返回输出"""
    script_name = SCRIPTS[script_dropdown]
    
    if not question.strip():
        return "请输入问题！", "", "", "", None
    
    # 清空日志队列
    while not log_queue.empty():
        log_queue.get()
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 创建带时间戳的日志文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{script_name.replace('.py', '')}_{timestamp}.log"
    
    # 构建命令
    cmd = [sys.executable, os.path.join("owl", "script_adapter.py"), os.path.join("owl", script_name)]
    
    # 创建环境变量副本并添加问题
    env = os.environ.copy()
    env["OWL_QUESTION"] = question
    
    # 启动进程
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env
    )
    
    # 创建线程来读取输出
    def read_output():
        with open(log_file, "w", encoding="utf-8") as f:
            for line in iter(process.stdout.readline, ""):
                if line:
                    # 写入日志文件
                    f.write(line)
                    f.flush()
                    # 添加到队列
                    log_queue.put(line)
    
    # 启动读取线程
    threading.Thread(target=read_output, daemon=True).start()
    
    # 收集日志
    logs = []
    progress(0, desc="正在运行...")
    
    # 等待进程完成或超时
    start_time = time.time()
    timeout = 1800  # 30分钟超时
    
    while process.poll() is None:
        # 检查是否超时
        if time.time() - start_time > timeout:
            process.terminate()
            log_queue.put("执行超时，已终止进程\n")
            break
        
        # 从队列获取日志
        while not log_queue.empty():
            log = log_queue.get()
            logs.append(log)
        
        # 更新进度
        elapsed = time.time() - start_time
        progress(min(elapsed / 300, 0.99), desc="正在运行...")
        
        # 短暂休眠以减少CPU使用
        time.sleep(0.1)
        
        # 每秒更新一次日志显示
        yield status_message(process), extract_answer(logs), "".join(logs), str(log_file), None
    
    # 获取剩余日志
    while not log_queue.empty():
        logs.append(log_queue.get())
    
    # 提取聊天历史（如果有）
    chat_history = extract_chat_history(logs)
    
    # 返回最终状态和日志
    return status_message(process), extract_answer(logs), "".join(logs), str(log_file), chat_history

def status_message(process):
    """根据进程状态返回状态消息"""
    if process.poll() is None:
        return "⏳ 正在运行..."
    elif process.returncode == 0:
        return "✅ 执行成功"
    else:
        return f"❌ 执行失败 (返回码: {process.returncode})"

def extract_answer(logs):
    """从日志中提取答案"""
    answer = ""
    for log in logs:
        if "Answer:" in log:
            answer = log.split("Answer:", 1)[1].strip()
            break
    return answer

def extract_chat_history(logs):
    """尝试从日志中提取聊天历史"""
    try:
        for i, log in enumerate(logs):
            if "chat_history" in log:
                # 尝试找到JSON格式的聊天历史
                start_idx = log.find("[")
                if start_idx != -1:
                    # 尝试解析JSON
                    json_str = log[start_idx:].strip()
                    # 查找下一行中可能的结束括号
                    if json_str[-1] != "]" and i+1 < len(logs):
                        for j in range(i+1, min(i+10, len(logs))):
                            end_idx = logs[j].find("]")
                            if end_idx != -1:
                                json_str += logs[j][:end_idx+1]
                                break
                    
                    try:
                        chat_data = json.loads(json_str)
                        # 格式化为Gradio聊天组件可用的格式
                        formatted_chat = []
                        for msg in chat_data:
                            if "role" in msg and "content" in msg:
                                role = "用户" if msg["role"] == "user" else "助手"
                                formatted_chat.append([role, msg["content"]])
                        return formatted_chat
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    return None

def modify_script(script_name, question):
    """修改脚本以使用提供的问题"""
    script_path = os.path.join("owl", script_name)
    
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 查找并替换问题变量
    if "question = " in content:
        # 使用正则表达式替换问题字符串
        modified_content = re.sub(
            r'question\s*=\s*["\'].*?["\']', 
            f'question = "{question}"', 
            content
        )
        
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
        
        return True
    
    return False

def create_ui():
    """创建Gradio界面"""
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as app:
        gr.Markdown(
            """
            # 🦉 OWL 智能助手运行平台
            
            选择一个模型并输入您的问题，系统将运行相应的脚本并显示结果。
            """
        )
        
        with gr.Row():
            with gr.Column(scale=1):
                script_dropdown = gr.Dropdown(
                    choices=list(SCRIPTS.keys()),
                    value=list(SCRIPTS.keys())[0],
                    label="选择模型"
                )
                
                script_info = gr.Textbox(
                    value=get_script_info(list(SCRIPTS.keys())[0]),
                    label="模型描述",
                    interactive=False
                )
                
                script_dropdown.change(
                    fn=lambda x: get_script_info(x),
                    inputs=script_dropdown,
                    outputs=script_info
                )
                
                question_input = gr.Textbox(
                    lines=5,
                    placeholder="请输入您的问题...",
                    label="问题"
                )
                
                run_button = gr.Button("运行", variant="primary")
            
            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.TabItem("结果"):
                        status_output = gr.Textbox(label="状态")
                        answer_output = gr.Textbox(label="回答", lines=10)
                        log_file_output = gr.Textbox(label="日志文件路径")
                    
                    with gr.TabItem("运行日志"):
                        log_output = gr.Textbox(label="完整日志", lines=25)
                    
                    with gr.TabItem("聊天历史"):
                        chat_output = gr.Chatbot(label="对话历史")
        
        run_button.click(
            fn=run_script,
            inputs=[
                script_dropdown,
                question_input
            ],
            outputs=[status_output, answer_output, log_output, log_file_output, chat_output],
            show_progress=True
        )
        
        # 示例问题
        examples = [
            ["Qwen Mini (中文)", "打开小红书上浏览推荐栏目下的前三个笔记内容，不要登陆，之后给我一个总结报告"],
            ["Mini", "What was the volume in m^3 of the fish bag that was calculated in the University of Leicester paper `Can Hiccup Supply Enough Fish to Maintain a Dragon's Diet?`"],
            ["默认", "What is the current weather in New York?"]
        ]
        
        gr.Examples(
            examples=examples,
            inputs=[script_dropdown, question_input]
        )
        
        # 添加页脚
        gr.Markdown(
            """
            ### 📝 使用说明
            
            - 选择一个模型并输入您的问题
            - 点击"运行"按钮开始执行
            - 在"结果"标签页查看执行状态和回答
            - 在"运行日志"标签页查看完整日志
            - 在"聊天历史"标签页查看对话历史（如果有）
            
            ### ⚠️ 注意事项
            
            - 运行某些模型可能需要API密钥，请确保在`.env`文件中设置了相应的环境变量
            - 某些脚本可能需要较长时间运行，请耐心等待
            - 如果运行超过30分钟，进程将自动终止
            """
        )
    
    return app

if __name__ == "__main__":
    # 创建并启动应用
    app = create_ui()
    app.queue().launch(share=True) 