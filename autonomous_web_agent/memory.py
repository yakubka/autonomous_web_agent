from typing import List, Dict, Any
from datetime import datetime

class Memory:
    def __init__(self, max_history=100):
        self.max_history = max_history
        self.history: List[Dict] = []
        self.observations: List[Dict] = []
        self.task = ""
        
    def add_action(self, action: Dict, result: Dict):
        """Добавление действия в историю"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'result': result,
            'success': result.get('success', False)
        }
        
        self.history.append(entry)
        
        # Ограничиваем размер истории
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def add_observation(self, observation: Dict):
        """Добавление наблюдения (состояния страницы)"""
        self.observations.append({
            'timestamp': datetime.now().isoformat(),
            'observation': observation
        })
        
        if len(self.observations) > 20:  # Храним последние 20 состояний
            self.observations = self.observations[-20:]
    
    def get_recent_history(self, count=10) -> List[Dict]:
        """Получение последних действий"""
        return self.history[-count:] if len(self.history) > count else self.history
    
    def get_last_successful_action(self) -> Dict:
        """Получение последнего успешного действия"""
        for action in reversed(self.history):
            if action.get('success'):
                return action
        return {}
    
    def set_task(self, task: str):
        """Установка текущей задачи"""
        self.task = task
    
    def get_task(self) -> str:
        """Получение текущей задачи"""
        return self.task
    
    def get_summary(self) -> str:
        """Получение краткой сводки о прогрессе"""
        if not self.history:
            return "Еще не выполнено действий"
        
        total = len(self.history)
        successful = sum(1 for h in self.history if h.get('success', False))
        
        return f"Выполнено действий: {total}, успешных: {successful}"