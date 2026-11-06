# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import List, Dict, Any
import sqlite3
from config.settings import DB_PATH
from database import RESUMES_TABLE_SQL

class ResumeModel:
    def __init__(self):
        self.db_path = DB_PATH
        self._init_database()
    
    def _init_database(self):
        """Initialize resume table if not exists"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(RESUMES_TABLE_SQL)
            conn.commit()
    
    def add_resume(self, file_path: str, name: str, is_active: bool = False) -> int:
        """Add a new resume to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO resumes (name, file_path, is_active)
                VALUES (?, ?, ?)
            ''', (name, file_path, 1 if is_active else 0))
            conn.commit()
            return cursor.lastrowid
    
    def list_resumes(self) -> List[Dict[str, Any]]:
        """List all resumes"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM resumes ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_active_resume(self) -> Dict[str, Any]:
        """Get the currently active resume"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM resumes WHERE is_active = 1 LIMIT 1')
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def set_active_resume_by_path(self, file_path: str):
        """Set a resume as active by file path"""
        with sqlite3.connect(self.db_path) as conn:
            # Deactivate all others
            conn.execute('UPDATE resumes SET is_active = 0')
            # Activate selected
            conn.execute('UPDATE resumes SET is_active = 1 WHERE file_path = ?', (file_path,))
            conn.commit()
    
    def delete_resume_by_path(self, file_path: str):
        """Delete a resume by file path"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM resumes WHERE file_path = ?', (file_path,))
            conn.commit()
