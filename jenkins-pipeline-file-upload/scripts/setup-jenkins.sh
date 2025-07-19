#!/bin/bash

# Jenkins 环境配置脚本
# 功能: 自动安装必需插件和配置Jenkins环境
# 作者: DevOps Team
# 版本: 1.0.0

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查Jenkins是否运行
check_jenkins_running() {
    local jenkins_url="${JENKINS_URL:-http://localhost:8080}"
    
    log_info "检查Jenkins运行状态..."
    
    if curl -s --connect-timeout 5 "${jenkins_url}/login" >/dev/null; then
        log_info "Jenkins正在运行: ${jenkins_url}"
        return 0
    else
        log_error "Jenkins未运行或无法访问: ${jenkins_url}"
        return 1
    fi
}

# 安装Jenkins CLI
install_jenkins_cli() {
    local jenkins_url="${JENKINS_URL:-http://localhost:8080}"
    local cli_jar="jenkins-cli.jar"
    
    log_info "下载Jenkins CLI..."
    
    if ! curl -s "${jenkins_url}/jnlpJars/jenkins-cli.jar" -o "$cli_jar"; then
        log_error "下载Jenkins CLI失败"
        return 1
    fi
    
    log_info "Jenkins CLI下载完成: $cli_jar"
    echo "$cli_jar"
}

# 等待Jenkins启动完成
wait_for_jenkins() {
    local jenkins_url="${JENKINS_URL:-http://localhost:8080}"
    local max_attempts=30
    local attempt=1
    
    log_info "等待Jenkins启动完成..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s --connect-timeout 5 "${jenkins_url}/api/json" >/dev/null; then
            log_info "Jenkins已启动完成"
            return 0
        fi
        
        log_debug "等待Jenkins启动... (尝试 $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    log_error "等待Jenkins启动超时"
    return 1
}

# 获取已安装的插件列表
get_installed_plugins() {
    local cli_jar="$1"
    local jenkins_url="${JENKINS_URL:-http://localhost:8080}"
    local auth_args=""
    
    if [[ -n "${JENKINS_USER:-}" && -n "${JENKINS_TOKEN:-}" ]]; then
        auth_args="-auth ${JENKINS_USER}:${JENKINS_TOKEN}"
    fi
    
    java -jar "$cli_jar" -s "$jenkins_url" $auth_args list-plugins --output csv | awk -F',' '{print $1}' | tail -n +2
}

# 安装Jenkins插件
install_plugin() {
    local plugin_name="$1"
    local cli_jar="$2"
    local jenkins_url="${JENKINS_URL:-http://localhost:8080}"
    local auth_args=""
    
    if [[ -n "${JENKINS_USER:-}" && -n "${JENKINS_TOKEN:-}" ]]; then
        auth_args="-auth ${JENKINS_USER}:${JENKINS_TOKEN}"
    fi
    
    log_info "安装插件: $plugin_name"
    
    if java -jar "$cli_jar" -s "$jenkins_url" $auth_args install-plugin "$plugin_name" -restart; then
        log_info "插件 $plugin_name 安装成功"
        return 0
    else
        log_error "插件 $plugin_name 安装失败"
        return 1
    fi
}

# 检查插件是否已安装
is_plugin_installed() {
    local plugin_name="$1"
    local installed_plugins="$2"
    
    echo "$installed_plugins" | grep -q "^$plugin_name$"
}

