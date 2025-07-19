#!/usr/bin/env groovy

/**
 * Jenkins Pipeline: 基础文件上传参数构建
 * 功能: 支持多种参数类型和文件上传
 * 作者: DevOps Team
 * 版本: 1.0.0
 */

// 定义构建参数
properties([
    parameters([
        // 字符串参数
        string(
            name: 'APP_VERSION', 
            defaultValue: '1.0.0', 
            description: '应用版本号',
            trim: true
        ),
        
        // 选择参数
        choice(
            name: 'ENVIRONMENT', 
            choices: ['dev', 'test', 'staging', 'prod'], 
            description: '部署环境'
        ),
        
        // 布尔值参数
        booleanParam(
            name: 'SKIP_TESTS', 
            defaultValue: false, 
            description: '是否跳过测试'
        ),
        
        // 文件上传参数
        file(
            name: 'CONFIG_FILE', 
            description: '配置文件上传 (支持: .yml, .yaml, .json, .properties)'
        ),
        
        // 部署包文件
        file(
            name: 'DEPLOY_PACKAGE', 
            description: '部署包上传 (支持: .war, .jar, .zip)'
        ),
        
        // 多行文本参数
        text(
            name: 'BUILD_NOTES', 
            defaultValue: '', 
            description: '构建说明 (可选)'
        ),
        
        // 密码参数
        password(
            name: 'DEPLOY_PASSWORD', 
            defaultValue: '', 
            description: '部署密码'
        )
    ]),
    
    // 构建保留策略
    buildDiscarder(logRotator(
        numToKeepStr: '10',
        daysToKeepStr: '30'
    )),
    
    // 禁用并发构建
    disableConcurrentBuilds()
])

