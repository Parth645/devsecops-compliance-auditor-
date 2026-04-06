#!/usr/bin/env python3
"""
Script to create PostgreSQL database and tables for the compliance auditor.
Run this script first to set up your database.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from schema.database import Base
from schema.schema import Organization, Project, Scan, Violation
import uuid

# Load environment variables
load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in .env file")
        return False
    
    # Extract database name and connection without database
    from urllib.parse import urlparse
    parsed = urlparse(database_url)
    db_name = parsed.path[1:]  # Remove leading slash
    
    # Connection without database name for creating database
    base_url = f"{parsed.scheme}://{parsed.netloc}/postgres"
    
    try:
        # Connect to PostgreSQL server
        print("Connecting to PostgreSQL server...")
        engine = create_engine(base_url)
        
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            if result.fetchone():
                print(f"Database '{db_name}' already exists.")
            else:
                # Create database
                conn.execute(text("COMMIT"))  # End any transaction
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database '{db_name}' created successfully.")
        
        return True
    
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

def create_tables():
    """Create all tables using SQLAlchemy"""
    database_url = os.getenv("DATABASE_URL")
    
    try:
        print("Creating database tables...")
        engine = create_engine(database_url, echo=True)
        
        # Create all tables
        Base.metadata.create_all(engine)
        print("All tables created successfully!")
        
        return engine
    
    except Exception as e:
        print(f"Error creating tables: {e}")
        return None

def create_sample_organization(engine):
    """Create a sample organization for testing"""
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if sample org already exists
        existing = session.query(Organization).filter_by(name="Sample Organization").first()
        if existing:
            print(f"Sample organization already exists with ID: {existing.id}")
            return existing.id
        
        # Create sample organization
        sample_org = Organization(
            name="Sample Organization",
            api_key_hash="sample_api_key_hash_12345",  # In real app, this would be hashed
            tier="free",
            limits={
                "max_projects": 3,
                "max_scans_per_month": 100,
                "max_violations_per_scan": 1000
            }
        )
        
        session.add(sample_org)
        session.commit()
        
        print(f"Sample organization created with ID: {sample_org.id}")
        return sample_org.id
    
    except Exception as e:
        print(f"Error creating sample organization: {e}")
        session.rollback()
        return None
    
    finally:
        session.close()

def main():
    """Main setup function"""
    print("🚀 Setting up PostgreSQL database for Compliance Auditor...")
    print("=" * 60)
    
    # Step 1: Create database
    if not create_database():
        print("❌ Failed to create database. Please check your PostgreSQL connection.")
        sys.exit(1)
    
    # Step 2: Create tables
    engine = create_tables()
    if not engine:
        print("❌ Failed to create tables.")
        sys.exit(1)
    
    # Step 3: Create sample data
    org_id = create_sample_organization(engine)
    if org_id:
        print("✅ Sample organization created successfully!")
    
    print("=" * 60)
    print("🎉 Database setup complete!")
    print("\nNext steps:")
    print("1. Update your .env file with the correct PostgreSQL credentials")
    print("2. Run 'python main.py' to start the API server")
    print("3. Visit http://localhost:8000/docs to see the API documentation")
    
    print(f"\n📊 Database Info:")
    print(f"   • Database URL: {os.getenv('DATABASE_URL')}")
    print(f"   • Sample Org ID: {org_id}")

if __name__ == "__main__":
    main()