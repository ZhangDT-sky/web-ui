# Linkbux 导航提取任务 

**目标**：登录并提取导航栏的所有菜单项及 URL。

## ⚠️ 关键操作 (必须遵守)

1. **Dashboard**：登录后的页面即为 Dashboard，**不要点击 Dashboard**，直接从第二个菜单开始。
2. **悬停触发**：所有菜单必须用 `hover_text("名称")` 触发。
3. **强制等待**：
   - `hover_text` 后：`wait(1)`
   - `click_text` 后：`wait(2)`
   - `go_back` 后：**必须 wait(2)** (等待页面完全加载)

---

## 🚀 执行步骤

### 1. 登录
- URL: `https://www.linkbux.com/login`
- 用户: `hucen` / 密码: `qwer@1234`
- 登录后检查 URL 是否包含 `/publisher`

### 2. 获取导航栏结构 (静态分析)
1. **仔细观察**侧边栏菜单，提取一级菜单、二级菜单和三级菜单的层级结构。
2. **记录**下完整的导航树结构，并将其保存在记忆中（不要输出）。
3. **格式示例** (仅用于理解):
   ```json
   [
     {"name": "Reports", "path": ["Reports"], "children": [
       {"name": "Performance", "path": ["Reports", "Performance"]}, 
       {"name": "Conversion Report", "path": ["Reports", "Conversion Report"]}
     ]},
     {"name": "Tools", "path": ["Tools"], "children": [
       {"name": "API", "path": ["Tools", "API"]}, 
       {"name": "Postback", "path": ["Tools", "Postback"]}
     ]}
   ]
   ```

### 3. 导航点击遍历 (基于结构)
**根据步骤 2 获取的结构，依次点击每个末级菜单（Leaf Node）。**

**核心策略：**
- **原子化执行 (Batch Actions)**：对于每一个目标菜单，**必须**将其所有的 hover/wait/click/get_url 动作一次性生成在同一个 Step 中。**严禁**分拆成多次对话，否则菜单会消失。
- **必须**按照刚才记录的列表顺序执行，不要遗漏。
- **优先使用 `click_text("名称")`**。

**对于每个目标菜单项 (必须在一个 Step 内完成)：**
1. **三级菜单**：`hover_text("一级")` -> `wait(1)` -> `hover_text("二级")` -> `wait(1)` -> `click_text("三级")` -> `wait(2)` -> `get_current_url()` -> `go_back()` -> `wait(2)`
2. **二级菜单**：`hover_text("一级")` -> `wait(1)` -> `click_text("二级")` -> `wait(2)` -> `get_current_url()` -> `go_back()` -> `wait(2)`
3. **一级菜单**：`click_text("一级")` -> `wait(2)` -> `get_current_url()` -> `go_back()` -> `wait(2)`

### 4. 输出
最后生成 JSON 格式的导航结构。
