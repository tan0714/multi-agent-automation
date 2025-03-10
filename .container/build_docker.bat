@echo off
setlocal enabledelayedexpansion

echo 在Windows上构建Docker镜像... | Building Docker image on Windows...

REM 设置配置变量 | Set configuration variables
set CACHE_DIR=.docker-cache\pip
set BUILD_ARGS=--build-arg BUILDKIT_INLINE_CACHE=1
set COMPOSE_FILE=docker-compose.yml

REM 解析命令行参数 | Parse command line arguments
set CLEAN_CACHE=0
set REBUILD=0
set SERVICE=

:parse_args
if "%~1"=="" goto :end_parse_args
if /i "%~1"=="--clean" (
    set CLEAN_CACHE=1
    shift
    goto :parse_args
)
if /i "%~1"=="--rebuild" (
    set REBUILD=1
    shift
    goto :parse_args
)
if /i "%~1"=="--service" (
    set SERVICE=%~2
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--help" (
    echo 用法 | Usage: build_docker.bat [选项 | options]
    echo 选项 | Options:
    echo   --clean     清理缓存目录 | Clean cache directory
    echo   --rebuild   强制重新构建镜像 | Force rebuild image
    echo   --service   指定要构建的服务名称 | Specify service name to build
    echo   --help      显示此帮助信息 | Show this help message
    exit /b 0
)
shift
goto :parse_args
:end_parse_args

REM 检查Docker是否安装 | Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误 | Error: Docker未安装 | Docker not installed
    echo 请先安装Docker Desktop | Please install Docker Desktop first: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

REM 检查Docker是否运行 | Check if Docker is running
docker info >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误 | Error: Docker未运行 | Docker not running
    echo 请启动Docker Desktop应用程序 | Please start Docker Desktop application
    pause
    exit /b 1
)

REM 检查docker-compose.yml文件是否存在 | Check if docker-compose.yml file exists
if not exist "%COMPOSE_FILE%" (
    echo 错误 | Error: 未找到%COMPOSE_FILE%文件 | %COMPOSE_FILE% file not found
    echo 请确保在正确的目录中运行此脚本 | Please make sure you are running this script in the correct directory
    pause
    exit /b 1
)

REM 检查Docker Compose命令 | Check Docker Compose command
where docker-compose >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set COMPOSE_CMD=docker-compose
) else (
    echo 尝试使用新的docker compose命令... | Trying to use new docker compose command...
    docker compose version >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set COMPOSE_CMD=docker compose
    ) else (
        echo 错误 | Error: 未找到Docker Compose命令 | Docker Compose command not found
        echo 请确保Docker Desktop已正确安装 | Please make sure Docker Desktop is properly installed
        pause
        exit /b 1
    )
)

REM 设置Docker BuildKit环境变量 | Set Docker BuildKit environment variables
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1

echo 启用Docker BuildKit加速构建... | Enabling Docker BuildKit to accelerate build...

REM 清理缓存（如果指定） | Clean cache (if specified)
if %CLEAN_CACHE% EQU 1 (
    echo 清理缓存目录... | Cleaning cache directory...
    if exist "%CACHE_DIR%" rmdir /s /q "%CACHE_DIR%"
)

REM 创建缓存目录 | Create cache directory
if not exist "%CACHE_DIR%" (
    echo 创建缓存目录... | Creating cache directory...
    mkdir "%CACHE_DIR%"
)

REM 添加构建时间标记 | Add build time tag
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YEAR=%dt:~0,4%"
set "MONTH=%dt:~4,2%"
set "DAY=%dt:~6,2%"
set "HOUR=%dt:~8,2%"
set "MINUTE=%dt:~10,2%"
set "BUILD_TIME=%YEAR%%MONTH%%DAY%_%HOUR%%MINUTE%"
set "BUILD_ARGS=%BUILD_ARGS% --build-arg BUILD_TIME=%BUILD_TIME%"

REM 构建Docker镜像 | Build Docker image
echo 开始构建Docker镜像... | Starting to build Docker image...

if "%SERVICE%"=="" (
    if %REBUILD% EQU 1 (
        echo 强制重新构建所有服务... | Force rebuilding all services...
        %COMPOSE_CMD% build --no-cache %BUILD_ARGS%
    ) else (
        %COMPOSE_CMD% build %BUILD_ARGS%
    )
) else (
    if %REBUILD% EQU 1 (
        echo 强制重新构建服务 %SERVICE%... | Force rebuilding service %SERVICE%...
        %COMPOSE_CMD% build --no-cache %BUILD_ARGS% %SERVICE%
    ) else (
        echo 构建服务 %SERVICE%... | Building service %SERVICE%...
        %COMPOSE_CMD% build %BUILD_ARGS% %SERVICE%
    )
)

if %ERRORLEVEL% EQU 0 (
    echo Docker镜像构建成功！ | Docker image build successful!
    echo 构建时间 | Build time: %BUILD_TIME%
    echo 可以使用以下命令启动容器： | You can use the following command to start the container:
    echo %COMPOSE_CMD% up -d
) else (
    echo Docker镜像构建失败，请检查错误信息。 | Docker image build failed, please check error messages.
)

pause