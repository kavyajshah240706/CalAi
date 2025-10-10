"""
Flask API for Food Volume Estimation
Wraps the terminal-based volume estimation model into a REST API
"""

from flask import Flask, request, jsonify, send_file
import os
import subprocess
import json
import uuid
from datetime import datetime
import shutil
from pathlib import Path

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create necessary directories
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, RESULTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Model configuration (adjust these paths to your actual model files)
DEPTH_MODEL_ARCHITECTURE = 'C:/Users/Kavya Shah/Downloads/food_volume_estimation/monovideo_fine_tune_food_videos.json'
DEPTH_MODEL_WEIGHTS = 'C:/Users/Kavya Shah/Downloads/food_volume_estimation/monovideo_fine_tune_food_videos.h5'
SEGMENTATION_WEIGHTS = 'C:/Users/Kavya Shah/Downloads/food_volume_estimation/mask_rcnn_food_segmentation.h5'
FOV = 70  # Camera field of view
GT_DEPTH_SCALE = 0.5  # Expected distance
MIN_DEPTH = 0.01
MAX_DEPTH = 10
RELAXATION_PARAM = 0.01


def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def run_volume_estimation(image_path, output_dir, session_id):
    """
    Run the volume estimation command and capture results
    
    Args:
        image_path: Path to input image
        output_dir: Directory to store output plots
        session_id: Unique session identifier
    
    Returns:
        dict: Results containing volumes and output paths
    """
    results_file = os.path.join(RESULTS_FOLDER, f'{session_id}_results.csv')
    
    # Build the command to run the volume estimator
    cmd = [
        'python', 'volume_estimator.py',
        '--input_images', image_path,
        '--depth_model_architecture', DEPTH_MODEL_ARCHITECTURE,
        '--depth_model_weights', DEPTH_MODEL_WEIGHTS,
        '--segmentation_weights', SEGMENTATION_WEIGHTS,
        '--fov', str(FOV),
        '--gt_depth_scale', str(GT_DEPTH_SCALE),
        '--min_depth', str(MIN_DEPTH),
        '--max_depth', str(MAX_DEPTH),
        '--relaxation_param', str(RELAXATION_PARAM),
        '--plot_results',
        '--results_file', results_file,
        '--plots_directory', output_dir
    ]
    
    try:
        # Run the command and capture output (Python 3.6 compatible)
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=True
        )
        
        # Decode the output
        stdout = result.stdout.decode('utf-8') if result.stdout else ''
        stderr = result.stderr.decode('utf-8') if result.stderr else ''
        
        return {
            'success': True,
            'stdout': stdout,
            'stderr': stderr,
            'results_file': results_file
        }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Processing timeout exceeded'
        }
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode('utf-8') if e.stderr else 'Unknown error'
        return {
            'success': False,
            'error': f'Volume estimation failed: {stderr}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def parse_results(results_file, output_dir):
    """
    Parse the results CSV and collect output images
    
    Args:
        results_file: Path to results CSV
        output_dir: Directory containing output plots
    
    Returns:
        dict: Parsed results with image paths
    """
    import pandas as pd
    
    results = {
        'segments': [],
        'output_images': [],
        'total_volume': 0
    }
    
    # Read results CSV if it exists
    if os.path.exists(results_file):
        try:
            df = pd.read_csv(results_file)
            for idx, row in df.iterrows():
                segment = {
                    'segment_id': idx + 1,
                    'volume': float(row.get('volume', 0))
                }
                results['segments'].append(segment)
                results['total_volume'] += segment['volume']
        except Exception as e:
            print(f"Error parsing results: {e}")
    
    # Collect all generated images
    if os.path.exists(output_dir):
        for file in sorted(os.listdir(output_dir)):
            if file.endswith(('.png', '.jpg', '.jpeg')):
                results['output_images'].append(
                    os.path.join(output_dir, file)
                )
    
    return results


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/estimate-volume', methods=['POST'])
def estimate_volume():
    """
    Main endpoint for volume estimation
    
    Expected: multipart/form-data with 'image' field
    Returns: JSON with volumes and paths to generated images
    """
    
    # Check if image file is present
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg'}), 400
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Save uploaded image
    filename = f"{session_id}_{file.filename}"
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)
    
    # Generate sequential output number
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # IMPORTANT: This assumes the output JSON files are in the same directory as app.py
    existing_outputs = [f for f in os.listdir(base_dir) if f.startswith('output') and f.endswith('.json')]
    output_num = len(existing_outputs) + 1
    output_dir = f'output{output_num}'
    
    # --- CHANGE #1: Define the correct filename here ---
    actual_metadata_file = f'output{output_num}.json'
        
    try:
        # Run volume estimation
        estimation_result = run_volume_estimation(
            input_path, 
            output_dir, 
            session_id
        )
        
        if not estimation_result['success']:
            return jsonify({
                'error': estimation_result.get('error', 'Unknown error'),
                'session_id': session_id
            }), 500
        
        # Parse results and collect output images
        results = parse_results(
            estimation_result['results_file'], 
            output_dir
        )
        
        # --- CHANGE #2: Remove this entire block of code ---
        # It was trying to copy a file that doesn't exist to a name we don't want.
        # metadata_source = os.path.join(output_dir, 'metadata.json')
        # metadata_dest = f'metadata_{session_id}.json' 
        # if os.path.exists(metadata_source):
        #     shutil.copy(metadata_source, metadata_dest)
        
        # Build response
        response = {
            'session_id': session_id,
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'input_image': filename,
            'total_volume': results['total_volume'],
            # --- CHANGE #3: Use the correct filename variable ---
            'metadata_file': actual_metadata_file, 
            'segments': results['segments'],
            'output_images': [
                f"/get-image/{session_id}/{os.path.basename(img)}" 
                for img in results['output_images']
            ],
            'num_segments': len(results['segments'])
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
            'session_id': session_id
        }), 500


