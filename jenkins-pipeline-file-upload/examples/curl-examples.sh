#!/bin/bash

# Jenkins API cURL 示例脚本
# 功能: 使用cURL通过REST API上传文件并触发构建
# 作者: DevOps Team
# 版本: 1.0.0

set -euo pipefail

# 默认配置
JENKINS_URL="${JENKINS_URL:-http://localhost:8080}"
JENKINS_USER="${JENKINS_USER:-admin}"
JENKINS_TOKEN="${JENKINS_TOKEN:-}"
JOB_NAME="${JOB_NAME:-file-upload-pipeline-demo}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检查必需的命令
check_dependencies() {
    local missing_deps=()
    
    if ! command -v curl >/dev/null 2>&1; then
        missing_deps+=("curl")
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        missing_deps+=("jq")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "缺少必需的依赖: ${missing_deps[*]}"
        log_info "请安装缺少的工具："
        for dep in "${missing_deps[@]}"; do
            case $dep in
                curl) echo "  Ubuntu/Debian: sudo apt-get install curl" ;;
                jq) echo "  Ubuntu/Debian: sudo apt-get install jq" ;;
            esac
        done
        exit 1
    fi
}

# 验证Jenkins连接
test_jenkins_connection() {
    log_info "测试Jenkins连接..."
    
    local response
    response=$(curl -s -w "%{http_code}" \
        -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
        "${JENKINS_URL}/api/json" \
        -o /tmp/jenkins_response.json)
    
    if [ "$response" = "200" ]; then
        local version
        version=$(jq -r '.version // "Unknown"' /tmp/jenkins_response.json 2>/dev/null || echo "Unknown")
        log_info "连接成功 - Jenkins版本: $version"
        rm -f /tmp/jenkins_response.json
        return 0
    else
        log_error "连接失败 - HTTP状态码: $response"
        if [ -f /tmp/jenkins_response.json ]; then
            log_debug "响应内容: $(cat /tmp/jenkins_response.json)"
            rm -f /tmp/jenkins_response.json
        fi
        return 1
    fi
}

# 获取任务信息
get_job_info() {
    local job_name="$1"
    
    log_info "获取任务信息: $job_name"
    
    local response
    response=$(curl -s -w "%{http_code}" \
        -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
        "${JENKINS_URL}/job/${job_name}/api/json" \
        -o /tmp/job_info.json)
    
    if [ "$response" = "200" ]; then
        log_info "任务信息获取成功"
        
        # 显示任务参数
        if command -v jq >/dev/null 2>&1; then
            echo "任务参数:"
            jq -r '.actions[]? | select(.parameterDefinitions?) | .parameterDefinitions[] | "  - \(.name) (\(.type)): \(.description // "无描述")"' /tmp/job_info.json 2>/dev/null || echo "  无法解析参数信息"
        fi
        
        rm -f /tmp/job_info.json
        return 0
    else
        log_error "获取任务信息失败 - HTTP状态码: $response"
        if [ -f /tmp/job_info.json ]; then
            log_debug "响应内容: $(cat /tmp/job_info.json)"
            rm -f /tmp/job_info.json
        fi
        return 1
    fi
}

