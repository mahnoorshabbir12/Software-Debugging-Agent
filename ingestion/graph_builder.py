import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Set
from neo4j import GraphDatabase
from ingestion.parser import TreeSitterParser

log = logging.getLogger(__name__)

class CodeGraphBuilder:
    def __init__(self, uri: str = "neo4j://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.parser = TreeSitterParser()
        
    def close(self):
        self.driver.close()
        
    def _create_indexes(self):
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (func:Function) REQUIRE func.id IS UNIQUE")
            
    def _extract_python_nodes(self, tree: Any, file_path: str) -> Dict[str, Any]:
        """
        Extract functions, calls, and imports using tree-sitter.
        This uses heuristic traversal.
        """
        functions = []
        calls = []
        imports = []
        
        root = tree.root_node
        
        def traverse(node, current_func=None):
            if node.type == 'function_definition':
                # find the name node
                for child in node.children:
                    if child.type == 'identifier':
                        func_name = child.text.decode('utf8')
                        functions.append({
                            'name': func_name,
                            'id': f"{file_path}::{func_name}",
                            'file': file_path
                        })
                        current_func = func_name
                        break
                        
            elif node.type == 'call':
                for child in node.children:
                    if child.type == 'identifier' or child.type == 'attribute':
                        # Simple heuristic: just grab the text of the callable
                        callee_name = child.text.decode('utf8')
                        if '.' in callee_name:
                            callee_name = callee_name.split('.')[-1]
                        calls.append({
                            'caller': current_func,
                            'callee': callee_name,
                            'file': file_path
                        })
                        break
                        
            elif node.type in ('import_statement', 'import_from_statement'):
                for child in node.children:
                    if child.type == 'dotted_name':
                        imports.append(child.text.decode('utf8'))
                        
            for child in node.children:
                traverse(child, current_func)
                
        traverse(root)
        
        return {
            "functions": functions,
            "calls": calls,
            "imports": imports
        }

    def ingest_repository(self, project_root: str):
        self._create_indexes()
        
        root = Path(project_root).resolve()
        
        for root_dir, _, files in os.walk(root):
            for file in files:
                if not file.endswith(".py"):
                    continue
                    
                path = Path(root_dir) / file
                
                # skip venv, hidden, etc
                if any(part.startswith('.') for part in path.parts) or 'venv' in path.parts:
                    continue
                    
                rel_path = str(path.relative_to(root)).replace("\\", "/")
                
                try:
                    parsed = self.parser.parse_file(str(path))
                    data = self._extract_python_nodes(parsed['tree'], rel_path)
                    self._ingest_file_data(rel_path, data)
                except Exception as e:
                    log.warning(f"Failed to parse/ingest {rel_path}: {e}")
                    
        self._resolve_calls()

    def _ingest_file_data(self, file_path: str, data: Dict[str, Any]):
        """Write nodes and intra-file edges to Neo4j"""
        with self.driver.session() as session:
            # Create File node
            session.run(
                "MERGE (f:File {path: $path})",
                path=file_path
            )
            
            # Create Function nodes and DEFINES edges
            for func in data['functions']:
                session.run("""
                    MERGE (f:File {path: $file_path})
                    MERGE (func:Function {id: $func_id})
                    SET func.name = $func_name
                    MERGE (f)-[:DEFINES]->(func)
                """, file_path=file_path, func_id=func['id'], func_name=func['name'])
                
            # Create CALLS edges (as temporary string relations that we'll resolve later)
            for call in data['calls']:
                caller = call['caller']
                if caller:
                    caller_id = f"{file_path}::{caller}"
                    session.run("""
                        MERGE (func:Function {id: $caller_id})
                        MERGE (func)-[:CALLS_RAW]->(callee:UnresolvedName {name: $callee_name})
                    """, caller_id=caller_id, callee_name=call['callee'])
                else:
                    # module-level call
                    session.run("""
                        MERGE (f:File {path: $file_path})
                        MERGE (f)-[:CALLS_RAW]->(callee:UnresolvedName {name: $callee_name})
                    """, file_path=file_path, callee_name=call['callee'])
                    
            # Create IMPORTS edges
            for imp in data['imports']:
                session.run("""
                    MERGE (f:File {path: $file_path})
                    MERGE (m:Module {name: $module_name})
                    MERGE (f)-[:IMPORTS]->(m)
                """, file_path=file_path, module_name=imp)
                
    def _resolve_calls(self):
        """Resolve CALLS_RAW edges to actual Function nodes where names match."""
        with self.driver.session() as session:
            # Resolve function-to-function calls
            session.run("""
                MATCH (caller)-[r:CALLS_RAW]->(u:UnresolvedName)
                MATCH (callee:Function {name: u.name})
                MERGE (caller)-[:CALLS]->(callee)
            """)
            # Cleanup unresolved raw edges (optional, but keeps graph clean)
            session.run("MATCH ()-[r:CALLS_RAW]->() DELETE r")
            session.run("MATCH (u:UnresolvedName) WHERE NOT ()-->(u) DELETE u")
