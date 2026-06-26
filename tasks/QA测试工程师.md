【强制技能 — webapp-testing · systematic-debugging · verification-before-completion】
────────────────────────

T-P2-1：全站回归测试

今天完成了5个commit的大量改动，需要做回归测试验证没有引入新Bug：

需要验证的功能清单：
1. 主题系统（4套切换无闪烁/编辑器可读/滚动条适配）
2. 角色面板（三个标签按钮→插入光标位置）
3. 回收站（删除→deletedAt记录→30天清理）
4. 卷管理（重命名/删除/未分类章节/旧数据兼容）
5. 导入TXT（选文件→自动分章→确认导入→批量创建章节）
6. 全本导出（合并所有章节→下载TXT）
7. AI超时（触发超时→显示⏱️提示）
8. AI重试（网络失败→自动重试3次）
9. 6页面内容（works/features/templates/tools/cases/library有真实内容）
10. 登录/注册（Mock模式正常）
11. 基础功能回归（编辑器/章节CRUD/合规检测/脑洞喷射）

验证：启动dev服务器手动测试
输出：output/QA-全站回归测试.md
Bug标记到 D:\建网站\mojing-docs\Bug主清单.md
