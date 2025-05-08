import os
from pathlib import Path
import glob
from datetime import datetime
import time
from heapq import heappush, heappop

def search_file(filename, max_results=5, timeout=5):
    """
    Search for files matching the given filename pattern.
    Supports partial matches and common file extensions.
    Prioritizes most recently modified files.
    
    Args:
        filename (str): The filename or pattern to search for
        max_results (int): Maximum number of results to return
        timeout (int): Maximum time to search in seconds
        
    Returns:
        list: List of dictionaries containing file information:
            {
                'path': str,  # Full path to the file
                'name': str,  # Filename
                'extension': str,  # File extension
                'size': int,  # File size in bytes
                'modified': str,  # Last modified date
                'created': str   # Creation date
            }
    """
    start_time = time.time()
    
    # Common file extensions to check if none specified
    common_extensions = ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.xls']
    
    # Get user's home directory
    home_dir = str(Path.home())
    
    # Use a min heap to keep track of most recent files
    # We'll store (modification_time, file_info) tuples
    recent_files = []
    
    # If filename doesn't have an extension, try with common extensions
    if '.' not in filename:
        search_patterns = [f"**/*{filename}*{ext}" for ext in common_extensions]
    else:
        search_patterns = [f"**/*{filename}*"]
    
    # Search in common directories with max depth of 2
    search_dirs = [
        os.path.join(home_dir, 'Documents'),
        os.path.join(home_dir, 'Downloads'),
        os.path.join(home_dir, 'Desktop')
    ]
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
            
        for pattern in search_patterns:
            try:
                # Use glob to find matching files with max depth
                matches = glob.glob(os.path.join(search_dir, pattern), recursive=True)
                
                for file_path in matches:
                    # Check timeout
                    if time.time() - start_time > timeout:
                        print("\nSearch timeout reached. Returning best matches found so far.")
                        return [file_info for _, file_info in sorted(recent_files, reverse=True)]
                        
                    if os.path.isfile(file_path):
                        file_stat = os.stat(file_path)
                        mod_time = file_stat.st_mtime
                        
                        file_info = {
                            'path': file_path,
                            'name': os.path.basename(file_path),
                            'extension': os.path.splitext(file_path)[1],
                            'size': file_stat.st_size,
                            'modified': datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S'),
                            'created': datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # Add to heap, keeping only the most recent files
                        heappush(recent_files, (mod_time, file_info))
                        if len(recent_files) > max_results:
                            heappop(recent_files)
                            
            except Exception as e:
                print(f"Error searching in {search_dir}: {str(e)}")
                continue
    
    # Convert heap to sorted list (most recent first)
    results = [file_info for _, file_info in sorted(recent_files, reverse=True)]
    return results

if __name__ == "__main__":
    # Test the function
    test_filename = "resume"
    start_time = time.time()
    results = search_file(test_filename)
    end_time = time.time()
    
    print(f"\nSearch completed in {end_time - start_time:.2f} seconds")
    print(f"Searching for files containing '{test_filename}':")
    for result in results:
        print(f"\nFile: {result['name']}")
        print(f"Path: {result['path']}")
        print(f"Size: {result['size']} bytes")
        print(f"Modified: {result['modified']}")
        print(f"Created: {result['created']}")