# 主要的插件安装函数
install_required_plugins() {
    local cli_jar="$1"
    
    # 必需的插件列表
    local required_plugins=(
        "pipeline-stage-view"           # Pipeline阶段视图
        "workflow-aggregator"           # Pipeline插件集合
        "build-with-parameters"         # 参数化构建
        "file-parameters"               # 文件参数
        "extended-choice-parameter"     # 扩展选择参数
        "active-choices"                # 动态选择参数
        "pipeline-utility-steps"        # Pipeline工具步骤
        "ws-cleanup"                    # 工作空间清理
        "timestamper"                   # 时间戳
        "ansicolor"                     # ANSI颜色
        "build-timeout"                 # 构建超时
        "email-ext"                     # 邮件扩展
        "slack"                         # Slack通知
        "git"                           # Git插件
        "github"                        # GitHub插件
        "credentials"                   # 凭证管理
        "ssh-credentials"               # SSH凭证
        "plain-credentials"             # 普通凭证
        "matrix-auth"                   # 矩阵授权
        "role-strategy"                 # 角色策略
        "ldap"                          # LDAP认证
        "audit-trail"                   # 审计跟踪
        "job-dsl"                       # Job DSL
        "configuration-as-code"         # 配置即代码
        "prometheus"                    # Prometheus监控
        "blue-ocean"                    # Blue Ocean UI
    )
    
    # 可选的插件列表
    local optional_plugins=(
        "docker-workflow"               # Docker Pipeline
        "kubernetes"                    # Kubernetes插件
        "sonar"                         # SonarQube插件
        "jacoco"                        # JaCoCo代码覆盖率
        "junit"                         # JUnit测试报告
        "htmlpublisher"                 # HTML报告发布
        "performance"                   # 性能测试
        "jmeter"                        # JMeter插件
        "artifactory"                   # Artifactory插件
        "nexus-artifact-uploader"       # Nexus上传器
        "checkstyle"                    # Checkstyle插件
        "findbugs"                      # FindBugs插件
        "pmd"                           # PMD插件
        "warnings-ng"                   # 警告收集器
        "build-monitor-plugin"          # 构建监控
        "dashboard-view"                # 仪表盘视图
        "build-pipeline-plugin"         # 构建流水线视图
    )
    
    log_info "获取已安装插件列表..."
    local installed_plugins
    installed_plugins=$(get_installed_plugins "$cli_jar")
    
    # 安装必需插件
    log_info "开始安装必需插件..."
    local required_install_count=0
    
    for plugin in "${required_plugins[@]}"; do
        if is_plugin_installed "$plugin" "$installed_plugins"; then
            log_info "插件 $plugin 已安装，跳过"
        else
            if install_plugin "$plugin" "$cli_jar"; then
                ((required_install_count++))
            fi
        fi
    done
    
    # 安装可选插件 (根据环境变量决定)
    if [[ "${INSTALL_OPTIONAL_PLUGINS:-false}" == "true" ]]; then
        log_info "开始安装可选插件..."
        local optional_install_count=0
        
        for plugin in "${optional_plugins[@]}"; do
            if is_plugin_installed "$plugin" "$installed_plugins"; then
                log_info "插件 $plugin 已安装，跳过"
            else
                if install_plugin "$plugin" "$cli_jar"; then
                    ((optional_install_count++))
                else
                    log_warn "可选插件 $plugin 安装失败，继续..."
                fi
            fi
        done
        
        log_info "可选插件安装完成，共安装 $optional_install_count 个插件"
    fi
    
    log_info "必需插件安装完成，共安装 $required_install_count 个插件"
    
    if [ $required_install_count -gt 0 ]; then
        log_warn "已安装新插件，Jenkins将重启..."
        return 1  # 需要重启
    else
        log_info "所有必需插件已安装，无需重启"
        return 0  # 无需重启
    fi
}

# 配置Jenkins安全设置
configure_security() {
    local cli_jar="$1"
    local jenkins_url="${JENKINS_URL:-http://localhost:8080}"
    local auth_args=""
    
    if [[ -n "${JENKINS_USER:-}" && -n "${JENKINS_TOKEN:-}" ]]; then
        auth_args="-auth ${JENKINS_USER}:${JENKINS_TOKEN}"
    fi
    
    log_info "配置Jenkins安全设置..."
    
    # 创建安全配置脚本
    cat > security-config.groovy << 'EOF'
import jenkins.model.*
import hudson.security.*
import hudson.security.csrf.DefaultCrumbIssuer

def instance = Jenkins.getInstance()

// 启用CSRF保护
if(!instance.getCrumbIssuer()) {
    instance.setCrumbIssuer(new DefaultCrumbIssuer(true))
    println "CSRF保护已启用"
}

// 配置授权策略 (如果还没有配置)
if(!(instance.getAuthorizationStrategy() instanceof GlobalMatrixAuthorizationStrategy)) {
    def strategy = new GlobalMatrixAuthorizationStrategy()
    
    // 授予匿名用户读取权限
    strategy.add(Jenkins.READ, "anonymous")
    
    // 授予认证用户基本权限
    strategy.add(Jenkins.ADMINISTER, "authenticated")
    strategy.add(Jenkins.READ, "authenticated")
    strategy.add(Item.BUILD, "authenticated")
    strategy.add(Item.READ, "authenticated")
    strategy.add(Item.WORKSPACE, "authenticated")
    
    instance.setAuthorizationStrategy(strategy)
    println "授权策略已配置"
}

// 保存配置
instance.save()
println "安全配置已保存"
EOF

    # 执行安全配置
    if java -jar "$cli_jar" -s "$jenkins_url" $auth_args groovy security-config.groovy; then
        log_info "安全配置完成"
        rm -f security-config.groovy
        return 0
    else
        log_error "安全配置失败"
        rm -f security-config.groovy
        return 1
    fi
}

