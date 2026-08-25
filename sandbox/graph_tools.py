from typing import List, Dict, Any, Annotated
from langchain_core.tools import tool, InjectedToolArg
from neo4j import GraphDatabase

def _get_driver():
    """Returns a Neo4j driver connection. Assumes default credentials."""
    return GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "password"))

@tool
def get_function_callers(
    function_name: str, 
    project_root: Annotated[str, InjectedToolArg]
) -> str:
    """
    Finds all functions that call the given function_name. 
    Use this to trace backwards up the call stack to see what depends on this function.
    """
    driver = _get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (caller:Function)-[:CALLS]->(callee:Function {name: $func_name})
                RETURN caller.name as caller_name, caller.id as caller_id
            """, func_name=function_name)
            
            records = list(result)
            if not records:
                return f"No callers found for function '{function_name}'."
                
            out = [f"Functions calling '{function_name}':"]
            for record in records:
                # caller_id is 'file_path::function_name'
                out.append(f"- {record['caller_id']}")
                
            return f"<file_content>\n" + "\n".join(out) + "\n</file_content>"
    except Exception as e:
        return f"<file_content>\nError querying graph: {e}\n</file_content>"
    finally:
        driver.close()

@tool
def get_function_dependencies(
    function_name: str, 
    project_root: Annotated[str, InjectedToolArg]
) -> str:
    """
    Finds all functions that the given function_name calls.
    Use this to trace forwards down the call stack to see what this function depends on.
    """
    driver = _get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (caller:Function {name: $func_name})-[:CALLS]->(callee:Function)
                RETURN callee.name as callee_name, callee.id as callee_id
            """, func_name=function_name)
            
            records = list(result)
            if not records:
                return f"Function '{function_name}' does not call any known functions."
                
            out = [f"Function '{function_name}' calls:"]
            for record in records:
                out.append(f"- {record['callee_id']}")
                
            return f"<file_content>\n" + "\n".join(out) + "\n</file_content>"
    except Exception as e:
        return f"<file_content>\nError querying graph: {e}\n</file_content>"
    finally:
        driver.close()

@tool
def get_file_imports(
    file_path: str,
    project_root: Annotated[str, InjectedToolArg]
) -> str:
    """
    Finds all external modules or files imported by the given file_path.
    Use this to understand a file's external dependencies.
    """
    # ensure we have relative path for matching neo4j nodes
    import os
    if os.path.isabs(file_path):
        from pathlib import Path
        try:
            file_path = str(Path(file_path).relative_to(project_root)).replace("\\", "/")
        except ValueError:
            pass # ignore, fallback to what was given
            
    file_path = file_path.replace("\\", "/")
    
    driver = _get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (f:File {path: $file_path})-[:IMPORTS]->(m:Module)
                RETURN m.name as module_name
            """, file_path=file_path)
            
            records = list(result)
            if not records:
                return f"No imports found for file '{file_path}'."
                
            out = [f"File '{file_path}' imports:"]
            for record in records:
                out.append(f"- {record['module_name']}")
                
            return f"<file_content>\n" + "\n".join(out) + "\n</file_content>"
    except Exception as e:
        return f"<file_content>\nError querying graph: {e}\n</file_content>"
    finally:
        driver.close()