# 创建示例文件
create_sample_files() {
    local sample_dir="./sample-files"
    
    log_info "创建示例文件..."
    
    mkdir -p "$sample_dir"
    
    # 创建配置文件
    cat > "${sample_dir}/config.yml" << 'EOF'
# 示例应用配置文件
app:
  name: sample-app
  version: 1.0.0
  environment: dev

database:
  host: localhost
  port: 3306
  name: sample_db
  username: app_user

redis:
  host: localhost
  port: 6379
  database: 0

logging:
  level: DEBUG
  file: /var/log/app.log

features:
  enable_cache: true
  enable_metrics: true
  enable_tracing: false
EOF

    # 创建SQL脚本
    cat > "${sample_dir}/migration.sql" << 'EOF'
-- 数据库迁移脚本
-- 版本: 1.0.0

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 创建角色表
CREATE TABLE IF NOT EXISTS roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INT,
    role_id INT,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- 插入默认数据
INSERT INTO roles (name, description) VALUES 
('admin', '管理员角色'),
('user', '普通用户角色')
ON DUPLICATE KEY UPDATE description = VALUES(description);

INSERT INTO users (username, email, password_hash) VALUES 
('admin', 'admin@example.com', '$2b$12$example_hash_for_admin'),
('demo_user', 'demo@example.com', '$2b$12$example_hash_for_demo')
ON DUPLICATE KEY UPDATE email = VALUES(email);
EOF

    # 创建部署包 (模拟JAR文件)
    cat > "${sample_dir}/app.jar" << 'EOF'
PK                      sample-app-1.0.0.jar
This is a mock JAR file for demonstration purposes.
In a real scenario, this would be a compiled Java application.
EOF

    # 创建压缩包
    (cd "$sample_dir" && tar -czf deploy-package.tar.gz config.yml migration.sql app.jar)
    
    log_info "示例文件已创建在: $sample_dir"
    ls -la "$sample_dir"
}

# 基础参数构建 (无文件上传)
trigger_basic_build() {
    local job_name="$1"
    local app_version="${2:-1.0.0}"
    local environment="${3:-dev}"
    
    log_info "触发基础参数构建..."
    
    local response
    response=$(curl -s -w "%{http_code}" \
        -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
        -X POST \
        "${JENKINS_URL}/job/${job_name}/buildWithParameters" \
        -d "APP_VERSION=${app_version}" \
        -d "ENVIRONMENT=${environment}" \
        -d "SKIP_TESTS=false" \
        -d "BUILD_NOTES=cURL触发的基础构建" \
        -D /tmp/response_headers.txt \
        -o /tmp/build_response.txt)
    
    if [ "$response" = "201" ]; then
        log_info "构建触发成功"
        
        # 从Location头获取队列URL
        if [ -f /tmp/response_headers.txt ]; then
            local queue_url
            queue_url=$(grep -i "Location:" /tmp/response_headers.txt | cut -d' ' -f2 | tr -d '\r\n')
            if [ -n "$queue_url" ]; then
                log_info "队列URL: $queue_url"
                
                # 获取构建编号
                local build_number
                build_number=$(get_build_number_from_queue "$queue_url")
                if [ -n "$build_number" ]; then
                    log_info "构建编号: $build_number"
                    log_info "构建URL: ${JENKINS_URL}/job/${job_name}/${build_number}/"
                fi
            fi
        fi
        
        rm -f /tmp/response_headers.txt /tmp/build_response.txt
        return 0
    else
        log_error "构建触发失败 - HTTP状态码: $response"
        if [ -f /tmp/build_response.txt ]; then
            log_debug "响应内容: $(cat /tmp/build_response.txt)"
            rm -f /tmp/build_response.txt
        fi
        rm -f /tmp/response_headers.txt
        return 1
    fi
}