pipeline {
    agent any
    
    // 环境变量
    environment {
        BUILD_TIMESTAMP = sh(script: "date '+%Y%m%d-%H%M%S'", returnStdout: true).trim()
        WORKSPACE_FILES = "${WORKSPACE}/uploaded-files"
        LOG_LEVEL = 'INFO'
    }
    
    // 构建选项
    options {
        timeout(time: 30, unit: 'MINUTES')
        retry(2)
        skipStagesAfterUnstable()
        timestamps()
    }
    
    stages {
        stage('🔍 Parameter Validation') {
            steps {
                script {
                    echo "=== 构建参数验证 ==="
                    
                    // 打印所有参数
                    echo "应用版本: ${params.APP_VERSION}"
                    echo "部署环境: ${params.ENVIRONMENT}"
                    echo "跳过测试: ${params.SKIP_TESTS}"
                    echo "构建说明: ${params.BUILD_NOTES}"
                    echo "构建时间: ${env.BUILD_TIMESTAMP}"
                    
                    // 验证版本号格式
                    if (!params.APP_VERSION.matches(/^\d+\.\d+\.\d+$/)) {
                        error("版本号格式错误，应为 x.y.z 格式")
                    }
                    
                    // 验证环境参数
                    def validEnvs = ['dev', 'test', 'staging', 'prod']
                    if (!(params.ENVIRONMENT in validEnvs)) {
                        error("无效的部署环境: ${params.ENVIRONMENT}")
                    }
                    
                    echo "✅ 参数验证通过"
                }
            }
        }
        
        stage('📁 File Upload Processing') {
            when {
                anyOf {
                    expression { params.CONFIG_FILE != null && params.CONFIG_FILE != '' }
                    expression { params.DEPLOY_PACKAGE != null && params.DEPLOY_PACKAGE != '' }
                }
            }
            steps {
                script {
                    echo "=== 文件上传处理 ==="
                    
                    // 创建文件存储目录
                    sh """
                        mkdir -p ${env.WORKSPACE_FILES}
                        mkdir -p ${env.WORKSPACE_FILES}/config
                        mkdir -p ${env.WORKSPACE_FILES}/packages
                        mkdir -p ${env.WORKSPACE_FILES}/backup
                    """
                    
                    // 处理配置文件
                    if (params.CONFIG_FILE) {
                        processUploadedFile('CONFIG_FILE', 'config', ['.yml', '.yaml', '.json', '.properties', '.xml'])
                    }
                    
                    // 处理部署包
                    if (params.DEPLOY_PACKAGE) {
                        processUploadedFile('DEPLOY_PACKAGE', 'packages', ['.war', '.jar', '.zip', '.tar.gz'])
                    }
                    
                    echo "✅ 文件处理完成"
                }
            }
        }
        
        stage('🔧 Configuration Processing') {
            when {
                expression { params.CONFIG_FILE != null && params.CONFIG_FILE != '' }
            }
            steps {
                script {
                    echo "=== 配置文件处理 ==="
                    
                    def configFile = "${env.WORKSPACE_FILES}/config/${params.CONFIG_FILE}"
                    
                    if (fileExists(configFile)) {
                        // 检查文件格式并处理
                        def fileExtension = configFile.split('\\.').last().toLowerCase()
                        
                        switch(fileExtension) {
                            case 'yml':
                            case 'yaml':
                                processYamlConfig(configFile)
                                break
                            case 'json':
                                processJsonConfig(configFile)
                                break
                            case 'properties':
                                processPropertiesConfig(configFile)
                                break
                            case 'xml':
                                processXmlConfig(configFile)
                                break
                            default:
                                echo "⚠️ 未知的配置文件格式: ${fileExtension}"
                        }
                    } else {
                        error("配置文件不存在: ${configFile}")
                    }
                }
            }
        }
        
        stage('📦 Package Processing') {
            when {
                expression { params.DEPLOY_PACKAGE != null && params.DEPLOY_PACKAGE != '' }
            }
            steps {
                script {
                    echo "=== 部署包处理 ==="
                    
                    def packageFile = "${env.WORKSPACE_FILES}/packages/${params.DEPLOY_PACKAGE}"
                    
                    if (fileExists(packageFile)) {
                        // 获取文件信息
                        def fileSize = sh(script: "stat -c%s '${packageFile}'", returnStdout: true).trim()
                        def fileMD5 = sh(script: "md5sum '${packageFile}' | cut -d' ' -f1", returnStdout: true).trim()
                        
                        echo "文件大小: ${fileSize} bytes"
                        echo "MD5 校验: ${fileMD5}"
                        
                        // 验证文件大小 (限制100MB)
                        if (fileSize.toLong() > 100 * 1024 * 1024) {
                            error("文件过大，超过100MB限制")
                        }
                        
                        // 根据文件类型处理
                        def fileExtension = packageFile.split('\\.').last().toLowerCase()
                        
                        switch(fileExtension) {
                            case 'zip':
                                processZipPackage(packageFile)
                                break
                            case 'war':
                                processWarPackage(packageFile)
                                break
                            case 'jar':
                                processJarPackage(packageFile)
                                break
                            case 'gz':
                                processTarGzPackage(packageFile)
                                break
                            default:
                                echo "ℹ️ 标准文件，无需特殊处理"
                        }
                        
                        // 保存文件元数据
                        writeFile file: "${env.WORKSPACE_FILES}/packages/${params.DEPLOY_PACKAGE}.metadata", 
                                  text: """filename=${params.DEPLOY_PACKAGE}
size=${fileSize}
md5=${fileMD5}
uploadTime=${env.BUILD_TIMESTAMP}
environment=${params.ENVIRONMENT}
version=${params.APP_VERSION}"""
                        
                    } else {
                        error("部署包文件不存在: ${packageFile}")
                    }
                }
            }
        }
        
        stage('🚀 Build & Test') {
            steps {
                script {
                    echo "=== 构建与测试 ==="
                    
                    // 模拟构建过程
                    echo "开始构建应用 ${params.APP_VERSION}..."
                    sleep(time: 2, unit: 'SECONDS')
                    
                    if (!params.SKIP_TESTS) {
                        echo "执行单元测试..."
                        sleep(time: 3, unit: 'SECONDS')
                        echo "✅ 测试通过"
                    } else {
                        echo "⚠️ 跳过测试阶段"
                    }
                    
                    echo "✅ 构建完成"
                }
            }
        }
        
        stage('🌍 Deploy to Environment') {
            steps {
                script {
                    echo "=== 部署到 ${params.ENVIRONMENT} 环境 ==="
                    
                    // 根据环境执行不同的部署逻辑
                    switch(params.ENVIRONMENT) {
                        case 'dev':
                            deployToDev()
                            break
                        case 'test':
                            deployToTest()
                            break
                        case 'staging':
                            deployToStaging()
                            break
                        case 'prod':
                            deployToProd()
                            break
                        default:
                            error("未支持的部署环境: ${params.ENVIRONMENT}")
                    }
                    
                    echo "✅ 部署完成"
                }
            }
        }
        
        stage('📋 Generate Report') {
            steps {
                script {
                    echo "=== 生成构建报告 ==="
                    
                    def report = generateBuildReport()
                    
                    // 保存报告
                    writeFile file: "${env.WORKSPACE}/build-report-${env.BUILD_TIMESTAMP}.md", 
                              text: report
                    
                    // 归档报告
                    archiveArtifacts artifacts: "build-report-${env.BUILD_TIMESTAMP}.md", 
                                   fingerprint: true
                    
                    echo "✅ 报告生成完成"
                }
            }
        }
    }
    
    post {
        always {
            echo "=== 构建清理 ==="
            
            // 备份重要文件
            script {
                if (fileExists("${env.WORKSPACE_FILES}")) {
                    sh """
                        tar -czf build-artifacts-${env.BUILD_TIMESTAMP}.tar.gz -C ${env.WORKSPACE_FILES} .
                        mv build-artifacts-${env.BUILD_TIMESTAMP}.tar.gz ${env.WORKSPACE}/
                    """
                    
                    archiveArtifacts artifacts: "build-artifacts-${env.BUILD_TIMESTAMP}.tar.gz", 
                                   fingerprint: true
                }
            }
            
            // 清理工作空间
            cleanWs(
                cleanWhenAborted: true,
                cleanWhenFailure: true,
                cleanWhenNotBuilt: true,
                cleanWhenSuccess: true,
                cleanWhenUnstable: true,
                deleteDirs: true
            )
        }
        
        success {
            echo "🎉 构建成功完成!"
            
            // 发送成功通知
            script {
                sendNotification('SUCCESS', "构建成功: ${params.APP_VERSION} 已部署到 ${params.ENVIRONMENT}")
            }
        }
        
        failure {
            echo "❌ 构建失败!"
            
            // 发送失败通知
            script {
                sendNotification('FAILURE', "构建失败: ${params.APP_VERSION} 部署到 ${params.ENVIRONMENT} 失败")
            }
        }
        
        unstable {
            echo "⚠️ 构建不稳定"
            
            script {
                sendNotification('UNSTABLE', "构建不稳定: ${params.APP_VERSION}")
            }
        }
    }
}

