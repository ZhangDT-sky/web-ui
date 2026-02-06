# LinkHaiTao 导航提取任务 (Classic Mode)

**目标**：登录并提取导航栏的所有菜单项及 URL。

## ⚠️ 关键操作 (必须遵守)
1. **强制等待**：
   - `click_text` 后：`wait(1)`
   - `go_to_url` 后：`wait(1)`
   - 提取结构前：`wait(2)`
2. **绝对归位**：
   - 每次任务完成后，必须使用 `go_to_url("https://www.linkhaitao.com/dashboard")` 回到主页。不要使用 `go_back()`，防止回退到登录页。
3. **禁止**：
   - **禁止**凭空猜想，必须基于 Step 2 看到的实际结构执行。
   - **禁止**在动作列表（Action List）中间使用 `click_element_by_index`。该工具**仅允许**作为 Step 的第一个动作使用。
     - ✅ **正确**：`click_element_by_index(10)` -> `click_text("Submenu")` (Index 在首位，安全)
     - ❌ **错误**：`click_text("Menu")` -> `click_element_by_index(10)` (Index 在中间，**绝对禁止**！因为点击 "Menu" 后 DOM 结构变了，原 Index 10 可能指向错误的元素)

---

## 🚀 执行步骤

### 1. 登录
- URL: `https://www.linkhaitao.com/user/login`
- 用户: `pangpang`
- 密码: `admin123`
- 操作：
  - 输入用户名和密码。
  - 点击登录按钮。
  - 登录后检查 URL 是否包含 `/dashboard`。

### 2. 获取导航栏结构
1. **观察**：侧边栏是展开的吗？如果是折叠的（只显示图标），请先点击 "Toggle" 或 "Menu" 图标展开。
2. **提取**：仔细观察侧边栏，提取完整的导航树结构（包含一级、二级、三级菜单）。
3. **立即调用**工具 `save_navigation_structure(json_structure)` 将结构保存到文件。
4. **记住**工具返回的文件名 (例如: `nav_task_20260204_120000.json`)，这是后续所有操作的凭证。
5. **格式示例**:
   ```json
   [
     {"name": "Reports", "path": ["Reports"], "children": [
       {"name": "Performance", "path": ["Reports", "Performance"]}, 
       {"name": "Conversion Report", "path": ["Reports", "Conversion Report"]}
     ]}
   ]
   ```
6. **初始化**：保存成功后，Agent 会自动获得第一个待办任务。准备进入 Step 3。

### 3. 导航点击遍历 (两阶段模式)
**为了确保稳定性，严禁将点击和归位合并在一个 Step 中。请严格分两轮执行：**

**第一轮：执行与观测 (Phase 1)**
1.  **获取任务**：
    - 调用 `get_next_task()`。如果返回空，则跳转到 Step 4。
2.  **执行点击 (Atomic Execution)**：
    - **必须**在一个 Step 内提交以下动作序列（Batch Action）：
    - **模式**：`click_element_by_index(...)` (仅限首位) -> `wait(1)` -> ... -> `get_current_url()`。
    - **示例**：
      `click_element_by_index(15)` -> `wait(1)` -> `click_text("Link Generator")` -> `wait(2)` -> `get_current_url()`
    - **禁止**：本轮**不要**调用 `go_to_url` 或 `update_task_status`。
3.  **【停止】**：本轮结束，等待观察页面跳转结果。

**第二轮：记录与归位 (Phase 2)**
1.  **状态核销**：
    - 调用 `update_task_status(filename, task_id, "done", result_url="上一轮的URL")`。
    - **规则**：无论是否跳转，只要点了就算 Done。
2.  **归位**：
    - `go_to_url("https://www.linkhaitao.com/dashboard")` -> `wait(2)`。
3.  **循环**：
    - 回到 Phase 1。

### 4. 输出
当 `get_next_task()` 返回空时，任务结束。请输出 "All navigation tasks completed."。