# 文件上传构建
trigger_file_upload_build() {
    local job_name="$1"
    local config_file="$2"
    local package_file="$3"
    local app_version="${4:-1.0.0}"
    local environment="${5:-dev}"
    
    log_info "触发文件上传构建..."
    
    # 构建cURL命令
    local curl_cmd=(
        curl -s -w "%{http_code}"
        -u "${JENKINS_USER}:${JENKINS_TOKEN}"
        -X POST
        "${JENKINS_URL}/job/${job_name}/buildWithParameters"
        -F "APP_VERSION=${app_version}"
        -F "ENVIRONMENT=${environment}"
        -F "SKIP_TESTS=false"
        -F "BUILD_NOTES=cURL触发的文件上传构建"
    )
    
    # 添加文件参数
    if [ -n "$config_file" ] && [ -f "$config_file" ]; then
        curl_cmd+=(-F "CONFIG_FILE=@${config_file}")
        log_info "添加配置文件: $config_file"
    fi
    
    if [ -n "$package_file" ] && [ -f "$package_file" ]; then
        curl_cmd+=(-F "DEPLOY_PACKAGE=@${package_file}")
        log_info "添加部署包: $package_file"
    fi
    
    curl_cmd+=(
        -D /tmp/response_headers.txt
        -o /tmp/build_response.txt
    )
    
    # 执行请求
    local response
    response=$("${curl_cmd[@]}")
    
    if [ "$response" = "201" ]; then
        log_info "文件上传构建触发成功"
        
        # 处理响应
        if [ -f /tmp/response_headers.txt ]; then
            local queue_url
            queue_url=$(grep -i "Location:" /tmp/response_headers.txt | cut -d' ' -f2 | tr -d '\r\n')
            if [ -n "$queue_url" ]; then
                log_info "队列URL: $queue_url"
                
                local build_number
                build_number=$(get_build_number_from_queue "$queue_url")
                if [ -n "$build_number" ]; then
                    log_info "构建编号: $build_number"
                    log_info "构建URL: ${JENKINS_URL}/job/${job_name}/${build_number}/"
                    
                    # 可选：等待构建完成
                    if [ "${WAIT_FOR_BUILD:-false}" = "true" ]; then
                        wait_for_build_completion "$job_name" "$build_number"
                    fi
                fi
            fi
        fi
        
        rm -f /tmp/response_headers.txt /tmp/build_response.txt
        return 0
    else
        log_error "文件上传构建触发失败 - HTTP状态码: $response"
        if [ -f /tmp/build_response.txt ]; then
            log_debug "响应内容: $(cat /tmp/build_response.txt)"
            rm -f /tmp/build_response.txt
        fi
        rm -f /tmp/response_headers.txt
        return 1
    fi
}

# 从队列获取构建编号
get_build_number_from_queue() {
    local queue_url="$1"
    
    log_debug "从队列获取构建编号: $queue_url"
    
    # 等待构建开始
    for i in {1..30}; do
        local response
        response=$(curl -s -w "%{http_code}" \
            -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
            "${queue_url}api/json" \
            -o /tmp/queue_item.json)
        
        if [ "$response" = "200" ]; then
            if command -v jq >/dev/null 2>&1; then
                local build_number
                build_number=$(jq -r '.executable.number // empty' /tmp/queue_item.json 2>/dev/null)
                if [ -n "$build_number" ] && [ "$build_number" != "null" ]; then
                    rm -f /tmp/queue_item.json
                    echo "$build_number"
                    return 0
                fi
            fi
        fi
        
        log_debug "等待构建开始... ($i/30)"
        sleep 2
    done
    
    log_warn "无法从队列获取构建编号"
    rm -f /tmp/queue_item.json
    return 1
}

# 获取构建状态
get_build_status() {
    local job_name="$1"
    local build_number="$2"
    
    local response
    response=$(curl -s -w "%{http_code}" \
        -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
        "${JENKINS_URL}/job/${job_name}/${build_number}/api/json" \
        -o /tmp/build_status.json)
    
    if [ "$response" = "200" ]; then
        if command -v jq >/dev/null 2>&1; then
            local building result duration
            building=$(jq -r '.building' /tmp/build_status.json)
            result=$(jq -r '.result // "BUILDING"' /tmp/build_status.json)
            duration=$(jq -r '.duration' /tmp/build_status.json)
            
            echo "$building|$result|$duration"
        else
            echo "true|UNKNOWN|0"
        fi
        rm -f /tmp/build_status.json
        return 0
    else
        rm -f /tmp/build_status.json
        return 1
    fi
}