// ========== 自定义函数 ==========

/**
 * 处理上传的文件
 */
def processUploadedFile(paramName, targetDir, allowedExtensions) {
    echo "处理文件参数: ${paramName}"
    
    def filename = params[paramName]
    if (!filename) {
        echo "⚠️ 文件参数 ${paramName} 为空，跳过处理"
        return
    }
    
    // 验证文件扩展名
    def fileExtension = '.' + filename.split('\\.').last().toLowerCase()
    if (!(fileExtension in allowedExtensions)) {
        error("不支持的文件类型: ${fileExtension}，支持的类型: ${allowedExtensions}")
    }
    
    // 移动文件到目标目录
    def targetPath = "${env.WORKSPACE_FILES}/${targetDir}/${filename}"
    
    sh """
        if [ -f "${filename}" ]; then
            cp "${filename}" "${targetPath}"
            echo "文件已复制到: ${targetPath}"
        else
            echo "警告: 源文件不存在: ${filename}"
        fi
    """
    
    // 验证文件完整性
    if (fileExists(targetPath)) {
        def fileSize = sh(script: "stat -c%s '${targetPath}'", returnStdout: true).trim()
        echo "✅ 文件处理完成: ${filename} (${fileSize} bytes)"
    } else {
        error("❌ 文件处理失败: ${filename}")
    }
}

/**
 * 处理YAML配置文件
 */
def processYamlConfig(configFile) {
    echo "处理YAML配置文件: ${configFile}"
    
    // 验证YAML格式
    def yamlValid = sh(script: "python3 -c 'import yaml; yaml.safe_load(open(\"${configFile}\"))' 2>/dev/null", returnStatus: true)
    if (yamlValid != 0) {
        error("YAML格式验证失败")
    }
    
    // 读取配置内容
    def configContent = readFile(configFile)
    echo "YAML配置预览:"
    echo configContent.take(500) + (configContent.length() > 500 ? "..." : "")
}

/**
 * 处理JSON配置文件
 */
def processJsonConfig(configFile) {
    echo "处理JSON配置文件: ${configFile}"
    
    // 验证JSON格式
    def jsonValid = sh(script: "python3 -c 'import json; json.load(open(\"${configFile}\"))' 2>/dev/null", returnStatus: true)
    if (jsonValid != 0) {
        error("JSON格式验证失败")
    }
    
    def configContent = readFile(configFile)
    echo "JSON配置预览:"
    echo configContent.take(500) + (configContent.length() > 500 ? "..." : "")
}

/**
 * 处理Properties配置文件
 */
def processPropertiesConfig(configFile) {
    echo "处理Properties配置文件: ${configFile}"
    
    def configContent = readFile(configFile)
    echo "Properties配置预览:"
    echo configContent.take(500) + (configContent.length() > 500 ? "..." : "")
}

/**
 * 处理XML配置文件
 */
