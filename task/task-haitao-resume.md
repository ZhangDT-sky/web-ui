# Linkbux 导航提取 - 断点续传 (Resume Mode)

**目标**：继续完成 Linkbux 未完成的导航菜单点击测试。

**前置条件**：
- 浏览器已打开。
- 用户已登录 Linkbux。
- 当前页面应为 Dashboard (`https://www.linkbux.com/publisher` 或类似)。

---

## 🚀 执行步骤

### 1. 初始化
1. **归位**：如果当前不是 Dashboard，请调用 `go_to_url("https://www.linkbux.com/publisher")` 并等待页面加载。

### 2. 导航点击遍历 (两阶段循环)
**文件名常量**：`nav_task_20260211_105537.json`

**必须严格遵守以下 Phase 1 -> Phase 2 的循环：**

**第一轮：执行与观测 (Phase 1)**
1.  **获取任务**：
    - 调用 `get_next_task(filename="nav_task_20260211_105537.json")`。
    - **如果返回任务**：获取 `node_path` (例如 `["Reports", "Performance"]`)。
    - **如果返回空**：任务结束。

2.  **执行点击 (Atomic Execution)**：
    - 根据菜单层级，**必须**在一个 Step 内提交完整的动作序列：
    - **三级菜单**：`click_element_by_text("一级")` (或 hover) -> `wait(1)` -> `click_element_by_text("二级")` (或 hover) -> `wait(1)` -> `click_element_by_text("三级")` -> `wait(2)` -> `get_current_url()`
    - **二级菜单**：`click_element_by_text("一级")` (或 hover) -> `wait(1)` -> `click_element_by_text("二级")` -> `wait(2)` -> `get_current_url()`
    - **一级菜单**：`click_element_by_text("一级")` -> `wait(2)` -> `get_current_url()`
    - **禁止**：本轮**不要**调用 `go_back` 或 `update_task_status`。

3.  **【停止】**：本轮结束，等待观察页面跳转结果。

**第二轮：记录与归位 (Phase 2)**
1.  **状态核销**：
    - 调用 `update_task_status(filename="nav_task_20260211_105537.json", task_id=..., status="done", result_url="上一轮提取的URL")`。
2.  **归位**：
    - 调用 `go_to_url("https://www.linkbux.com/publisher")` -> `wait(2)`。
3.  **循环**：
    - 回到 Phase 1。

### 3. 结束
当 `get_next_task` 返回完成时，输出 "Linkbux Navigation Task Completed."。