# 等待构建完成
wait_for_build_completion() {
    local job_name="$1"
    local build_number="$2"
    local timeout="${3:-1800}"  # 30分钟默认超时
    
    log_info "等待构建完成: ${job_name} #${build_number}"
    
    local start_time
    start_time=$(date +%s)
    
    while true; do
        local current_time
        current_time=$(date +%s)
        
        if [ $((current_time - start_time)) -gt $timeout ]; then
            log_warn "等待构建超时"
            return 1
        fi
        
        local status_info
        status_info=$(get_build_status "$job_name" "$build_number")
        
        if [ $? -eq 0 ]; then
            IFS='|' read -r building result duration <<< "$status_info"
            
            if [ "$building" = "false" ]; then
                log_info "构建完成: $result"
                if [ "$duration" != "null" ] && [ "$duration" != "0" ]; then
                    local duration_seconds=$((duration / 1000))
                    log_info "构建耗时: ${duration_seconds}秒"
                fi
                
                case "$result" in
                    SUCCESS)
                        log_info "✅ 构建成功"
                        return 0
                        ;;
                    FAILURE)
                        log_error "❌ 构建失败"
                        return 1
                        ;;
                    UNSTABLE)
                        log_warn "⚠️ 构建不稳定"
                        return 2
                        ;;
                    ABORTED)
                        log_warn "🚫 构建已中止"
                        return 3
                        ;;
                    *)
                        log_warn "❓ 构建状态未知: $result"
                        return 4
                        ;;
                esac
            else
                log_info "构建进行中..."
            fi
        else
            log_warn "无法获取构建状态"
        fi
        
        sleep 10
    done
}

# 获取构建日志
get_build_log() {
    local job_name="$1"
    local build_number="$2"
    local output_file="${3:-}"
    
    log_info "获取构建日志: ${job_name} #${build_number}"
    
    local response
    if [ -n "$output_file" ]; then
        response=$(curl -s -w "%{http_code}" \
            -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
            "${JENKINS_URL}/job/${job_name}/${build_number}/consoleText" \
            -o "$output_file")
        
        if [ "$response" = "200" ]; then
            log_info "构建日志已保存到: $output_file"
            return 0
        fi
    else
        response=$(curl -s -w "%{http_code}" \
            -u "${JENKINS_USER}:${JENKINS_TOKEN}" \
            "${JENKINS_URL}/job/${job_name}/${build_number}/consoleText" \
            -o /tmp/build_log.txt)
        
        if [ "$response" = "200" ]; then
            cat /tmp/build_log.txt
            rm -f /tmp/build_log.txt
            return 0
        fi
    fi
    
    log_error "获取构建日志失败 - HTTP状态码: $response"
    return 1
}

# 批量文件上传
batch_file_upload() {
    local job_name="$1"
    shift
    local files=("$@")
    
    log_info "批量文件上传构建..."
    
    local curl_cmd=(
        curl -s -w "%{http_code}"
        -u "${JENKINS_USER}:${JENKINS_TOKEN}"
        -X POST
        "${JENKINS_URL}/job/${job_name}/buildWithParameters"
        -F "APP_VERSION=1.0.0"
        -F "ENVIRONMENT=dev"
        -F "BUILD_NOTES=批量文件上传构建"
    )
    
    # 添加多个文件
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            # 根据文件扩展名决定参数名
            case "$file" in
                *.yml|*.yaml|*.json|*.properties|*.xml)
                    curl_cmd+=(-F "CONFIG_FILE=@${file}")
                    log_info "添加配置文件: $file"
                    ;;
                *.jar|*.war|*.zip|*.tar.gz)
                    curl_cmd+=(-F "DEPLOY_PACKAGE=@${file}")
                    log_info "添加部署包: $file"
                    ;;
                *.sql)
                    curl_cmd+=(-F "DATABASE_SCRIPTS=@${file}")
                    log_info "添加数据库脚本: $file"
                    ;;
                *)
                    log_warn "未知文件类型，跳过: $file"
                    ;;
            esac
        else
            log_warn "文件不存在，跳过: $file"
        fi
    done
    
    curl_cmd+=(
        -D /tmp/response_headers.txt
        -o /tmp/build_response.txt
    )
    
    # 执行请求
    local response
    response=$("${curl_cmd[@]}")
    
    if [ "$response" = "201" ]; then
        log_info "批量文件上传构建触发成功"
        rm -f /tmp/response_headers.txt /tmp/build_response.txt
        return 0
    else
        log_error "批量文件上传构建触发失败 - HTTP状态码: $response"
        if [ -f /tmp/build_response.txt ]; then
            log_debug "响应内容: $(cat /tmp/build_response.txt)"
        fi
        rm -f /tmp/response_headers.txt /tmp/build_response.txt
        return 1
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
Jenkins cURL API 示例脚本

