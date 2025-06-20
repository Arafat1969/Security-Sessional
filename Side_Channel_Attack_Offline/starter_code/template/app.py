from flask import Flask, request, jsonify, send_from_directory
# additional imports
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import sqlite3

app = Flask(__name__)

stored_traces = []
stored_heatmaps = []

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/collect_trace', methods=['POST'])
def collect_trace():
    """ 
    Implement the collect_trace endpoint to receive trace data from the frontend and generate a heatmap.
    1. Receive trace data from the frontend as JSON
    2. Generate a heatmap using matplotlib
    3. Store the heatmap and trace data in the backend temporarily
    4. Return the heatmap image and optionally other statistics to the frontend
    """
    data = request.json
    trace = data.get("trace")
    stored_traces.append(trace)

    # Compute min, max, range, samples count
    arr = np.array(trace)
    stats = {
        "min": int(arr.min()),
        "max": int(arr.max()),
        "range": int(arr.max() - arr.min()),
        "samples": len(arr)
    }

    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 2))
    ax.imshow([trace], aspect='auto', cmap='hot')
    ax.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    encoded_img = base64.b64encode(buf.read()).decode('utf-8')
    stored_heatmaps.append({"image": encoded_img, "stats": stats})
    return jsonify({
        "image": encoded_img,
        "stats": stats
    })


@app.route('/api/clear_results', methods=['POST'])
def clear_results():
    """ 
    Implment a clear results endpoint to reset stored data.
    1. Clear stored traces and heatmaps
    2. Return success/error message
    """
    stored_traces.clear()
    stored_heatmaps.clear()
    return jsonify({"status": "Cleared"})


# Additional endpoints can be implemented here as needed.
@app.route('/api/get_results', methods=['GET'])
def get_results():
    """ 
    Retrieve all collected traces and heatmaps.
    1. Return the stored trace data and generated heatmaps.
    2. Send it back to the frontend.
    """
    return jsonify({
        "traces": stored_traces,
        "heatmaps": stored_heatmaps
    })



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)