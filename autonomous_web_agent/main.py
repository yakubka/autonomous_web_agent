#!/usr/bin/env python3
import asyncio
import sys
from agent import AutonomousWebAgent
from config import Config
import argparse

async def main():
    parser = argparse.ArgumentParser(description='Автономный веб-агент')
    parser.add_argument('--task', type=str, help='Задача для выполнения')
    parser.add_argument('--url', type=str, help='Начальный URL')
    parser.add_argument('--headless', action='store_true', help='Запуск в headless режиме')
    parser.add_argument('--demo', action='store_true', help='Запуск демо-задачи')
    
    args = parser.parse_args()
    
    # Проверка API ключа
    if not Config.GEMINI_API_KEY:
        print("❌ Ошибка: GEMINI_API_KEY не найден в .env файле")
        print("ℹ️ Получите ключ на: https://makersuite.google.com/app/apikey")
        sys.exit(1)
    
    # Создаем агента
    agent = AutonomousWebAgent(headless=args.headless)
    
    try:
        # Инициализируем агента
        await agent.initialize()
        
        # Если указан URL - переходим
        if args.url:
            await agent.browser.page.goto(args.url)
            print(f"🌐 Перешли на {args.url}")
        
        # Если указана задача - выполняем
        if args.task:
            result = await agent.run_task(args.task)
            
            # Сохраняем историю
            import json
            with open('task_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("📁 Результат сохранен в task_result.json")
        
        # Демо режим
        elif args.demo:
            demo_tasks = [
                "Найди рецепт пасты на сайте kulinar.ru",
                "Найди последние новости про ИИ на habr.com",
                "Найди курсы по Python на Coursera",
            ]
            
            print("🎬 Демо режим:")
            for i, task in enumerate(demo_tasks, 1):
                print(f"\n{i}. {task}")
                await agent.run_task(task)
                input("Нажмите Enter для следующей задачи...")
        
        # Интерактивный режим
        else:
            await agent.interactive_mode()
    
    except KeyboardInterrupt:
        print("\n⏹️ Прервано пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main())