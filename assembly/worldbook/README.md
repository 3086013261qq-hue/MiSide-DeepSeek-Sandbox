# 米鲸｜咩咩全栈 v1.0.0 世界书装配

## 来源
- 远程 main 最新封版正文：7条BLUE、3条GREEN、22条CHAR、五卷151事件、19条LOC。
- 工具口径：咩咩制卡·全栈 v1.0.0 的 templates/fullcard.md 和《同人角色卡通用创作母版2.0.0》。
- 不修改任何上述封版正文；不使用MVU、单独能力层或额外剧情导演。

## 结构
- 7组分区与14个起止空标记；
- 556清空局部变量；记忆三槽保留但默认关闭；
- 五卷时间线独立保存，仅第一卷开启；@Depth 0；
- 日常解谜推演、简洁状态栏、开放话题池、开放沙盒规则；
- 七篇蓝灯常驻；三篇设定绿灯按story_scene触发；
- 22篇角色按角色名与AI名合并触发（含Bing/Copilot共享故障米塔；多莉无AI），只扫描story_scene；
- 19处地点只从status的当前位置识别；
- 绿灯/角色/地点双防递归均开启；蓝灯不启用双防递归。

## 构建
python assembly/worldbook/build_worldbook.py

产物：
- assembly/worldbook/dist/米鲸_character_book.json
- assembly/worldbook/dist/米鲸_worldbook_build_report.json

仓库Action在脚本/正文变更时运行并提交上述产物，构建中若有别名串位、状态栏缺字段、顺序/数量冲突会失败。构建通过不等同于Android或SillyTavern实机可见性与触发验证。

严格不要把 README、QA、规划、研究文档或工作流写入正式世界书 entries。人物与地点SRC不重写，时间线只提取原有world_timeline块，不复制文件头说明。

下一步：生成最终CCV3卡体、嵌入此character_book，并进行实机导入核对。