# 配置全局工具
configure_global_tools() {
    local cli_jar="$1"
    local jenkins_url="${JENKINS_URL:-http://localhost:8080}"
    local auth_args=""
    
    if [[ -n "${JENKINS_USER:-}" && -n "${JENKINS_TOKEN:-}" ]]; then
        auth_args="-auth ${JENKINS_USER}:${JENKINS_TOKEN}"
    fi
    
    log_info "配置全局工具..."
    
    # 创建工具配置脚本
    cat > tools-config.groovy << 'EOF'
import jenkins.model.*
import hudson.model.*
import hudson.tools.*
import hudson.util.DescribableList
import hudson.plugins.git.GitTool

def instance = Jenkins.getInstance()

// 配置Git工具
def gitTools = instance.getDescriptor(GitTool.class)
def gitInstallations = gitTools.getInstallations()

if (gitInstallations.length == 0) {
    def newGitInstallations = [
        new GitTool("Default", "/usr/bin/git", [])
    ] as GitTool[]
    
    gitTools.setInstallations(newGitInstallations)
    println "Git工具已配置"
}

// 保存配置
instance.save()
println "全局工具配置完成"
EOF

    # 执行工具配置
    if java -jar "$cli_jar" -s "$jenkins_url" $auth_args groovy tools-config.groovy; then
        log_info "全局工具配置完成"
        rm -f tools-config.groovy
        return 0
    else
        log_error "全局工具配置失败"
        rm -f tools-config.groovy
        return 1
    fi
}

