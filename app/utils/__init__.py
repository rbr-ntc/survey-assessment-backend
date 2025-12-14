# Utils package

CATEGORIES = {
    "documentation": {"name": "Документирование", "icon": "📝", "weight": 1},
    "modeling": {"name": "Моделирование процессов", "icon": "📊", "weight": 1.2},
    "api": {"name": "API Design", "icon": "🔌", "weight": 1.1},
    "database": {"name": "Базы данных", "icon": "🗄️", "weight": 1.1},
    "messaging": {"name": "Асинхронные взаимодействия", "icon": "📨", "weight": 1},
    "system_design": {"name": "Проектирование систем", "icon": "🏗️", "weight": 1.3},
    "security": {"name": "Безопасность", "icon": "🔒", "weight": 1},
    "analytical": {"name": "Аналитическое мышление", "icon": "🧠", "weight": 1.2},
    "communication": {"name": "Коммуникации", "icon": "💬", "weight": 1},
}

LEVELS = [
    {"level": "Senior", "description": "Экспертный уровень системного аналитика", "nextLevel": "Lead/Architect", "minYears": "5+", "nextLevelScore": 100, "minScore": 85},
    {"level": "Middle+", "description": "Уверенный Middle с потенциалом роста", "nextLevel": "Senior", "minYears": "3-5", "nextLevelScore": 85, "minScore": 70},
    {"level": "Middle", "description": "Самостоятельный системный аналитик", "nextLevel": "Middle+", "minYears": "2-3", "nextLevelScore": 70, "minScore": 55},
    {"level": "Junior+", "description": "Развивающийся Junior", "nextLevel": "Middle", "minYears": "1-2", "nextLevelScore": 55, "minScore": 40},
    {"level": "Junior", "description": "Начинающий системный аналитик", "nextLevel": "Junior+", "minYears": "0-1", "nextLevelScore": 40, "minScore": 0},
]

def get_level(score):
    """Определяет уровень на основе балла"""
    for lvl in LEVELS:
        if score >= lvl["minScore"]:
            return lvl
    return LEVELS[-1]

__all__ = ['CATEGORIES', 'get_level']
