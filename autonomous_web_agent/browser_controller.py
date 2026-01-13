from playwright.async_api import async_playwright, Page
import json
from typing import Dict, List, Any
import asyncio

class BrowserController:
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        
    async def start(self):
        """Запуск браузера"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--start-maximized']
        )
        self.page = await self.browser.new_page()
        
        # Настройка окна браузера
        await self.page.set_viewport_size({'width': 1920, 'height': 1080})
        
        return self.page
    
    async def close(self):
        """Закрытие браузера"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def get_page_state(self) -> Dict[str, Any]:
        """Получение текущего состояния страницы"""
        if not self.page:
            return {}
        
        try:
            # Получаем основную информацию о странице
            state = {
                'url': self.page.url,
                'title': await self.page.title(),
                'screenshot': await self._get_minimal_screenshot(),
                'visible_text': await self._get_visible_text(),
                'interactive_elements': await self._get_interactive_elements(),
                'page_structure': await self._get_page_structure(),
            }
            return state
        except Exception as e:
            print(f"Error getting page state: {e}")
            return {}
    
    async def _get_visible_text(self) -> str:
        """Извлечение видимого текста со страницы"""
        try:
            # Получаем все видимые текстовые элементы
            text = await self.page.evaluate("""
                () => {
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    let texts = [];
                    let node;
                    while (node = walker.nextNode()) {
                        if (node.parentElement && 
                            node.parentElement.offsetParent !== null && 
                            node.textContent.trim().length > 0) {
                            texts.push(node.textContent.trim());
                        }
                    }
                    return texts.join('\\n');
                }
            """)
            return text[:5000]  # Ограничиваем размер
        except:
            return ""
    
    async def _get_interactive_elements(self) -> List[Dict]:
        """Получение интерактивных элементов"""
        try:
            elements = await self.page.evaluate("""
                () => {
                    const selectors = [
                        'a', 'button', 'input', 'textarea', 'select',
                        '[role="button"]', '[role="link"]', '[role="textbox"]',
                        '[onclick]', '[href]', '[type="submit"]', '[type="button"]'
                    ];
                    
                    const allElements = [];
                    selectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => {
                            if (el.offsetParent !== null &&  // Видимый элемент
                                (el.offsetWidth > 0 || el.offsetHeight > 0)) {
                                
                                const rect = el.getBoundingClientRect();
                                const centerX = Math.floor(rect.left + rect.width / 2);
                                const centerY = Math.floor(rect.top + rect.height / 2);
                                
                                allElements.push({
                                    tag: el.tagName.toLowerCase(),
                                    text: el.textContent?.trim().substring(0, 100) || '',
                                    placeholder: el.placeholder || '',
                                    type: el.type || '',
                                    href: el.href || '',
                                    id: el.id || '',
                                    class: el.className || '',
                                    role: el.getAttribute('role') || '',
                                    xpath: getXPath(el),
                                    center_x: centerX,
                                    center_y: centerY,
                                    visible: true
                                });
                            }
                        });
                    });
                    
                    // Вспомогательная функция для получения XPath
                    function getXPath(element) {
                        if (element.id !== '')
                            return '//*[@id="' + element.id + '"]';
                        if (element === document.body)
                            return '/html/body';
                        
                        var ix = 0;
                        var siblings = element.parentNode.childNodes;
                        
                        for (var i = 0; i < siblings.length; i++) {
                            var sibling = siblings[i];
                            if (sibling === element)
                                return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                            if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                                ix++;
                        }
                    }
                    
                    return allElements;
                }
            """)
            return elements
        except Exception as e:
            print(f"Error getting interactive elements: {e}")
            return []
    
    async def _get_page_structure(self) -> str:
        """Получение структуры страницы (заголовки, секции)"""
        try:
            structure = await self.page.evaluate("""
                () => {
                    const elements = [];
                    const tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'nav', 'header', 'footer', 'main', 'section', 'article'];
                    
                    tags.forEach(tag => {
                        document.querySelectorAll(tag).forEach(el => {
                            if (el.offsetParent !== null) {
                                elements.push({
                                    tag: tag,
                                    text: el.textContent?.trim().substring(0, 200) || '',
                                    id: el.id || ''
                                });
                            }
                        });
                    });
                    
                    return JSON.stringify(elements);
                }
            """)
            return structure
        except:
            return "[]"
    
    async def _get_minimal_screenshot(self) -> str:
        """Получение миниатюры скриншота (base64)"""
        try:
            screenshot = await self.page.screenshot(
                encoding="base64",
                type="jpeg",
                quality=30,  # Низкое качество для экономии токенов
                clip={"x": 0, "y": 0, "width": 800, "height": 600}
            )
            return f"data:image/jpeg;base64,{screenshot}"
        except:
            return ""
    
    async def execute_action(self, action: Dict) -> Dict:
        """Выполнение действия в браузере"""
        action_type = action.get('type')
        details = action.get('details', {})
        
        try:
            if action_type == 'navigate':
                url = details.get('url')
                if url:
                    await self.page.goto(url, wait_until='networkidle')
                    await asyncio.sleep(2)
                    return {'success': True, 'result': f'Navigated to {url}'}
            
            elif action_type == 'click':
                selector = details.get('selector')
                if selector:
                    await self.page.click(selector)
                    await asyncio.sleep(1)
                    return {'success': True, 'result': f'Clicked {selector}'}
                
                # Клик по координатам
                x = details.get('x')
                y = details.get('y')
                if x is not None and y is not None:
                    await self.page.mouse.click(x, y)
                    await asyncio.sleep(1)
                    return {'success': True, 'result': f'Clicked at ({x}, {y})'}
            
            elif action_type == 'type':
                selector = details.get('selector')
                text = details.get('text')
                if selector and text:
                    await self.page.fill(selector, text)
                    await asyncio.sleep(0.5)
                    return {'success': True, 'result': f'Typed "{text}" into {selector}'}
            
            elif action_type == 'press':
                key = details.get('key')
                if key:
                    await self.page.keyboard.press(key)
                    await asyncio.sleep(0.5)
                    return {'success': True, 'result': f'Pressed {key}'}
            
            elif action_type == 'scroll':
                direction = details.get('direction', 'down')
                amount = details.get('amount', 300)
                
                if direction == 'down':
                    await self.page.evaluate(f"window.scrollBy(0, {amount})")
                else:
                    await self.page.evaluate(f"window.scrollBy(0, -{amount})")
                
                await asyncio.sleep(0.5)
                return {'success': True, 'result': f'Scrolled {direction}'}
            
            elif action_type == 'wait':
                seconds = details.get('seconds', 2)
                await asyncio.sleep(seconds)
                return {'success': True, 'result': f'Waited {seconds} seconds'}
            
            return {'success': False, 'error': 'Unknown action type'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}