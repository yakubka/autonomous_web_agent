import asyncio
from typing import Dict, Any, List
from browser_controller import BrowserController
from ai_planner import AIPlanner
from memory import Memory
from config import Config
import json

class AutonomousWebAgent:
    def __init__(self, headless=False):
        self.browser = BrowserController(headless=headless)
        self.planner = AIPlanner()
        self.memory = Memory()
        self.running = False
        self.current_task = ""
        
    async def initialize(self):
        print("Инициализация агента...")
        await self.browser.start()
        print("Браузер запущен")
        return True
    
    async def run_task(self, task: str) -> Dict[str, Any]:
        print(f"\nНачинаю выполнение задачи: {task}")
        print("=" * 50)
        
        self.running = True
        self.current_task = task
        self.memory.set_task(task)
        
        steps = 0
        max_steps = Config.MAX_STEPS
        
        try:
            while self.running and steps < max_steps:
                steps += 1
                print(f"\nШаг {steps}/{max_steps}")
                
                print("Анализирую страницу...")
                page_state = await self.browser.get_page_state()
                self.memory.add_observation(page_state)
                
                print("Планирую следующее действие...")
                plan = await self.planner.plan_next_action(
                    task=self.current_task,
                    history=[h['action'] for h in self.memory.get_recent_history(5)],
                    page_state=page_state
                )
                
                if 'thoughts' in plan:
                    print(f"AI: {plan['thoughts']}")
                
                action = plan.get('action', {})
                action_type = action.get('type', '')
                confidence = plan.get('confidence', 0.5)
                
                print(f"Действие: {action_type} (уверенность: {confidence:.2f})")
                
                if action_type == 'complete':
                    result = action.get('details', {}).get('result', 'Задача выполнена')
                    print(f"\nЗАДАЧА ВЫПОЛНЕНА: {result}")
                    self.running = False
                    return {
                        'success': True,
                        'result': result,
                        'steps': steps,
                        'history': self.memory.history
                    }
                
                elif action_type == 'ask_user':
                    question = action.get('details', {}).get('question', '')
                    print(f"\nВОПРОС К ПОЛЬЗОВАТЕЛЮ: {question}")
                    print("Для демо продолжаю выполнение...")
                    action = {'type': 'wait', 'details': {'seconds': 1}}
                
                if action_type not in ['complete', 'ask_user']:
                    result = await self.browser.execute_action(action)
                    self.memory.add_action(action, result)
                    
                    if result.get('success'):
                        print(f"Успешно: {result.get('result', '')}")
                    else:
                        print(f"Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                
                await asyncio.sleep(Config.THINKING_DELAY)
            
            if steps >= max_steps:
                print(f"\nДостигнут лимит шагов ({max_steps})")
                return {
                    'success': False,
                    'error': f'Достигнут лимит шагов ({max_steps})',
                    'steps': steps,
                    'history': self.memory.history
                }
                
        except Exception as e:
            print(f"\nКритическая ошибка: {e}")
            return {
                'success': False,
                'error': str(e),
                'steps': steps,
                'history': self.memory.history
            }
    
    async def interactive_mode(self):
        print("\n" + "="*50)
        print("АВТОНОМНЫЙ WEB-АГЕНТ")
        print("="*50)
        print("Команды:")
        print("  /task [задача] - Выполнить задачу")
        print("  /url [url] - Перейти по URL")
        print("  /stop - Остановить агента")
        print("  /status - Статус")
        print("  /exit - Выход")
        print("="*50)
        
        while True:
            try:
                user_input = input("\nВведите команду или задачу: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == '/exit':
                    print("Выход...")
                    break
                
                elif user_input.lower() == '/status':
                    print(f"{self.memory.get_summary()}")
                
                elif user_input.lower() == '/stop':
                    self.running = False
                    print("Агент остановлен")
                
                elif user_input.lower().startswith('/url '):
                    url = user_input[5:].strip()
                    if url:
                        await self.browser.page.goto(url)
                        print(f"Переход на {url}")
                
                elif user_input.lower().startswith('/task '):
                    task = user_input[6:].strip()
                    if task:
                        await self.run_task(task)
                
                else:
                    await self.run_task(user_input)
                    
            except KeyboardInterrupt:
                print("\nПрервано пользователем")
                break
            except Exception as e:
                print(f"Ошибка: {e}")
    
    async def close(self):
        await self.browser.close()
        print("Агент завершил работу")