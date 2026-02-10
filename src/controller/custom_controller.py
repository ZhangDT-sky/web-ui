import pdb

import pyperclip
from typing import Optional, Type, Callable, Dict, Any, Union, Awaitable, TypeVar
from pydantic import BaseModel
from browser_use.agent.views import ActionResult
from browser_use.browser.context import BrowserContext
from browser_use.controller.service import Controller, DoneAction
from browser_use.controller.registry.service import Registry, RegisteredAction
from main_content_extractor import MainContentExtractor
from browser_use.controller.views import (
    ClickElementAction,
    DoneAction,
    ExtractPageContentAction,
    GoToUrlAction,
    InputTextAction,
    OpenTabAction,
    ScrollAction,
    SearchGoogleAction,
    SendKeysAction,
    SwitchTabAction,
)
import logging
import inspect
import asyncio
import os
from langchain_core.language_models.chat_models import BaseChatModel
from browser_use.agent.views import ActionModel, ActionResult

from src.utils.mcp_client import create_tool_param_model, setup_mcp_client_and_tools

from browser_use.utils import time_execution_sync

logger = logging.getLogger(__name__)

Context = TypeVar('Context')


class CustomController(Controller):
    def __init__(self, exclude_actions: list[str] = [],
                 output_model: Optional[Type[BaseModel]] = None,
                 ask_assistant_callback: Optional[Union[Callable[[str, BrowserContext], Dict[str, Any]], Callable[
                     [str, BrowserContext], Awaitable[Dict[str, Any]]]]] = None,
                 ):
        super().__init__(exclude_actions=exclude_actions, output_model=output_model)
        self._register_custom_actions()
        self.ask_assistant_callback = ask_assistant_callback
        self.mcp_client = None
        self.mcp_server_config = None

    def _register_custom_actions(self):
        """Register all custom browser actions"""

        @self.registry.action(
            "When executing tasks, prioritize autonomous completion. However, if you encounter a definitive blocker "
            "that prevents you from proceeding independently – such as needing credentials you don't possess, "
            "requiring subjective human judgment, needing a physical action performed, encountering complex CAPTCHAs, "
            "or facing limitations in your capabilities – you must request human assistance."
        )
        async def ask_for_assistant(query: str, browser: BrowserContext):
            if self.ask_assistant_callback:
                if inspect.iscoroutinefunction(self.ask_assistant_callback):
                    user_response = await self.ask_assistant_callback(query, browser)
                else:
                    user_response = self.ask_assistant_callback(query, browser)
                msg = f"AI ask: {query}. User response: {user_response['response']}"
                logger.info(msg)
                return ActionResult(extracted_content=msg, include_in_memory=True)
            else:
                return ActionResult(extracted_content="Human cannot help you. Please try another way.",
                                    include_in_memory=True)

        @self.registry.action(
            'Upload file to interactive element with file path ',
        )
        async def upload_file(index: int, path: str, browser: BrowserContext, available_file_paths: list[str]):
            if path not in available_file_paths:
                return ActionResult(error=f'File path {path} is not available')

            if not os.path.exists(path):
                return ActionResult(error=f'File {path} does not exist')

            dom_el = await browser.get_dom_element_by_index(index)

            file_upload_dom_el = dom_el.get_file_upload_element()

            if file_upload_dom_el is None:
                msg = f'No file upload element found at index {index}'
                logger.info(msg)
                return ActionResult(error=msg)

            file_upload_el = await browser.get_locate_element(file_upload_dom_el)

            if file_upload_el is None:
                msg = f'No file upload element found at index {index}'
                logger.info(msg)
                return ActionResult(error=msg)

            try:
                await file_upload_el.set_input_files(path)
                msg = f'Successfully uploaded file to index {index}'
                logger.info(msg)
                return ActionResult(extracted_content=msg, include_in_memory=True)
            except Exception as e:
                msg = f'Failed to upload file to index {index}: {str(e)}'
                logger.info(msg)
                return ActionResult(error=msg)

        """
        按文本名点击页面元素
        """
        @self.registry.action(
            'Click element by exact text content. Use this to click buttons or links when you know their text, e.g. "Submit", "Log In", "Dashboard".',
        )
        async def click_text(text: str, browser: BrowserContext):
            page = await browser.get_current_page()
            logger.info(f"🖱️ Attempting to click text: '{text}'")  # Start log
            try:
                # 1. Exact text match (visible only)
                loc = page.get_by_text(text, exact=True)
                if await loc.count() > 0 and await loc.first.is_visible():
                    await loc.first.click()
                    logger.info(f"✅ Clicked element with text: '{text}'")
                    return ActionResult(extracted_content=f"Clicked element with text: '{text}'")
                
                # 2. Case insensitive / Partial match fallback
                loc = page.locator(f"text=/{text}/i")
                if await loc.count() > 0 and await loc.first.is_visible():
                    await loc.first.click()
                    logger.info(f"✅ Clicked element with text (fuzzy): '{text}'")
                    return ActionResult(extracted_content=f"Clicked element with text (fuzzy): '{text}'")
                
                logger.warning(f"❌ Could not find visible element with text '{text}'") # Upgraded from DEBUG
                return ActionResult(error=f"Could not find visible element with text '{text}'")
            except Exception as e:

                logger.warning(f"Failed to click text '{text}': {str(e)}")
                return ActionResult(error=f"Failed to click text '{text}': {str(e)}")

        """
        处理悬停方式菜单栏
        """
        @self.registry.action(
            'Hover over element by exact text content.',
        )
        async def hover_text(text: str, browser: BrowserContext):
            page = await browser.get_current_page()
            logger.info(f"Attempting to hover text: '{text}'")
            try:
                loc = page.get_by_text(text, exact=True)
                if await loc.count() > 0 and await loc.first.is_visible():
                    await loc.first.hover()
                    logger.info(f"✅ Hovered over element with text: '{text}'")
                    return ActionResult(extracted_content=f"Hovered over element with text: '{text}'")
                
                loc = page.locator(f"text=/{text}/i")
                if await loc.count() > 0 and await loc.first.is_visible():
                    await loc.first.hover()
                    logger.info(f"✅ Hovered over element with text (fuzzy): '{text}'")
                    return ActionResult(extracted_content=f"Hovered over element with text (fuzzy): '{text}'")
                
                logger.warning(f"❌ Could not find visible element with text '{text}'")
                return ActionResult(error=f"Could not find visible element with text '{text}'")
            except Exception as e:
                logger.warning(f"Failed to hover text '{text}': {str(e)}")
                return ActionResult(error=f"❌ Failed to hover text '{text}': {str(e)}")

        """
        获取当前页面URL
        """
        @self.registry.action(
            'Get the current page URL. Use this to extract the URL after navigation.',
        )
        async def get_current_url(browser: BrowserContext):
            try:
                page = await browser.get_current_page()
                url = page.url
                logger.info(f"🔗 Extracted URL: {url}")
                return ActionResult(extracted_content=f"Current URL: {url}")
            except Exception as e:
                logger.warning(f"Failed to get current URL: {str(e)}")
                return ActionResult(error=f"Failed to get current URL: {str(e)}")


        """
        保存为导航树
        """
        @self.registry.action(
            'Save the navigation structure to a specific JSON file. Use this after extracting the structure in Step 2. '
            'Returns the filename used (e.g., nav_task_20231027_120000.json). '
            'You MUST remember this filename for subsequent steps.'
        )
        async def save_navigation_structure(structure: str, browser: BrowserContext):
            try:
                import json
                import time
                import ast
                
                # Generate unique filename based on time
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"nav_task_{timestamp}.json"
                nav_dir = os.path.join(os.getcwd(), "nav_task")
                os.makedirs(nav_dir, exist_ok=True)
                filepath = os.path.join(nav_dir, filename)
                
                # Helper to flatten the tree
                flat_tasks = []
                def extract_nodes(nodes, parent_path=[]):
                    for node in nodes:
                        # Handle string nodes (leaf items in a list, e.g., from 'group' arrays)
                        if isinstance(node, str):
                            flat_tasks.append({
                                "id": f"task_{len(flat_tasks)}",
                                "name": node,
                                "path": parent_path + [node],
                                "url": "",
                                "status": "pending"
                            })
                            continue
                        
                        # Handle dict nodes
                        # Support multiple keys for name/label (including Agent's extract_content variations)
                        node_name = (node.get('name') or node.get('label') or node.get('text') or 
                                    node.get('menu_item') or node.get('submenu_item') or 'Unknown')
                        current_path = parent_path + [node_name]
                        # Support multiple keys for children (including Agent's extract_content variations)
                        children = (node.get('children') or node.get('submenus') or node.get('submenu') or 
                                   node.get('items') or node.get('sub_items') or node.get('submenu_items') or 
                                   node.get('group') or node.get('sub_submenu') or [])
                        
                        if not children:
                            flat_tasks.append({
                                "id": f"task_{len(flat_tasks)}",
                                "name": node_name,
                                "path": current_path,
                                "url": node.get('url', ''),
                                "status": "pending"  # pending, done, failed
                            })
                        else:
                            extract_nodes(children, current_path)

                # Parse input structure
                if isinstance(structure, str):
                     try:
                         safe_data = json.loads(structure)
                     except:
                         try:
                            safe_data = ast.literal_eval(structure)
                         except:
                            return ActionResult(error="Invalid JSON structure provided")
                else:
                    safe_data = structure

                # Handle Dict input (unwrap recursively to find the list)
                root_nodes = safe_data
                if isinstance(safe_data, dict):
                    def find_list(d):
                        for key, value in d.items():
                            if isinstance(value, list):
                                return value
                            if isinstance(value, dict):
                                result = find_list(value)
                                if result:
                                    return result
                        return None

                    found_list = find_list(safe_data)
                    if found_list:
                        root_nodes = found_list
                    else:
                        return ActionResult(error="Invalid structure: Could not find a list of navigation items in the provided dictionary.")

                if not isinstance(root_nodes, list):
                     return ActionResult(error=f"Invalid structure: Expected a list of items, got {type(root_nodes).__name__}")

                extract_nodes(root_nodes)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({"session_id": timestamp, "tasks": flat_tasks}, f, ensure_ascii=False, indent=2)
                    
                logger.info(f"💾 Navigation structure saved to {filename}")
                return ActionResult(extracted_content=f"Structure saved to {filename}. Total tasks: {len(flat_tasks)}")
            except Exception as e:
                return ActionResult(error=f"Failed to save structure: {str(e)}")

        """
        获取下一个执行任务
        """
        @self.registry.action(
            'Get the next pending task from the saved navigation file. Requires the filename.',
        )
        async def get_next_task(filename: str, browser: BrowserContext):
            try:
                import json
                nav_dir = os.path.join(os.getcwd(), "nav_task")
                filepath = os.path.join(nav_dir, filename)

                # Fallback to project root for backward compatibility
                if not os.path.exists(filepath):
                    filepath = os.path.join(os.getcwd(), filename)
                    if not os.path.exists(filepath):
                        return ActionResult(error=f"File {filename} not found in nav_task/ or root directory.")

                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                tasks = data.get("tasks", [])
                # Find the first pending task
                next_task = next((t for t in tasks if t["status"] == "pending"), None)

                if next_task:
                    return ActionResult(extracted_content=json.dumps(next_task))
                else:
                    return ActionResult(extracted_content="ALL_TASKS_COMPLETED")

            except Exception as e:
                return ActionResult(error=f"Failed to read next task: {str(e)}")

        """
        更新菜单项状态
        """
        @self.registry.action(
            'Mark a task as completed (or failed) in the saved file. Optionally record the extracted URL.',
        )
        async def update_task_status(filename: str, task_id: str, status: str, browser: BrowserContext, result_url: str = ""):
            try:
                import json
                nav_dir = os.path.join(os.getcwd(), "nav_task")
                filepath = os.path.join(nav_dir, filename)

                # Fallback to project root for backward compatibility
                if not os.path.exists(filepath):
                    filepath = os.path.join(os.getcwd(), filename)
                    if not os.path.exists(filepath):
                        return ActionResult(error=f"File {filename} not found in nav_task/ or root directory.")

                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                updated = False
                for t in data["tasks"]:
                    if t["id"] == task_id:
                        t["status"] = status
                        if result_url:
                            t["url"] = result_url  # Update or set the URL
                        updated = True
                        break

                if updated:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    return ActionResult(extracted_content=f"Task {task_id} marked as {status}. URL updated: {bool(result_url)}")
                else:
                    return ActionResult(error=f"Task {task_id} not found")
            except Exception as e:
                return ActionResult(error=f"Failed to update task: {str(e)}")


    """
    分析功能 - 提取
    """

    @time_execution_sync('--act')
    async def act(
            self,
            action: ActionModel,
            browser_context: Optional[BrowserContext] = None,
            #
            page_extraction_llm: Optional[BaseChatModel] = None,
            sensitive_data: Optional[Dict[str, str]] = None,
            available_file_paths: Optional[list[str]] = None,
            #
            context: Context | None = None,
    ) -> ActionResult:
        """Execute an action"""

        try:
            for action_name, params in action.model_dump(exclude_unset=True).items():
                if params is not None:
                    if action_name.startswith("mcp"):
                        # this is a mcp tool
                        logger.debug(f"Invoke MCP tool: {action_name}")
                        mcp_tool = self.registry.registry.actions.get(action_name).function
                        result = await mcp_tool.ainvoke(params)
                    else:
                        result = await self.registry.execute_action(
                            action_name,
                            params,
                            browser=browser_context,
                            page_extraction_llm=page_extraction_llm,
                            sensitive_data=sensitive_data,
                            available_file_paths=available_file_paths,
                            context=context,
                        )

                    if isinstance(result, str):
                        return ActionResult(extracted_content=result)
                    elif isinstance(result, ActionResult):
                        return result
                    elif result is None:
                        return ActionResult()
                    else:
                        raise ValueError(f'Invalid action result type: {type(result)} of {result}')
            return ActionResult()
        except Exception as e:
            raise e

    async def setup_mcp_client(self, mcp_server_config: Optional[Dict[str, Any]] = None):
        self.mcp_server_config = mcp_server_config
        if self.mcp_server_config:
            self.mcp_client = await setup_mcp_client_and_tools(self.mcp_server_config)
            self.register_mcp_tools()

    def register_mcp_tools(self):
        """
        Register the MCP tools used by this controller.
        """
        if self.mcp_client:
            for server_name in self.mcp_client.server_name_to_tools:
                for tool in self.mcp_client.server_name_to_tools[server_name]:
                    tool_name = f"mcp.{server_name}.{tool.name}"
                    self.registry.registry.actions[tool_name] = RegisteredAction(
                        name=tool_name,
                        description=tool.description,
                        function=tool,
                        param_model=create_tool_param_model(tool),
                    )
                    logger.info(f"Add mcp tool: {tool_name}")
                logger.debug(
                    f"Registered {len(self.mcp_client.server_name_to_tools[server_name])} mcp tools for {server_name}")
        else:
            logger.warning(f"MCP client not started.")

    async def close_mcp_client(self):
        if self.mcp_client:
            await self.mcp_client.__aexit__(None, None, None)
