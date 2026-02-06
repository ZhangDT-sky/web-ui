import json
import logging
import os

from browser_use.browser.browser import Browser, IN_DOCKER
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from playwright.async_api import Browser as PlaywrightBrowser
from playwright.async_api import BrowserContext as PlaywrightBrowserContext
from typing import Optional
from browser_use.browser.context import BrowserContextState

logger = logging.getLogger(__name__)


class CustomBrowserContext(BrowserContext):
    def __init__(
            self,
            browser: 'Browser',
            config: BrowserContextConfig | None = None,
            state: Optional[BrowserContextState] = None,
    ):
        super(CustomBrowserContext, self).__init__(browser=browser, config=config, state=state)

    async def _create_context(self, browser: PlaywrightBrowser):
        context = await super()._create_context(browser)
        # Inject cursor visualization script
        await context.add_init_script(CURSOR_JS)
        return context


print("LOADING CUSTOM CONTEXT MODULE...")

CURSOR_JS = """
(function() {
    // Only run in top frame
    if (window !== window.top) return;

    console.log("Antigravity: Injecting Cursor Script...");

    const createCursor = () => {
        const cursor = document.createElement('div');
        cursor.style.position = 'fixed';
        cursor.style.zIndex = '2147483647'; // Max Z-Index
        cursor.style.pointerEvents = 'none';
        cursor.style.width = '20px';
        cursor.style.height = '20px';
        cursor.style.border = '2px solid rgba(0, 255, 0, 0.8)'; // GREEN
        cursor.style.borderRadius = '50%';
        cursor.style.backgroundColor = 'rgba(0, 255, 0, 0.2)';
        cursor.style.transform = 'translate(-50%, -50%)';
        cursor.style.transition = 'top 0.1s ease, left 0.1s ease'; // Smooth movement
        cursor.style.display = 'none';
        cursor.id = 'agent-cursor';
        
        const center = document.createElement('div');
        center.style.position = 'absolute';
        center.style.top = '50%';
        center.style.left = '50%';
        center.style.width = '4px';
        center.style.height = '4px';
        center.style.backgroundColor = '#00FF00'; // GREEN CENTER
        center.style.borderRadius = '50%';
        center.style.transform = 'translate(-50%, -50%)';
        cursor.appendChild(center);
        
        document.body.appendChild(cursor); // Append to BODY
        console.log("Antigravity: Cursor element created and appended.");

        let lastX = 0;
        let lastY = 0;

        document.addEventListener('mousemove', (e) => {
            lastX = e.clientX;
            lastY = e.clientY;
            cursor.style.display = 'block';
            cursor.style.left = e.clientX + 'px';
            cursor.style.top = e.clientY + 'px';
        }, {passive: true, capture: true});

        document.addEventListener('click', (e) => {
            console.log("Antigravity: Click detected at", e.clientX, e.clientY);
            const ripple = document.createElement('div');
            ripple.style.position = 'fixed';
            ripple.style.zIndex = '2147483646';
            ripple.style.pointerEvents = 'none';
            ripple.style.width = '20px';
            ripple.style.height = '20px';
            ripple.style.borderRadius = '50%';
            ripple.style.backgroundColor = 'rgba(0, 255, 0, 0.5)'; // GREEN RIPPLE
            ripple.style.left = e.clientX + 'px';
            ripple.style.top = e.clientY + 'px';
            ripple.style.transform = 'translate(-50%, -50%)';
            document.body.appendChild(ripple);

            const animation = ripple.animate([
                { transform: 'translate(-50%, -50%) scale(1)', opacity: 0.5 },
                { transform: 'translate(-50%, -50%) scale(4)', opacity: 0 }
            ], {
                duration: 500,
                easing: 'ease-out'
            });

            animation.onfinish = () => ripple.remove();
        }, {passive: true, capture: true});
    };

    if (document.body) {
        createCursor();
    } else {
        document.addEventListener('DOMContentLoaded', createCursor);
    }
})();
"""
