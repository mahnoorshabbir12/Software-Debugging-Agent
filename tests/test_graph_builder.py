import pytest
import os
import tempfile
from pathlib import Path
from ingestion.graph_builder import CodeGraphBuilder

def test_graph_ingestion_and_retrieval():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        
        # Create some mock Python files to build our AST graph
        # 1. auth.py
        auth_file = root / "auth.py"
        auth_file.write_text("""
def verify_token(token):
    if not token:
        return False
    return True

def login(user, passw):
    token = "xyz"
    if verify_token(token):
        return True
    return False
""")

        # 2. main.py
        main_file = root / "main.py"
        main_file.write_text("""
import auth
from database import get_db

def start_server():
    db = get_db()
    auth.login("admin", "admin")
""")

        # Run ingestion
        builder = CodeGraphBuilder(uri="neo4j://localhost:7687", user="neo4j", password="password")
        
        # We need to wipe the db first in case this test runs multiple times
        with builder.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            
        builder.ingest_repository(str(root))
        
        # Now query the graph to ensure nodes and edges exist
        with builder.driver.session() as session:
            # Check files
            res = session.run("MATCH (f:File) RETURN f.path as path")
            files = [r["path"] for r in res]
            assert "auth.py" in files
            assert "main.py" in files
            
            # Check functions
            res = session.run("MATCH (f:Function) RETURN f.name as name")
            functions = [r["name"] for r in res]
            assert "verify_token" in functions
            assert "login" in functions
            assert "start_server" in functions
            
            # Check callers of verify_token
            res = session.run("""
                MATCH (caller:Function)-[:CALLS]->(callee:Function {name: 'verify_token'})
                RETURN caller.name as name
            """)
            callers = [r["name"] for r in res]
            assert "login" in callers
            
            # Check callers of login
            res = session.run("""
                MATCH (caller:Function)-[:CALLS]->(callee:Function {name: 'login'})
                RETURN caller.name as name
            """)
            callers = [r["name"] for r in res]
            assert "start_server" in callers
            
            # Check imports
            res = session.run("""
                MATCH (f:File {path: 'main.py'})-[:IMPORTS]->(m:Module)
                RETURN m.name as name
            """)
            imports = [r["name"] for r in res]
            assert "auth" in imports
            assert "database" in imports
            
        builder.close()
