# LinkHaiTao 导航提取 - 断点续传 (Resume Mode)

**目标**：继续完成未完成的导航菜单点击测试。

**前置条件**：
- 浏览器已打开。
- 用户已登录。
- 当前页面应为 Dashboard (`https://www.linkhaitao.com/dashboard`)。

## ⚠️ 关键规则
1. **强制等待**：`click` 后 `wait(1)`，`go_to_url` 后 `wait(2)`。
2. **两阶段执行**：点击和记录分开执行，防止幻觉。
3. **禁止中间 Index**：仅 Action List 的首个动作允许使用 `click_element_by_index`。

---

## 🚀 执行步骤

### 1. 初始化
1. **确认状态**：调用 `get_current_url()`。
2. **归位**：如果当前 URL 不是 Dashboard，请调用 `go_to_url("https://www.linkhaitao.com/dashboard")` 并等待页面加载。

### 2. 导航点击遍历 (两阶段循环)
**文件名常量**：`nav_task_20260206_113656.json`

**必须严格遵守以下 Phase 1 -> Phase 2 的循环：**

**第一轮：执行与观测 (Phase 1)**
1.  **获取任务**：
    - 调用 `get_next_task(filename="nav_task_20260206_113656.json")`。
    - **如果返回 "ALL_TASKS_COMPLETED" 或空**：说明所有任务已完成，**结束任务**。
    - **如果返回任务**：获取 `node_path` (例如 `["Tools", "Global Postback Editing"]`) 和 `task_id`。

2.  **执行点击 (Atomic Execution)**：
    - **必须**在一个 Step 内提交以下动作序列：
    - **模式**：`click_element_by_index(...)` (仅限首位) -> `wait(1)` -> `click_text(目标菜单名)` -> `wait(2)` -> `get_current_url()`。
    - **示例**：
      `click_element_by_index(16)` -> `wait(1)` -> `click_text("Global Postback Editing")` -> `wait(2)` -> `get_current_url()`
    - **注意**：
      - 如果菜单项名称包含 "Add/Edit/Delete/Upload/New"，**不要点击**，直接进行下一步标记为 Skipped。
      - 本轮**禁止**调用 `update_task_status`。

3.  **【停止】**：本轮结束，观察日志中的 Warning 或 Success 信息。

**第二轮：记录与归位 (Phase 2)**
1.  **状态核销**：
    - 读取上一轮 `get_current_url` 的结果 (如果失败或未跳转，则视为 "done" 或 "skipped")。
    - 调用 `update_task_status(filename="nav_task_20260206_113656.json", task_id=..., status="done", result_url="...")`。
2.  **归位**：
    - `go_to_url("https://www.linkhaitao.com/dashboard")` -> `wait(2)`。
3.  **循环**：
    - 回到 Phase 1。

### 3. 结束
当 `get_next_task` 返回完成时，输出 "Mission Complete: All pending tasks processed."。
