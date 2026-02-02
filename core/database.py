import sqlite3
import os
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_path="output/superlink.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Verified Leads Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verified_leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    email TEXT UNIQUE,
                    phone TEXT,
                    location TEXT,
                    contact_person TEXT,
                    business_scope TEXT,
                    source_url TEXT,
                    verification_status TEXT, -- 'valid', 'invalid', 'pending'
                    verification_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_verified_at TIMESTAMP
                )
            ''')
            
            # 2. Email Sending Records
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_send_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    recipient_email TEXT,
                    subject TEXT,
                    template_name TEXT,
                    status TEXT, -- 'sent', 'failed', 'bounced'
                    error_message TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES verified_leads(id)
                )
            ''')
            
            # 3. Feedback Records
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_email TEXT,
                    subject TEXT,
                    body TEXT,
                    intent_category TEXT, -- 'high_interest', 'consulting', 'no_interest', 'complaint'
                    ai_analysis TEXT,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

    def add_verified_lead(self, lead_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO verified_leads 
                    (company_name, email, phone, location, contact_person, business_scope, source_url, verification_status, verification_details, last_verified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lead_data.get('公司名称'),
                    lead_data.get('公开邮箱'),
                    lead_data.get('公开电话'),
                    lead_data.get('注册国家/城市'),
                    lead_data.get('业务负责人'),
                    lead_data.get('业务范围'),
                    lead_data.get('来源URL'),
                    lead_data.get('status', 'pending'),
                    lead_data.get('details', ''),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Email already exists
                return False

    def log_email_sent(self, lead_id, email, subject, template, status, error=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO email_send_records (lead_id, recipient_email, subject, template_name, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (lead_id, email, subject, template, status, error))
            conn.commit()

    def add_feedback(self, feedback_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO feedback_records (sender_email, subject, body, intent_category, ai_analysis)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                feedback_data.get('from'),
                feedback_data.get('subject'),
                feedback_data.get('body'),
                feedback_data.get('category'),
                feedback_data.get('analysis')
            ))
            conn.commit()
