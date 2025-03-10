@echo off
setlocal enabledelayedexpansion

REM 定义配置变量 | Define configuration variables
set SERVICE_NAME=owl
set PYTHON_CMD=xvfb-python
set MAX_WAIT_SECONDS=60
set CHECK_INTERVAL_SECONDS=2

REM 检查参数 | Check parameters
if "%~1"=="" (
    echo 用法 | Usage: run_in_docker.bat [脚本名称 | script name] "你的问题 | your question"
    echo 例如 | Example: run_in_docker.bat run.py "什么是人工智能？ | What is artificial intelligence?"
    echo 或者 | Or: run_in_docker.bat run_deepseek_example.py "什么是人工智能？ | What is artificial intelligence?"
    echo 如果不指定脚本名称，默认使用 run.py | If script name is not specified, run.py will be used by default
    exit /b 1
)

REM 判断第一个参数是否是脚本名称 | Determine if the first parameter is a script name
set SCRIPT_NAME=%~1
set QUERY=%~2

if "!SCRIPT_NAME:~-3!"==".py" (
    REM 如果提供了第二个参数，则为查询内容 | If a second parameter is provided, it's the query content
    if "!QUERY!"=="" (
        echo 请提供查询参数，例如 | Please provide query parameter, e.g.: run_in_docker.bat !SCRIPT_NAME! "你的问题 | your question"
        exit /b 1
    )
) else (
    REM 如果第一个参数不是脚本名称，则默认使用 run.py | If the first parameter is not a script name, use run.py by default
    set QUERY=!SCRIPT_NAME!
    set SCRIPT_NAME=run.py
)

REM 检查脚本是否存在 | Check if the script exists
if not exist "owl\!SCRIPT_NAME!" (
    echo 错误 | Error: 脚本 | Script 'owl\!SCRIPT_NAME!' 不存在 | does not exist
    echo 可用的脚本有 | Available scripts:
    dir /b owl\*.py | findstr /v "__"
    exit /b 1
)

echo 使用脚本 | Using script: !SCRIPT_NAME!
echo 查询内容 | Query content: !QUERY!

REM 从docker-compose.yml获取服务名称（如果文件存在） | Get service name from docker-compose.yml (if file exists)
if exist ".container\docker-compose.yml" (
    for /f "tokens=*" %%a in ('findstr /r "^  [a-zA-Z0-9_-]*:" .container\docker-compose.yml') do (
        set line=%%a
        set service=!line:~2,-1!
        if not "!service!"=="" (
            REM 使用第一个找到的服务名称 | Use the first service name found
            set SERVICE_NAME=!service!
            echo 从docker-compose.yml检测到服务名称 | Detected service name from docker-compose.yml: !SERVICE_NAME!
            goto :found_service
        )
    )
)
:found_service

REM 确保Docker容器正在运行 | Ensure Docker container is running
docker-compose ps | findstr "!SERVICE_NAME!.*Up" > nul
if errorlevel 1 (
    echo 启动Docker容器... | Starting Docker container...
    docker-compose up -d
    
    REM 使用循环检查容器是否就绪 | Use loop to check if container is ready
    echo 等待容器启动... | Waiting for container to start...
    set /a total_wait=0
    
    :wait_loop
    timeout /t !CHECK_INTERVAL_SECONDS! /nobreak > nul
    set /a total_wait+=!CHECK_INTERVAL_SECONDS!
    
    docker-compose ps | findstr "!SERVICE_NAME!.*Up" > nul
    if errorlevel 1 (
        if !total_wait! LSS !MAX_WAIT_SECONDS! (
            echo 容器尚未就绪，已等待!total_wait!秒，继续等待... | Container not ready yet, waited for !total_wait! seconds, continuing to wait...
            goto :wait_loop
        ) else (
            echo 错误 | Error：容器启动超时，已等待!MAX_WAIT_SECONDS!秒 | Container startup timeout, waited for !MAX_WAIT_SECONDS! seconds
            echo 请检查Docker容器状态 | Please check Docker container status：docker-compose ps
            exit /b 1
        )
    ) else (
        echo 容器已就绪，共等待了!total_wait!秒 | Container is ready, waited for !total_wait! seconds in total
    )
)

REM 检查容器中是否存在xvfb-python命令 | Check if xvfb-python command exists in container
echo 检查容器中的命令... | Checking commands in container...
docker-compose exec -T !SERVICE_NAME! which !PYTHON_CMD! > nul 2>&1
if errorlevel 1 (
    echo 警告 | Warning：容器中未找到!PYTHON_CMD!命令，尝试使用python替代 | !PYTHON_CMD! command not found in container, trying to use python instead
    set PYTHON_CMD=python
    
    REM 检查python命令是否存在 | Check if python command exists
    docker-compose exec -T !SERVICE_NAME! which python > nul 2>&1
    if errorlevel 1 (
        echo 错误 | Error：容器中未找到python命令 | python command not found in container
        echo 请检查容器配置 | Please check container configuration
        exit /b 1
    )
)

REM 在容器中运行指定的脚本，传递查询参数 | Run the specified script in container, passing query parameter
echo 在Docker容器中使用!PYTHON_CMD!运行脚本... | Running script in Docker container using !PYTHON_CMD!...
docker-compose exec -T !SERVICE_NAME! !PYTHON_CMD! !SCRIPT_NAME! "!QUERY!"

if errorlevel 0 (
    echo 查询完成！ | Query completed!
) else (
    echo 查询执行失败，请检查错误信息。 | Query execution failed, please check error messages.
)

pause