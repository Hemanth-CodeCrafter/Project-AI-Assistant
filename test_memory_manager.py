from core.memory_manager import memory_manager
from core.memory_db import memory_db

memory_manager.remember(
    "My name is Hemanth"
)

memory_manager.remember(
    "I like Python"
)

memory_manager.remember(
    "I had tea today"
)

print(memory_db.get_all())