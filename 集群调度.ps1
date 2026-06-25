# 墨境 Agent 集群 — 调度脚本
# 用法：PowerShell 运行此脚本 → 自动更新所有角色任务文件

$team = @(
    @{name='前端技术负责人';   file='D:\建网站\mojing-docs\tasks\前端技术负责人.md'},
    @{name='后端技术负责人';   file='D:\建网站\mojing-docs\tasks\后端技术负责人.md'},
    @{name='UI设计师';         file='D:\建网站\mojing-docs\tasks\UI设计师.md'},
    @{name='UX体验员';         file='D:\建网站\mojing-docs\tasks\UX体验员.md'},
    @{name='QA测试工程师';     file='D:\建网站\mojing-docs\tasks\QA测试工程师.md'},
    @{name='提示词系统专家';   file='D:\建网站\mojing-docs\tasks\提示词系统专家.md'},
    @{name='产品经理';         file='D:\建网站\mojing-docs\tasks\产品经理.md'},
    @{name='架构审查员';       file='D:\建网站\mojing-docs\tasks\架构审查员.md'}
)

Write-Host @"
==================== 墨境 Agent 集群 ====================

当前任务分配：

  后端    → Supabase 数据库 + NextAuth 真实登录
  前端    → AI超时 + 垃圾桶 + 卷管理 + 导入TXT  
  UI      → 等前端完成
  UX      → 等前端完成
  QA      → 等前端完成
  提示词  → 等待中
  产品    → 等待中
  架构    → 等待中

======================================================
"@ -ForegroundColor Green

Write-Host "任务文件已就绪。去各对话窗口说：查收任务" -ForegroundColor Yellow
Write-Host ""

# 显示各角色状态
foreach ($r in $team) {
    $f = $r.file
    if (Test-Path $f) {
        $size = (Get-Item $f).Length
        $time = (Get-Item $f).LastWriteTime.ToString('HH:mm')
        Write-Host "  $($r.name) — $time ($($size)字节)" -ForegroundColor Gray
    } else {
        Write-Host "  $($r.name) — ❌ 文件不存在" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "按 Enter 打开任务目录..." -ForegroundColor Gray
$null = Read-Host
explorer "D:\建网站\mojing-docs\tasks"
