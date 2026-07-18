from core.memory_manager import MemoryManager
from core.memory_db import MemoryDB

# Instantiate the dependencies
db = MemoryDB()
memory_manager_instance = MemoryManager(db=db)

# Use the instance to test the remember method
memory_manager_instance.remember(
    "My name is Hemanth"
)

memory_manager_instance.remember(
    "I like Python"
)

memory_manager_instance.remember(
    "I had tea today"
)

# Verify the results using the db instance
print(db.get_all())