@app.route('/get-image/<session_id>/<filename>', methods=['GET'])
def get_image(session_id, filename):
    """
    Retrieve a generated output image
    
    Args:
        session_id: Session identifier
        filename: Image filename
    """
    image_path = os.path.join(OUTPUT_FOLDER, session_id, filename)
    
    if not os.path.exists(image_path):
        return jsonify({'error': 'Image not found'}), 404
    
    return send_file(image_path, mimetype='image/png')


@app.route('/get-all-images/<session_id>', methods=['GET'])
def get_all_images(session_id):
    """
    Get all output images for a session as a zip file
    
    Args:
        session_id: Session identifier
    """
    import zipfile
    import io
    
    output_dir = os.path.join(OUTPUT_FOLDER, session_id)
    
    if not os.path.exists(output_dir):
        return jsonify({'error': 'Session not found'}), 404
    
    # Create zip file in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in os.listdir(output_dir):
            if file.endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(output_dir, file)
                zf.write(file_path, arcname=file)
    
    memory_file.seek(0)
    
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{session_id}_outputs.zip'
    )


@app.route('/cleanup/<session_id>', methods=['DELETE'])
def cleanup_session(session_id):
    """
    Clean up files for a specific session
    
    Args:
        session_id: Session identifier
    """
    try:
        # Remove uploaded image
        for file in os.listdir(UPLOAD_FOLDER):
            if file.startswith(session_id):
                os.remove(os.path.join(UPLOAD_FOLDER, file))
        
        # Remove output directory
        output_dir = os.path.join(OUTPUT_FOLDER, session_id)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        
        # Remove results file
        results_file = os.path.join(RESULTS_FOLDER, f'{session_id}_results.csv')
        if os.path.exists(results_file):
            os.remove(results_file)
        
        return jsonify({
            'success': True,
            'message': f'Session {session_id} cleaned up'
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': f'Cleanup failed: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0', port=5000)