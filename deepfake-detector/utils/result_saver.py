"""
Save and load analysis results with proper ID handling
"""

import os
import json
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RESULTS_FOLDER


def save_result(result):
    """Save analysis result to JSON file with result_id"""
    try:
        # Generate result ID if not present
        if 'result_id' not in result:
            result['result_id'] = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Create filename with result_id for easy lookup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"result_{timestamp}_{result['result_id'][:8]}.json"
        filepath = os.path.join(RESULTS_FOLDER, filename)
        
        # Save result with indent for readability
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Store the filename in result for reference
        result['saved_file'] = filename
        
        print(f"✅ Result saved: {filename} (ID: {result['result_id']})")
        if result.get('thumbnail_path'):
            print(f"   📸 Thumbnail: {result['thumbnail_path']}")
        
        return filepath
        
    except Exception as e:
        print(f"❌ Error saving result: {e}")
        return None


def load_results(limit=100):
    """Load recent results with proper result_id"""
    results = []
    
    try:
        # Check if results folder exists
        if not os.path.exists(RESULTS_FOLDER):
            print(f"⚠️ Results folder not found: {RESULTS_FOLDER}")
            return []
        
        # Get all result files
        files = [f for f in os.listdir(RESULTS_FOLDER) 
                if f.startswith('result_') and f.endswith('.json')]
        files.sort(reverse=True)  # Newest first
        
        # Load up to limit files
        for filename in files[:limit]:
            filepath = os.path.join(RESULTS_FOLDER, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                    
                    # Ensure result_id exists
                    if 'result_id' not in result:
                        # Extract from filename if possible
                        if '_' in filename:
                            parts = filename.split('_')
                            if len(parts) >= 3:
                                result['result_id'] = parts[2].replace('.json', '')
                            else:
                                result['result_id'] = filename.replace('.json', '')
                        else:
                            result['result_id'] = filename.replace('.json', '')
                    
                    result['saved_file'] = filename
                    results.append(result)
                    
            except Exception as e:
                print(f"⚠️ Error loading {filename}: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Error loading results: {e}")
    
    return results


def get_result_by_id(result_id):
    """Get a specific result by its ID"""
    results = load_results(1000)  # Load all results
    for result in results:
        if result.get('result_id') == result_id:
            return result
    return None


def delete_result(result_id):
    """Delete a saved result by ID"""
    results = load_results(1000)
    for result in results:
        if result.get('result_id') == result_id:
            filepath = os.path.join(RESULTS_FOLDER, result['saved_file'])
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
    return False