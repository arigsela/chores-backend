import os
from pathlib import Path

def collect_python_files(start_dir, output_file):
    """
    Recursively collects .py files, ignoring folders that start with a dot.
    """
    start_path = Path(start_dir).resolve()
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(start_path):
            # Remove directories that start with a dot (modifies dirs in place)
            dirs[:] = [d for d in dirs if not d.startswith('.') 
                       and not d.startswith('venv') 
                       and not d.startswith('__')
                       and not d.startswith('getfiles')
                       ]
            
            # Only process .py files
            for filename in files:
                if not filename.endswith('.py'):
                    continue
                    
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(start_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                    
                    outfile.write(f"\n# {relative_path}\n")
                    outfile.write(content)
                    outfile.write("\n")
                except Exception as e:
                    outfile.write(f"\n# Error reading {relative_path}: {str(e)}\n")

if __name__ == "__main__":
    collect_python_files(os.getcwd(), "python_files_only.txt")
    print("Collection complete - check python_files_only.txt")