# 创建示例Pipeline任务
create_sample_job() {
    local cli_jar="$1"
    local jenkins_url="${JENKINS_URL:-http://localhost:8080}"
    local auth_args=""
    
    if [[ -n "${JENKINS_USER:-}" && -n "${JENKINS_TOKEN:-}" ]]; then
        auth_args="-auth ${JENKINS_USER}:${JENKINS_TOKEN}"
    fi
    
    local job_name="file-upload-pipeline-demo"
    
    log_info "创建示例Pipeline任务: $job_name"
    
    # 创建任务配置XML
    cat > job-config.xml << 'EOF'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <actions>
    <org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobAction plugin="pipeline-model-definition@1.8.5"/>
    <org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobPropertyTrackerAction plugin="pipeline-model-definition@1.8.5">
      <jobProperties/>
      <triggers/>
      <parameters/>
      <options/>
    </org.jenkinsci.plugins.pipeline.modeldefinition.actions.DeclarativeJobPropertyTrackerAction>
  </actions>
  <description>演示文件上传参数构建的Pipeline任务</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.plugins.buildselector.parameters.BuildParametersDefinitionProperty plugin="build-with-parameters@1.4">
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>APP_VERSION</name>
          <description>应用版本号</description>
          <defaultValue>1.0.0</defaultValue>
          <trim>true</trim>
        </hudson.model.StringParameterDefinition>
        <hudson.model.ChoiceParameterDefinition>
          <name>ENVIRONMENT</name>
          <description>部署环境</description>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array">
              <string>dev</string>
              <string>test</string>
              <string>staging</string>
              <string>prod</string>
            </a>
          </choices>
        </hudson.model.ChoiceParameterDefinition>
        <hudson.model.FileParameterDefinition>
          <name>CONFIG_FILE</name>
          <description>配置文件上传</description>
        </hudson.model.FileParameterDefinition>
        <hudson.model.FileParameterDefinition>
          <name>DEPLOY_PACKAGE</name>
          <description>部署包上传</description>
        </hudson.model.FileParameterDefinition>
        <hudson.model.BooleanParameterDefinition>
          <name>SKIP_TESTS</name>
          <description>是否跳过测试</description>
          <defaultValue>false</defaultValue>
        </hudson.model.BooleanParameterDefinition>
      </parameterDefinitions>
    </hudson.plugins.buildselector.parameters.BuildParametersDefinitionProperty>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers/>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.92">
    <script>
pipeline {
    agent any
    
    environment {
        BUILD_TIMESTAMP = sh(script: "date '+%Y%m%d-%H%M%S'", returnStdout: true).trim()
    }
    
    stages {
        stage('参数验证') {
            steps {
                script {
                    echo "=== 构建参数 ==="
                    echo "应用版本: ${params.APP_VERSION}"
                    echo "部署环境: ${params.ENVIRONMENT}"
                    echo "跳过测试: ${params.SKIP_TESTS}"
                    echo "构建时间: ${env.BUILD_TIMESTAMP}"
                    
                    if (params.CONFIG_FILE) {
                        echo "配置文件: ${params.CONFIG_FILE}"
                    }
                    if (params.DEPLOY_PACKAGE) {
                        echo "部署包: ${params.DEPLOY_PACKAGE}"
                    }
                }
            }
        }
        
        stage('文件处理') {
            when {
                anyOf {
                    expression { params.CONFIG_FILE != null && params.CONFIG_FILE != '' }
                    expression { params.DEPLOY_PACKAGE != null && params.DEPLOY_PACKAGE != '' }
                }
            }
            steps {
                script {
                    echo "=== 文件处理 ==="
                    
                    if (params.CONFIG_FILE) {
                        echo "处理配置文件: ${params.CONFIG_FILE}"
                        sh "ls -la ${params.CONFIG_FILE} || true"
                    }
                    
                    if (params.DEPLOY_PACKAGE) {
                        echo "处理部署包: ${params.DEPLOY_PACKAGE}"
                        sh "ls -la ${params.DEPLOY_PACKAGE} || true"
                    }
                }
            }
        }
        
        stage('构建与测试') {
            steps {
                script {
                    echo "=== 构建应用 ==="
                    echo "构建版本: ${params.APP_VERSION}"
                    
                    if (!params.SKIP_TESTS) {
                        echo "执行测试..."
                        sleep(2)
                    } else {
                        echo "跳过测试阶段"
                    }
                    
                    echo "构建完成"
                }
            }
        }
        
        stage('部署') {
            steps {
                script {
                    echo "=== 部署到 ${params.ENVIRONMENT} 环境 ==="
                    
                    switch(params.ENVIRONMENT) {
                        case 'dev':
                            echo "部署到开发环境"
                            break
                        case 'test':
                            echo "部署到测试环境"
                            break
                        case 'staging':
                            echo "部署到预发布环境"
                            break
                        case 'prod':
                            echo "部署到生产环境"
                            input message: '确认部署到生产环境?', ok: '确认'
                            break
                    }
                    
                    echo "部署完成"
                }
            }
        }
    }
    
    post {
        always {
            echo "构建后清理..."
            cleanWs()
        }
        success {
            echo "🎉 构建成功!"
        }
        failure {
            echo "❌ 构建失败!"
        }
    }
}
    </script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
EOF

    # 创建任务
    if java -jar "$cli_jar" -s "$jenkins_url" $auth_args create-job "$job_name" < job-config.xml; then
        log_info "示例任务创建成功: $job_name"
        log_info "访问地址: ${jenkins_url}/job/${job_name}/"
        rm -f job-config.xml
        return 0
    else
        log_error "示例任务创建失败"
        rm -f job-config.xml
        return 1
    fi
}