def processXmlConfig(configFile) {
    echo "处理XML配置文件: ${configFile}"
    
    // 验证XML格式
    def xmlValid = sh(script: "xmllint --noout '${configFile}' 2>/dev/null", returnStatus: true)
    if (xmlValid != 0) {
        echo "⚠️ XML格式验证失败或xmllint不可用"
    }
    
    def configContent = readFile(configFile)
    echo "XML配置预览:"
    echo configContent.take(500) + (configContent.length() > 500 ? "..." : "")
}

/**
 * 处理ZIP包
 */
def processZipPackage(packageFile) {
    echo "处理ZIP包: ${packageFile}"
    
    // 列出ZIP内容
    sh "unzip -l '${packageFile}' || true"
    
    // 解压到临时目录
    def extractDir = "${env.WORKSPACE_FILES}/extracted/${env.BUILD_TIMESTAMP}"
    sh """
        mkdir -p '${extractDir}'
        unzip -q '${packageFile}' -d '${extractDir}'
        echo "解压完成到: ${extractDir}"
    """
}

/**
 * 处理WAR包
 */
def processWarPackage(packageFile) {
    echo "处理WAR包: ${packageFile}"
    
    // 检查WAR包结构
    sh "jar -tf '${packageFile}' | head -20"
    
    // 验证WAR包
    def warValid = sh(script: "jar -tf '${packageFile}' | grep -q 'WEB-INF/web.xml'", returnStatus: true)
    if (warValid != 0) {
        echo "⚠️ 警告: 未发现标准的WAR包结构"
    }
}

/**
 * 处理JAR包
 */
def processJarPackage(packageFile) {
    echo "处理JAR包: ${packageFile}"
    
    // 检查JAR包信息
    sh "jar -tf '${packageFile}' | head -20"
    
    // 检查MANIFEST.MF
    def manifestExists = sh(script: "jar -tf '${packageFile}' | grep -q 'META-INF/MANIFEST.MF'", returnStatus: true)
    if (manifestExists == 0) {
        echo "✅ 发现MANIFEST.MF文件"
    }
}

/**
 * 处理TAR.GZ包
 */
def processTarGzPackage(packageFile) {
    echo "处理TAR.GZ包: ${packageFile}"
    
    // 列出压缩包内容
    sh "tar -tzf '${packageFile}' | head -20"
}

/**
 * 部署到开发环境
 */
def deployToDev() {
    echo "🔧 部署到开发环境"
    
    // 模拟部署过程
    sleep(time: 2, unit: 'SECONDS')
    
    echo "✅ 开发环境部署完成"
}

/**
 * 部署到测试环境
 */
def deployToTest() {
    echo "🧪 部署到测试环境"
    
    // 测试环境部署逻辑
    sleep(time: 3, unit: 'SECONDS')
    
    echo "✅ 测试环境部署完成"
}

/**
 * 部署到预发布环境
 */
def deployToStaging() {
    echo "🎭 部署到预发布环境"
    
    // 预发布环境需要更多验证
    sleep(time: 4, unit: 'SECONDS')
    
    echo "✅ 预发布环境部署完成"
}

/**
 * 部署到生产环境
 */
def deployToProd() {
    echo "🚀 部署到生产环境"
    
    // 生产环境部署需要审批
    timeout(time: 5, unit: 'MINUTES') {
        input message: '确认部署到生产环境?', 
              ok: '确认部署',
              submitterParameter: 'APPROVER'
    }
    
    echo "部署审批人: ${env.APPROVER}"
    sleep(time: 5, unit: 'SECONDS')
    
    echo "✅ 生产环境部署完成"
}

/**
 * 生成构建报告
 */
def generateBuildReport() {
    def report = """# 构建报告

## 基本信息
- **构建号**: ${env.BUILD_NUMBER}
- **构建时间**: ${env.BUILD_TIMESTAMP}
- **应用版本**: ${params.APP_VERSION}
- **部署环境**: ${params.ENVIRONMENT}
- **跳过测试**: ${params.SKIP_TESTS}

## 文件信息
- **配置文件**: ${params.CONFIG_FILE ?: '无'}
- **部署包**: ${params.DEPLOY_PACKAGE ?: '无'}

## 构建说明
${params.BUILD_NOTES ?: '无额外说明'}

## 构建状态
- **状态**: ${currentBuild.result ?: 'SUCCESS'}
- **持续时间**: ${currentBuild.durationString}

---
*报告生成时间: ${new Date()}*
"""
    
    return report
}

/**
 * 发送通知
 */
def sendNotification(status, message) {
    echo "📧 发送通知: ${status} - ${message}"
    
    // 这里可以集成邮件、Slack、钉钉等通知方式
    // 示例：
    // emailext (
    //     subject: "Jenkins Build ${status}: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
    //     body: message,
    //     to: "${env.CHANGE_AUTHOR_EMAIL}"
    // )
}