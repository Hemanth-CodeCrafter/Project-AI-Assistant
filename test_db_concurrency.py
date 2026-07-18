import unittest
import os
import sys
import threading

# Ensure the app's root directory is in the system path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.memory_db import MemoryDB

DB_FILE = "jarvis_memory.db"
NUM_THREADS = 5
WRITES_PER_THREAD = 100

class TestDbConcurrency(unittest.TestCase):

    def setUp(self):
        """Ensure the database is clean before each test."""
        if os.path.exists(DB_FILE):
            # Use a separate connection to clear the DB to avoid conflicts
            db = MemoryDB()
            db.clear()
            db.conn.close()

    def tearDown(self):
        """Clean up the database file after tests."""
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)

    def writer_task(self, thread_id: int):
        """
        A task for each thread. It creates its own DB connection
        and performs a number of writes.
        """
        try:
            db = MemoryDB()
            for i in range(WRITES_PER_THREAD):
                unique_memory = f"Memory from thread {thread_id}, item {i}"
                db.save(memory=unique_memory, category=f"thread-{thread_id}")
            db.conn.close()
        except Exception as e:
            # Store exception to be checked in the main thread
            self.thread_exceptions.append(e)


    def test_concurrent_writes_from_multiple_threads(self):
        """
        Tests that multiple threads, each with its own MemoryDB instance
        (and thus its own connection), can write to the database concurrently
        without raising a 'database is locked' or threading error.
        """
        self.thread_exceptions = []
        threads = []
        
        for i in range(NUM_THREADS):
            thread = threading.Thread(target=self.writer_task, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Assert that no exceptions occurred in the writer threads
        self.assertEqual(len(self.thread_exceptions), 0, f"Threads raised exceptions: {self.thread_exceptions}")

        # Verify the final state of the database
        final_db = MemoryDB()
        all_memories = final_db.get_all()
        final_db.conn.close()
        
        expected_records = NUM_THREADS * WRITES_PER_THREAD
        self.assertEqual(len(all_memories), expected_records, "The number of records in the database does not match the expected number of writes.")

if __name__ == '__main__':
    unittest.main()
