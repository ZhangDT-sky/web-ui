# Linkbux 导航提取任务 

**目标**：登录并提取导航栏的所有菜单项及 URL。

## 关键操作 (必须遵守)

1. **Dashboard**：登录后的页面即为 Dashboard，**不要点击 Dashboard**，直接从第二个菜单开始。
2. **悬停触发**：所有菜单必须用 `hover_text("名称")` 触发。
3. **强制等待**：
   - `hover_text` 后：`wait(1)`
   - `click_text` 后：`wait(2)`
   - `go_back` 后：**必须 wait(2)** (等待页面完全加载)

4. **索引点击规则 (Index Rules)**：
   - **允许**作为 Step 的**第一个动作**使用 `click_element_by_index`。
   - **严禁**在动作列表（Action List）中间使用 `click_element_by_index`。中途必须使用 `hover_text` 或 `click_text`。

---

## 执行步骤

### 1. 登录
- URL: `https://www.linkbux.com/login`
- 用户: `hucen` / 密码: `qwer@1234`
- 登录后检查 URL 是否包含 `/publisher`

### 2. 获取导航栏结构 (静态分析)
1. **仔细观察**侧边栏菜单，提取一级菜单、二级菜单和三级菜单的层级结构。
2. **保存**：立即调用 `save_navigation_structure(structure=...)` 将提取到的 JSON 结构保存到任务数据库中。
3. **格式示例** (仅用于理解):
   ```json
   [
     {"name": "Reports", "path": ["Reports"], "children": [
       {"name": "Performance", "path": ["Reports", "Performance"]}, 
       {"name": "Conversion Report", "path": ["Reports", "Conversion Report"]}
     ]}
   ]
   ```
4. **初始化**：保存成功后，准备进入 Step 3。

### 3. 导航点击遍历 (两阶段模式)
**为了确保稳定性，严禁将点击和归位合并在一个 Step 中。请严格分两轮执行：**

**第一轮:执行与观测 (Phase 1)**
1.  **获取任务 (第一且唯一的起始动作)**：
    - **必须**作为 Phase 1 的第一个动作调用 `get_next_task()`。
    - **严禁**在未调用 `get_next_task()` 的情况下执行任何 `click_text`、`hover_text` 等操作。
    - **严禁**凭借 Memory 或上下文推测下一个任务，必须通过 `get_next_task()` 获取明确指令。
    - 如果返回空，则跳转到 Step 4。
    
2.  **执行点击 (Atomic Execution)**：
    - **必须**在一个 Step 内提交以下动作序列：
    - **三级菜单**：`click_text("一级")` (或 hover) -> `wait(1)` -> `click_text("二级")` (或 hover) -> `wait(1)` -> `click_text("三级")` -> `wait(2)` -> `get_current_url()`
    - **二级菜单**：`click_text("一级")` (或 hover) -> `wait(1)` -> `click_text("二级")` -> `wait(2)` -> `get_current_url()`
    - **一级菜单**：`click_text("一级")` -> `wait(2)` -> `get_current_url()`
    - **禁止**：本轮**不要**调用 `go_back` 或 `update_task_status`。
    - **禁止**：**严禁**使用 `scroll` 或 `extract_content` 尝试寻找元素。如果找不到目标元素，直接失败并进入 Phase 2。
    
3.  **【停止】**：本轮结束，等待观察页面跳转结果。

**第二轮：记录与归位 (Phase 2)**
1.  **强制核销 (Mandatory Update)**：
    -   即使 URL **没有变化**（如只是展开了菜单），也**必须**调用 `update_task_status(..., status="done", result_url="当前URL")`。
    -   **严禁连续操作！** 完成一个菜单项后，**禁止**直接凭记忆（Memory）去点下一个。
    -   **必须**调用 `update_task_status` 才能结束当前 Task。

2.  **归位 (Reset)**：
    -   调用 `go_to_url("https://www.linkbux.com/publisher/dashboard")` -> `wait(2)`。
    -   **严禁**使用 `go_back()`，防止回退到登录页。

3.  **循环**：
    - 回到 Phase 1，重新调用 `get_next_task()` 获取新指令。

### 4. 输出
当 `get_next_task()` 返回完成时，任务结束。
