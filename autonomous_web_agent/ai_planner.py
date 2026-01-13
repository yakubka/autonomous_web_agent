import google.genai as genai
import json
import re
from typing import Dict, Any, List
from config import Config

class AIPlanner:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.model_name = Config.GEMINI_MODEL
        
        self.system_prompt = """Ты - автономный веб-агент, который управляет браузером.
Твоя задача - выполнять сложные многошаговые задачи в веб-браузере.

Ты должен:
1. Анализировать текущее состояние страницы
2. Определять следующие действия для выполнения задачи
3. Выбирать правильные элементы для взаимодействия
4. Адаптироваться к изменениям на странице
5. Сообщать о прогрессе и проблемах

Ты НЕ должен:
- Использовать предзаготовленные селекторы или пути
- Предполагать структуру сайта заранее
- Использовать хардкодированные подсказки

Формат ответа - всегда JSON:
{
    "thoughts": "Мои размышления о текущей ситуации и следующих шагах",
    "action": {
        "type": "navigate|click|type|press|scroll|wait|ask_user|complete",
        "details": {...}
    },
    "confidence": 0.8
}

Доступные действия:
1. navigate: {"url": "https://..."}
2. click: {"selector": "CSS селектор"} или {"x": 100, "y": 200}
3. type: {"selector": "input selector", "text": "текст для ввода"}
4. press: {"key": "Enter"}
5. scroll: {"direction": "up|down", "amount": 300}
6. wait: {"seconds": 2}
7. ask_user: {"question": "ваш вопрос пользователю"}
8. complete: {"result": "описание результата"}

Важно: всегда анализируй видимые элементы и выбирай действия на основе текущего контекста."""

    async def plan_next_action(self, 
                             task: str,
                             history: List[Dict],
                             page_state: Dict) -> Dict[str, Any]:
        
        context = self._create_context(task, history, page_state)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=context
            )
            
            if response.text:
                return self._parse_response(response.text)
            else:
                return self._create_fallback_action()
                
        except Exception as e:
            print(f"AI planning error: {e}")
            return self._create_fallback_action()
    
    def _create_context(self, task: str, history: List[Dict], page_state: Dict) -> str:
        
        recent_history = history[-5:] if len(history) > 5 else history
        
        context = f"""
{self.system_prompt}

ТЕКУЩАЯ ЗАДАЧА: {task}

ИСТОРИЯ ДЕЙСТВИЙ (последние {len(recent_history)}):
{self._format_history(recent_history)}

ТЕКУЩЕЕ СОСТОЯНИЕ СТРАНИЦЫ:
- URL: {page_state.get('url', 'Unknown')}
- Заголовок: {page_state.get('title', 'Unknown')}

ВИДИМЫЙ ТЕКСТ (первые 2000 символов):
{page_state.get('visible_text', '')[:2000]}

ИНТЕРАКТИВНЫЕ ЭЛЕМЕНТЫ (первые 20):
{self._format_elements(page_state.get('interactive_elements', [])[:20])}

СТРУКТУРА СТРАНИЦЫ:
{self._format_structure(page_state.get('page_structure', '[]'))}

Что следует сделать дальше для выполнения задачи? Верни JSON с действием.
"""
        return context
    
    def _format_history(self, history: List[Dict]) -> str:
        if not history:
            return "Нет истории действий"
        
        formatted = []
        for i, action in enumerate(history, 1):
            formatted.append(f"{i}. {action.get('type', 'unknown')}: {action.get('details', {})}")
        return "\n".join(formatted)
    
    def _format_elements(self, elements: List[Dict]) -> str:
        if not elements:
            return "Нет интерактивных элементов"
        
        formatted = []
        for i, el in enumerate(elements, 1):
            element_info = f"{i}. {el.get('tag', '')}"
            
            if el.get('text'):
                element_info += f" текст: '{el.get('text')}'"
            if el.get('placeholder'):
                element_info += f" placeholder: '{el.get('placeholder')}'"
            if el.get('type'):
                element_info += f" type: {el.get('type')}"
            if el.get('role'):
                element_info += f" роль: {el.get('role')}"
            
            formatted.append(element_info)
        
        return "\n".join(formatted)
    
    def _format_structure(self, structure_json: str) -> str:
        try:
            structure = json.loads(structure_json)
            formatted = []
            for item in structure:
                formatted.append(f"{item.get('tag', '')}: {item.get('text', '')}")
            return "\n".join(formatted)
        except:
            return "Не удалось проанализировать структуру"
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                if 'action' not in result:
                    result = self._create_fallback_action()
                
                return result
            else:
                return self._create_fallback_action()
                
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return self._create_fallback_action()
    
    def _create_fallback_action(self) -> Dict[str, Any]:
        return {
            "thoughts": "Не удалось распознать ответ AI, выполняю безопасное действие",
            "action": {
                "type": "wait",
                "details": {"seconds": 2}
            },
            "confidence": 0.1
        }