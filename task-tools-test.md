# LinkHaiTao Tools 菜单专项测试

**目标**：针对 "Tools" 菜单进行专项点击测试，彻底解决菜单未展开及假阳性成功的问题。

## ⚠️ 关键规则
1. **输入文件**：使用 `tools_test_tasks.json`。
2. **严禁**使用 `click_element_by_index`。
3. **必须**执行 "两阶段 (Two-Phase)" 策略。
4. **必须**执行 "URL 变化校验"。

---

## 🚀 执行步骤

### 1. 准备阶段
- 假设 Agent 已登录。
- 直接开始循环。

### 2. 持久化遍历循环 (Two-Phase Execution)

**第一轮：执行与验证 (Phase 1)**
1. **获取任务**：`get_next_task("tools_test_tasks.json")`。
2. **执行点击**：
   - **Step A (展开父菜单)**：如果 Path 中包含父菜单 (如 "Tools")：
     - check: 父菜单是否已展开？
     - action: 
       - 如果未展开，点击 `click_text("Tools")`。
       - **陷阱预警**：页面顶部（面包屑）也有 "Tools"。**必须确认**点击的是侧边栏。如果点击后子菜单未出现，说明点错了（点了面包屑），请尝试点击 **"Tools" (Index 1)** 或旁边的 **箭头图标**。
   - **Step B (点击子菜单)**：点击目标项 (如 "Link Generator")。
3. **验证结果**：调用 `get_current_url()`。
   - **严格校验**：对比点击前后的 URL。如果 **URL 完全没变**，且页面内容无刷新，视为 **FAILURE (失败)**。
     - 此时应停止当前 Phase，标记任务失败或重试，**不要**假装成功。
4. **【停止】**：不要在第一轮调用 `update_task_status`。

**第二轮：记录与重置 (Phase 2)**
1. **状态更新**：调用 `update_task_status("tools_test_tasks.json", task_id, "done" 或 "failed", result_url)`。
2. **绝对归位**：调用 `go_to_url("https://www.linkhaitao.com/dashboard")` -> `wait(3)`。
   - **不要使用 go_back()**。必须强制回到 Dashboard，确保下一次从干净的状态开始。

**循环直至完成。**

### 3. 结束
- 输出测试结果 summary。
