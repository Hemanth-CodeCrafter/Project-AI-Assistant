from core.memory_db import memory_db

memory_db.save(
    "My name is Hemanth",
    "personal",
    10
)

print(memory_db.get_all())