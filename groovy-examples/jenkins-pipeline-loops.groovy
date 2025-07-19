// Jenkins Pipeline 中的 Groovy 循环示例

pipeline {
    agent any
    
    environment {
        ENVIRONMENTS = 'dev,test,staging,prod'
        SERVICES = 'api,web,database'
    }
    
    stages {
        stage('基础循环示例') {
            steps {
                script {
                    // 1. 遍历环境列表
                    def envs = env.ENVIRONMENTS.split(',')
                    envs.each { environment ->
                        echo "部署到环境: ${environment}"
                    }
                    
                    // 2. 使用 for 循环
                    for (int i = 1; i <= 3; i++) {
                        echo "构建步骤 ${i}"
                    }
                    
                    // 3. 范围循环
                    for (buildNum in 1..5) {
                        echo "构建编号: ${buildNum}"
                    }
                }
            }
        }
        
        stage('并行构建多个服务') {
            steps {
                script {
                    def services = env.SERVICES.split(',')
                    def parallelStages = [:]
                    
                    // 创建并行任务
                    services.each { service ->
                        parallelStages["构建 ${service}"] = {
                            echo "开始构建服务: ${service}"
                            sleep(2) // 模拟构建时间
                            echo "完成构建服务: ${service}"
                        }
                    }
                    
                    // 执行并行任务
                    parallel parallelStages
                }
            }
        }
        
        stage('循环部署到多环境') {
            steps {
                script {
                    def environments = ['dev', 'test', 'staging']
                    def services = ['api', 'web']
                    
                    // 嵌套循环：每个环境部署每个服务
                    environments.each { env ->
                        echo "=== 部署到 ${env} 环境 ==="
                        services.each { service ->
                            echo "部署 ${service} 到 ${env}"
                            // 这里可以调用部署脚本
                            sh "echo '部署 ${service} 到 ${env} 环境'"
                        }
                    }
                }
            }
        }
        
        stage('条件循环和错误处理') {
            steps {
                script {
                    def testCases = [
                        [name: 'unit_test', required: true],
                        [name: 'integration_test', required: true],
                        [name: 'performance_test', required: false],
                        [name: 'security_test', required: false]
                    ]
                    
                    def failedTests = []
                    
                    testCases.each { test ->
                        try {
                            echo "执行测试: ${test.name}"
                            
                            // 模拟测试执行
                            def success = Math.random() > 0.3 // 70% 成功率
                            
                            if (!success) {
                                throw new Exception("测试失败: ${test.name}")
                            }
                            
                            echo "✅ ${test.name} 通过"
                            
                        } catch (Exception e) {
                            echo "❌ ${test.name} 失败: ${e.getMessage()}"
                            
                            if (test.required) {
                                failedTests.add(test.name)
                            } else {
                                echo "⚠️ ${test.name} 失败但非必需，继续执行"
                            }
                        }
                    }
                    
                    // 检查是否有必需测试失败
                    if (failedTests.size() > 0) {
                        error("必需测试失败: ${failedTests.join(', ')}")
                    }
                }
            }
        }
        
        stage('矩阵构建') {
            steps {
                script {
                    def platforms = ['linux', 'windows', 'macos']
                    def versions = ['java8', 'java11', 'java17']
                    def parallelBuilds = [:]
                    
                    // 创建矩阵构建任务
                    platforms.each { platform ->
                        versions.each { version ->
                            def buildName = "${platform}-${version}"
                            parallelBuilds[buildName] = {
                                echo "构建 ${buildName}"
                                // 模拟构建
                                sh "echo '在 ${platform} 上使用 ${version} 构建'"
                                sleep(1)
                                echo "完成 ${buildName} 构建"
                            }
                        }
                    }
                    
                    // 执行所有矩阵构建
                    parallel parallelBuilds
                }
            }
        }
        
        stage('文件处理循环') {
            steps {
                script {
                    // 创建测试文件
                    sh '''
                        mkdir -p test-files
                        echo "文件1内容" > test-files/file1.txt
                        echo "文件2内容" > test-files/file2.txt
                        echo "文件3内容" > test-files/file3.txt
                    '''
                    
                    // 遍历文件
                    def files = sh(
                        script: 'ls test-files/*.txt',
                        returnStdout: true
                    ).trim().split('\n')
                    
                    files.each { file ->
                        echo "处理文件: ${file}"
                        def content = readFile(file)
                        echo "文件内容: ${content}"
                    }
                    
                    // 清理
                    sh 'rm -rf test-files'
                }
            }
        }
        
        stage('重试循环') {
            steps {
                script {
                    def maxRetries = 3
                    def success = false
                    
                    for (int attempt = 1; attempt <= maxRetries; attempt++) {
                        try {
                            echo "尝试 ${attempt}/${maxRetries}"
                            
                            // 模拟可能失败的操作
                            def random = Math.random()
                            if (random < 0.7) { // 30% 成功率
                                throw new Exception("操作失败")
                            }
                            
                            echo "✅ 操作成功!"
                            success = true
                            break
                            
                        } catch (Exception e) {
                            echo "❌ 尝试 ${attempt} 失败: ${e.getMessage()}"
                            
                            if (attempt < maxRetries) {
                                echo "等待 2 秒后重试..."
                                sleep(2)
                            }
                        }
                    }
                    
                    if (!success) {
                        error("所有重试均失败")
                    }
                }
            }
        }
        
        stage('动态阶段创建') {
            steps {
                script {
                    def microservices = [
                        'user-service',
                        'order-service', 
                        'payment-service',
                        'notification-service'
                    ]
                    
                    // 为每个微服务创建构建和测试阶段
                    microservices.eachWithIndex { service, index ->
                        stage("构建 ${service}") {
                            echo "=== 构建微服务: ${service} ==="
                            
                            // 模拟构建步骤
                            def steps = ['编译', '单元测试', '打包', '上传镜像']
                            steps.each { step ->
                                echo "执行 ${step} for ${service}"
                                sleep(1)
                            }
                            
                            echo "✅ ${service} 构建完成"
                        }
                    }
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "=== 构建报告 ==="
                
                def results = [
                    'total_stages': 8,
                    'successful_stages': 8,
                    'failed_stages': 0
                ]
                
                results.each { key, value ->
                    echo "${key}: ${value}"
                }
            }
        }
    }
}

// ========================================
// 单独的 Groovy 函数示例
// ========================================

def deployToEnvironments(environments, service) {
    environments.each { env ->
        echo "部署 ${service} 到 ${env}"
        // 实际部署逻辑
    }
}

def runTestSuite(tests) {
    def results = [:]
    
    tests.each { test ->
        try {
            // 运行测试
            results[test] = 'PASSED'
        } catch (Exception e) {
            results[test] = 'FAILED'
        }
    }
    
    return results
}

def processFilesInDirectory(directory, extension) {
    def files = sh(
        script: "find ${directory} -name '*.${extension}'",
        returnStdout: true
    ).trim().split('\n')
    
    def processedFiles = []
    
    files.each { file ->
        if (file.trim()) {
            echo "处理文件: ${file}"
            processedFiles.add(file)
        }
    }
    
    return processedFiles
}