# 显示使用帮助
show_help() {
    cat << EOF
Jenkins 环境配置脚本

用法: $0 [选项]

选项:
  -h, --help                显示此帮助信息
  -u, --url URL            Jenkins服务器URL (默认: http://localhost:8080)
  --user USERNAME          Jenkins用户名 (用于认证)
  --token TOKEN            Jenkins API Token (用于认证)
  --install-optional       安装可选插件
  --skip-security          跳过安全配置
  --skip-tools             跳过工具配置
  --skip-sample-job        跳过示例任务创建
  --wait-timeout SECONDS   等待Jenkins启动超时时间 (默认: 300秒)

环境变量:
  JENKINS_URL             Jenkins服务器URL
  JENKINS_USER            Jenkins用户名
  JENKINS_TOKEN           Jenkins API Token
  INSTALL_OPTIONAL_PLUGINS 是否安装可选插件 (true/false)

示例:
  # 基本配置
  $0 --url http://localhost:8080

  # 使用认证
  $0 --url http://jenkins.example.com --user admin --token abc123

  # 安装可选插件
  $0 --install-optional

  # 使用环境变量
  export JENKINS_URL=http://localhost:8080
  export JENKINS_USER=admin
  export JENKINS_TOKEN=abc123
  $0
EOF
}

# 主函数
main() {
    local jenkins_url="${JENKINS_URL:-http://localhost:8080}"
    local jenkins_user="${JENKINS_USER:-}"
    local jenkins_token="${JENKINS_TOKEN:-}"
    local install_optional="${INSTALL_OPTIONAL_PLUGINS:-false}"
    local skip_security=false
    local skip_tools=false
    local skip_sample_job=false
    local wait_timeout=300
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -u|--url)
                jenkins_url="$2"
                shift 2
                ;;
            --user)
                jenkins_user="$2"
                shift 2
                ;;
            --token)
                jenkins_token="$2"
                shift 2
                ;;
            --install-optional)
                install_optional=true
                shift
                ;;
            --skip-security)
                skip_security=true
                shift
                ;;
            --skip-tools)
                skip_tools=true
                shift
                ;;
            --skip-sample-job)
                skip_sample_job=true
                shift
                ;;
            --wait-timeout)
                wait_timeout="$2"
                shift 2
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 设置环境变量
    export JENKINS_URL="$jenkins_url"
    export JENKINS_USER="$jenkins_user"
    export JENKINS_TOKEN="$jenkins_token"
    export INSTALL_OPTIONAL_PLUGINS="$install_optional"
    
    log_info "开始Jenkins环境配置..."
    log_info "Jenkins URL: $jenkins_url"
    
    # 检查依赖
    if ! command_exists java; then
        log_error "Java未安装或不在PATH中"
        exit 1
    fi
    
    if ! command_exists curl; then
        log_error "curl未安装或不在PATH中"
        exit 1
    fi
    
    # 等待Jenkins启动
    if ! wait_for_jenkins; then
        log_error "Jenkins未启动或无法访问"
        exit 1
    fi
    
    # 下载Jenkins CLI
    local cli_jar
    if ! cli_jar=$(install_jenkins_cli); then
        log_error "Jenkins CLI安装失败"
        exit 1
    fi
    
    # 安装插件
    local need_restart=false
    if install_required_plugins "$cli_jar"; then
        log_info "插件安装完成，无需重启"
    else
        log_warn "插件安装完成，需要重启Jenkins"
        need_restart=true
    fi
    
    # 如果需要重启，等待重启完成
    if [ "$need_restart" = true ]; then
        log_info "等待Jenkins重启..."
        sleep 30
        if ! wait_for_jenkins; then
            log_error "Jenkins重启后无法访问"
            exit 1
        fi
    fi
    
    # 配置安全设置
    if [ "$skip_security" = false ]; then
        if ! configure_security "$cli_jar"; then
            log_warn "安全配置失败，继续..."
        fi
    fi
    
    # 配置全局工具
    if [ "$skip_tools" = false ]; then
        if ! configure_global_tools "$cli_jar"; then
            log_warn "全局工具配置失败，继续..."
        fi
    fi
    
    # 创建示例任务
    if [ "$skip_sample_job" = false ]; then
        if ! create_sample_job "$cli_jar"; then
            log_warn "示例任务创建失败，继续..."
        fi
    fi
    
    # 清理
    rm -f "$cli_jar"
    
    log_info "Jenkins环境配置完成!"
    log_info ""
    log_info "后续步骤:"
    log_info "1. 访问Jenkins Web界面: $jenkins_url"
    log_info "2. 查看示例Pipeline任务: ${jenkins_url}/job/file-upload-pipeline-demo/"
    log_info "3. 根据需要创建自己的Pipeline任务"
    log_info "4. 配置凭证和其他全局设置"
    
    if [[ -n "$jenkins_user" && -n "$jenkins_token" ]]; then
        log_info ""
        log_info "API使用示例:"
        log_info "python3 api-upload-example.py \\"
        log_info "  --jenkins-url $jenkins_url \\"
        log_info "  --username $jenkins_user \\"
        log_info "  --token $jenkins_token \\"
        log_info "  --job-name file-upload-pipeline-demo"
    fi
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi