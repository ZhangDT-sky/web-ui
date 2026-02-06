# LinkHaiTao 导航提取任务 

**目标**：登录并提取导航栏的所有菜单项及 URL，使用**文件持久化**来管理任务状态，确保无遗漏、无重复。

## ⚠️ 关键操作 (必须遵守)
1. **强制等待**：
   - `click_text` 后：`wait(1)`
   - `go_back` 后：**必须 wait(3)** (等待页面完全加载)
2. **状态管理**：必须使用 `save_navigation_structure`、`get_next_task` 和 `update_task_status` 来驱动流程。
3. 在 Step 2 之后，**严禁**凭此前的上下文记忆去点击，**必须**依赖 `get_next_task` 返回的内容。

---

## 🚀 执行步骤

### 1. 登录
- URL: `https://www.linkhaitao.com/user/login`
- 用户: `pangpang` / 密码: `admin123`
- 输入验证码
- 点击登录按钮
- 检查是否进入主页 (`https://www.linkhaitao.com/dashboard`)

### 2. 获取并保存结构 (初始化)
1. **观察**：侧边栏是展开的（能看到文字）还是折叠的（只看到图标）？
2. **行动**：
   - 如果是**折叠状态**：查找并点击 "Toggle", "Collapse", "Menu" 或 ☰ 等图标按钮，直到侧边栏展开并显示文字。
   - 如果已展开：跳过此步。
3. **仔细观察**侧边栏菜单，提取完整的导航树结构（JSON）。
4. **立即调用**工具 `save_navigation_structure(json_structure)` 将结构保存到文件。
5. **记住**工具返回的文件名 (例如: `nav_task_20260204_120000.json`)，这是后续所有操作的凭证。

### 3. 持久化遍历循环 (分步执行策略)
**必须将单次循环拆分为两轮独立的对话 (Two-Phase Execution)，严禁在一个 Step 内完成所有操作。**

**第一轮：执行与观测 (Phase 1)**
1. **获取任务**：`get_next_task(filename)`。
2. **执行点击 (Hierarchical Strategy)**：
   - **原子化操作**：必须按照路径层级依次点击。
   - **功能按钮过滤**：如果任务名称匹配 `^(Add|Edit|Delete|Upload|New|Copy|Save|Submit|Cancel).*`，**跳过此任务**，标记为 "skipped"，不要点击。
   - **如果 Path 长度 > 1 (如 ["Tools", "Link Generator"])**：
     - `click_text(path[0])` (点击一级菜单，确保展开) -> `wait(1)` -> `click_text(path[1])` (点击目标) -> `wait(1)`。
   - **如果 Path 长度 = 1**：
     - `click_text(path[0])` -> `wait(1)`。
   - **严禁**直接点击子菜单而跳过父菜单。
3. **观测 URL**：调用 `get_current_url()`。
4. **【停止】**：不要在这一轮调用 `update_task_status`，等待观察结果。

**第二轮：记录与归位 (Phase 2)**
1. **读取 URL**：查看上一轮 `get_current_url` 返回的字符串。
2. **状态核销**：调用 `update_task_status(filename, task_id, "done", result_url="上一步的URL")`。
3. **归位**：调用 `go_to_url("https://www.linkhaitao.com/dashboard")` -> `wait(3)`。
   - **重要**：使用绝对跳转代替 `go_back`，防止因点击未产生历史记录而回退到登录页。

**循环上述两轮操作，直到 `get_next_task` 返回 "ALL_TASKS_COMPLETED"。**

### 4. 结束与输出
- 当 `get_next_task` 返回 "ALL_TASKS_COMPLETED" 时：
- 读取该 JSON 文件的最终内容。
- 使用 `AgentOutput` 输出最终结果。