用法: $0 [命令] [选项]

命令:
  test                     测试Jenkins连接
  info <job-name>          获取任务信息
  create-samples           创建示例文件
  basic-build <job-name>   触发基础参数构建
  file-build <job-name> <config> <package>  触发文件上传构建
  batch-build <job-name> <file1> [file2...]  批量文件上传构建
  wait <job-name> <build-number>  等待构建完成
  log <job-name> <build-number> [output-file]  获取构建日志

环境变量:
  JENKINS_URL              Jenkins服务器URL (默认: http://localhost:8080)
  JENKINS_USER             Jenkins用户名 (默认: admin)
  JENKINS_TOKEN            Jenkins API Token
  JOB_NAME                 默认任务名称
  WAIT_FOR_BUILD           是否等待构建完成 (true/false)

示例:
  # 测试连接
  $0 test

  # 获取任务信息
  $0 info my-pipeline-job

  # 创建示例文件
  $0 create-samples

  # 基础构建
  $0 basic-build my-pipeline-job

  # 文件上传构建
  $0 file-build my-pipeline-job ./config.yml ./app.jar

  # 批量文件上传
  $0 batch-build my-pipeline-job ./config.yml ./app.jar ./migration.sql

  # 等待构建完成
  $0 wait my-pipeline-job 123

  # 获取构建日志
  $0 log my-pipeline-job 123 build.log

环境变量示例:
  export JENKINS_URL=http://jenkins.example.com
  export JENKINS_USER=myuser
  export JENKINS_TOKEN=abc123def456
  export WAIT_FOR_BUILD=true
  $0 file-build my-job ./config.yml ./app.jar
EOF
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # 检查依赖
    check_dependencies
    
    local command="$1"
    shift
    
    case "$command" in
        test)
            test_jenkins_connection
            ;;
        info)
            if [ $# -lt 1 ]; then
                log_error "缺少任务名称参数"
                exit 1
            fi
            get_job_info "$1"
            ;;
        create-samples)
            create_sample_files
            ;;
        basic-build)
            if [ $# -lt 1 ]; then
                log_error "缺少任务名称参数"
                exit 1
            fi
            trigger_basic_build "$1" "${2:-1.0.0}" "${3:-dev}"
            ;;
        file-build)
            if [ $# -lt 3 ]; then
                log_error "缺少必要参数: job-name config-file package-file"
                exit 1
            fi
            trigger_file_upload_build "$1" "$2" "$3" "${4:-1.0.0}" "${5:-dev}"
            ;;
        batch-build)
            if [ $# -lt 2 ]; then
                log_error "缺少必要参数: job-name file1 [file2...]"
                exit 1
            fi
            batch_file_upload "$@"
            ;;
        wait)
            if [ $# -lt 2 ]; then
                log_error "缺少必要参数: job-name build-number"
                exit 1
            fi
            wait_for_build_completion "$1" "$2"
            ;;
        log)
            if [ $# -lt 2 ]; then
                log_error "缺少必要参数: job-name build-number [output-file]"
                exit 1
            fi
            get_build_log "$1" "$2" "${3:-}"
            ;;
        -h|--help)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi