#!/usr/bin/env groovy

// ========================================
// Groovy 循环示例
// ========================================

println "🔄 Groovy 循环示例演示"
println "=" * 50

// 1. 传统 for 循环
println "\n1. 传统 for 循环:"
for (int i = 0; i < 5; i++) {
    println "传统循环: i = $i"
}

// 2. Groovy 风格的 for 循环（范围）
println "\n2. Groovy 范围循环:"
for (i in 1..5) {
    println "范围循环: i = $i"
}

// 3. 倒序循环
println "\n3. 倒序循环:"
for (i in 5..1) {
    println "倒序循环: i = $i"
}

// 4. 步长循环
println "\n4. 步长循环 (step 2):"
for (i in 0..10) {
    if (i % 2 == 0) {
        println "步长循环: i = $i"
    }
}

// 更简洁的步长写法
println "\n4b. 使用 step 方法:"
(0..10).step(2) { i ->
    println "step方法: i = $i"
}

// 5. 遍历列表
println "\n5. 遍历列表:"
def fruits = ['苹果', '香蕉', '橘子', '葡萄']

// 传统方式
for (fruit in fruits) {
    println "水果: $fruit"
}

// 6. 使用 each 方法遍历列表
println "\n6. 使用 each 方法:"
fruits.each { fruit ->
    println "each方法 - 水果: $fruit"
}

// 7. 使用 eachWithIndex 获取索引
println "\n7. 使用 eachWithIndex:"
fruits.eachWithIndex { fruit, index ->
    println "索引 $index: $fruit"
}

// 8. 遍历 Map
println "\n8. 遍历 Map:"
def person = [
    name: '张三',
    age: 30,
    city: '北京',
    job: '程序员'
]

// 遍历 Map 的 key-value
person.each { key, value ->
    println "$key: $value"
}

// 9. while 循环
println "\n9. while 循环:"
def count = 0
while (count < 3) {
    println "while循环: count = $count"
    count++
}

// 10. times 方法
println "\n10. times 方法:"
5.times { i ->
    println "times方法: 第 ${i + 1} 次执行"
}

// 11. upto 方法
println "\n11. upto 方法:"
1.upto(5) { i ->
    println "upto方法: i = $i"
}

// 12. downto 方法
println "\n12. downto 方法:"
5.downto(1) { i ->
    println "downto方法: i = $i"
}

// 13. 嵌套循环
println "\n13. 嵌套循环 - 乘法表:"
(1..3).each { i ->
    (1..3).each { j ->
        print "${i} × ${j} = ${i * j}\t"
    }
    println ""
}

// 14. 条件中断循环
println "\n14. 条件中断循环:"
for (i in 1..10) {
    if (i == 5) {
        println "遇到 5，跳出循环"
        break
    }
    println "循环中: i = $i"
}

// 15. 跳过当前迭代
println "\n15. 跳过偶数:"
for (i in 1..10) {
    if (i % 2 == 0) {
        continue  // 跳过偶数
    }
    println "奇数: i = $i"
}

// 16. 使用 findAll 过滤
println "\n16. 使用 findAll 过滤偶数:"
def numbers = (1..10).toList()
def evenNumbers = numbers.findAll { it % 2 == 0 }
evenNumbers.each { num ->
    println "偶数: $num"
}

// 17. 使用 collect 转换
println "\n17. 使用 collect 转换 (平方):"
def squares = (1..5).collect { it * it }
squares.each { square ->
    println "平方: $square"
}

// 18. 多维数组循环
println "\n18. 多维数组循环:"
def matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]

matrix.eachWithIndex { row, rowIndex ->
    row.eachWithIndex { value, colIndex ->
        println "matrix[$rowIndex][$colIndex] = $value"
    }
}

// 19. 字符串遍历
println "\n19. 字符串遍历:"
def text = "Hello"
text.each { char ->
    println "字符: $char"
}

// 20. 文件行遍历示例
println "\n20. 创建临时文件并遍历:"
def tempFile = File.createTempFile("example", ".txt")
tempFile.withWriter { writer ->
    writer.writeLine("第一行")
    writer.writeLine("第二行")
    writer.writeLine("第三行")
}

tempFile.eachLine { line, lineNumber ->
    println "行 $lineNumber: $line"
}

// 清理临时文件
tempFile.delete()

// 21. 无限循环示例（小心使用）
println "\n21. 有限制的循环:"
def counter = 0
while (true) {
    counter++
    println "计数器: $counter"
    if (counter >= 3) {
        println "达到限制，退出循环"
        break
    }
}

// 22. 使用 any 和 every
println "\n22. 集合条件检查:"
def nums = [2, 4, 6, 8, 10]

// 检查是否有偶数
if (nums.any { it % 2 == 0 }) {
    println "列表中有偶数"
}

// 检查是否全是偶数
if (nums.every { it % 2 == 0 }) {
    println "列表中全是偶数"
}

// 23. 循环中的异常处理
println "\n23. 循环中的异常处理:"
def data = [1, 2, 0, 4, 5]
data.each { num ->
    try {
        def result = 10 / num
        println "10 / $num = $result"
    } catch (ArithmeticException e) {
        println "除零错误: 跳过 $num"
    }
}

println "\n" + "=" * 50
println "✅ Groovy 循环示例演示完成!"