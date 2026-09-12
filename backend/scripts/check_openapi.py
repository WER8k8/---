import sys
import argparse
import os

# Add the project root to sys.path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.main import app
except ImportError as e:
    print(f"Failed to import app.main: {e}")
    sys.exit(1)

def check_openapi(warn_only: bool = False):
    schema = app.openapi()
    paths = schema.get("paths", {})
    
    errors = []
    
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch", "options", "head", "trace"]:
                continue
                
            has_summary = bool(operation.get("summary"))
            has_description = bool(operation.get("description"))
            has_tags = bool(operation.get("tags"))
            
            if not (has_summary or has_description):
                errors.append(f"[{method.upper()}] {path} is missing summary or description.")
                
            if not has_tags:
                errors.append(f"[{method.upper()}] {path} is missing tags.")
                
            responses = operation.get("responses", {})
            has_2xx = False
            valid_response_schema = False
            
            for status_code, response in responses.items():
                if str(status_code).startswith("2"):
                    has_2xx = True
                    if str(status_code) == "204":
                        valid_response_schema = True
                    else:
                        content = response.get("content", {})
                        if "application/json" in content:
                            valid_response_schema = True
                            
            if not has_2xx:
                errors.append(f"[{method.upper()}] {path} is missing a 2xx response definition.")
            elif not valid_response_schema:
                errors.append(f"[{method.upper()}] {path} has a 2xx response but is missing application/json schema (and is not 204).")

    if errors:
        print("OpenAPI Schema Validation Failed:")
        for error in errors:
            print(f" - {error}")
        
        if not warn_only:
            sys.exit(1)
        else:
            print("\nRunning in --warn-only mode. Exiting with 0 despite errors.")
            sys.exit(0)
    else:
        print("OpenAPI Schema Validation Passed!")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check OpenAPI schema compliance.")
    parser.add_argument("--warn-only", action="store_true", help="Warn only, do not exit with 1 on errors.")
    args = parser.parse_args()
    
    check_openapi(warn_only=args.warn_only)
