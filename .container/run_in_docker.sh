#!/bin/bash

# 定义配置变量
SERVICE_NAME="owl"
PYTHON_CMD="xvfb-python"
MAX_WAIT_SECONDS=60
CHECK_INTERVAL_SECONDS=2

# 检测操作系统类型
OS_TYPE=$(uname -s)
echo "检测到操作系统: $OS_TYPE"

# 检查是否提供了查询参数
if [ $# -lt 1 ]; then
    echo "用法: ./run_in_docker.sh [脚本名称] '你的问题'"
    echo "例如: ./run_in_docker.sh run.py '什么是人工智能？'"
    echo "或者: ./run_in_docker.sh run_deepseek_example.py '什么是人工智能？'"
    echo "如果不指定脚本名称，默认使用 run.py"
    exit 1
fi

# 判断第一个参数是否是脚本名称
if [[ $1 == *.py ]]; then
    SCRIPT_NAME="$1"
    # 如果提供了第二个参数，则为查询内容
    if [ $# -ge 2 ]; then
        QUERY="$2"
    else
        echo "请提供查询参数，例如: ./run_in_docker.sh $SCRIPT_NAME '你的问题'"
        exit 1
    fi
else
    # 如果第一个参数不是脚本名称，则默认使用 run.py
    SCRIPT_NAME="run.py"
    QUERY="$1"
fi

# 检查脚本是否存在
if [ ! -f "owl/$SCRIPT_NAME" ]; then
    echo "错误: 脚本 'owl/$SCRIPT_NAME' 不存在"
    echo "可用的脚本有:"
    if [[ "$OS_TYPE" == MINGW* ]] || [[ "$OS_TYPE" == CYGWIN* ]] || [[ "$OS_TYPE" == MSYS* ]]; then
        find owl -name "*.py" | grep -v "__" | sed 's/\\/\//g'
    else
        ls -1 owl/*.py | grep -v "__"
    fi
    exit 1
fi

echo "使用脚本: $SCRIPT_NAME"
echo "查询内容: $QUERY"

# 从docker-compose.yml获取服务名称（如果文件存在）
if [ -f ".container/docker-compose.yml" ]; then
    DETECTED_SERVICE=$(grep -E "^  [a-zA-Z0-9_-]*:" .container/docker-compose.yml | head -1 | sed 's/^  \(.*\):.*/\1/')
    if [ ! -z "$DETECTED_SERVICE" ]; then
        SERVICE_NAME="$DETECTED_SERVICE"
        echo "从docker-compose.yml检测到服务名称: $SERVICE_NAME"
    fi
fi

# 检查Docker Compose命令
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "错误: 未找到Docker Compose命令"
    exit 1
fi

# 确保Docker容器正在运行
CONTAINER_RUNNING=$($COMPOSE_CMD ps | grep -c "$SERVICE_NAME.*Up" || true)
if [ "$CONTAINER_RUNNING" -eq 0 ]; then
    echo "启动Docker容器..."
    $COMPOSE_CMD up -d
    
    # 使用循环检查容器是否就绪
    echo "等待容器启动..."
    TOTAL_WAIT=0
    
    while [ $TOTAL_WAIT -lt $MAX_WAIT_SECONDS ]; do
        sleep $CHECK_INTERVAL_SECONDS
        TOTAL_WAIT=$((TOTAL_WAIT + CHECK_INTERVAL_SECONDS))
        
        CONTAINER_RUNNING=$($COMPOSE_CMD ps | grep -c "$SERVICE_NAME.*Up" || true)
        if [ "$CONTAINER_RUNNING" -gt 0 ]; then
            echo "容器已就绪，共等待了 $TOTAL_WAIT 秒"
            break
        else
            echo "容器尚未就绪，已等待 $TOTAL_WAIT 秒，继续等待..."
        fi
    done
    
    if [ "$CONTAINER_RUNNING" -eq 0 ]; then
        echo "错误：容器启动超时，已等待 $MAX_WAIT_SECONDS 秒"
        echo "请检查Docker容器状态：$COMPOSE_CMD ps"
        exit 1
    fi
fi

# 检查容器中是否存在指定的Python命令
echo "检查容器中的命令..."
if ! $COMPOSE_CMD exec -T $SERVICE_NAME which $PYTHON_CMD &> /dev/null; then
    echo "警告：容器中未找到 $PYTHON_CMD 命令，尝试使用python替代"
    PYTHON_CMD="python"
    
    # 检查python命令是否存在
    if ! $COMPOSE_CMD exec -T $SERVICE_NAME which python &> /dev/null; then
        echo "错误：容器中未找到python命令"
        echo "请检查容器配置"
        exit 1
    fi
fi

# 在容器中运行指定的脚本，传递查询参数
echo "在Docker容器中使用 $PYTHON_CMD 运行脚本..."

# 根据操作系统类型执行不同的命令
if [[ "$OS_TYPE" == MINGW* ]] || [[ "$OS_TYPE" == CYGWIN* ]] || [[ "$OS_TYPE" == MSYS* ]]; then
    # Windows可能需要特殊处理引号
    winpty $COMPOSE_CMD exec -T $SERVICE_NAME $PYTHON_CMD $SCRIPT_NAME "$QUERY"
    RESULT=$?
else
    # macOS 或 Linux
    $COMPOSE_CMD exec -T $SERVICE_NAME $PYTHON_CMD $SCRIPT_NAME "$QUERY"
    RESULT=$?
fi

# 检查命令执行结果
if [ $RESULT -eq 0 ]; then
    echo "查询完成！"
else
    echo "查询执行失败，请检查错误信息。"
fi 