from core.chroma_helper import get_chroma_client, get_global_chroma_client

"""
REST API interface for Nexus EVO
External integrations and HTTP access
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
from typing import Dict, Any
from agents.orchestrator import orchestrator
from tools.registry import registry
from macros import library as macro_library
from core.events import event_bus, EventType
from utils import get_logger
from app_config import config

logger = get_logger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web clients


# ============ AGENT ENDPOINTS ============

@app.route('/api/v1/execute', methods=['POST'])
def execute_task():
    """Execute a task"""
    try:
        data = request.get_json()
        task = data.get('task')
        context = data.get('context')
        
        if not task:
            return jsonify({'error': 'No task provided'}), 400
        
        result = orchestrator.execute(task, context)
        
        return jsonify({
            'success': True,
            'task': task,
            'result': result,
            'reasoning_steps': len(orchestrator.get_task_history())
        })
        
    except Exception as e:
        logger.error(f"Task execution error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/status', methods=['GET'])
def get_status():
    """Get agent status"""
    status = orchestrator.get_status()
    return jsonify(status)


@app.route('/api/v1/history', methods=['GET'])
def get_history():
    """Get task history"""
    limit = request.args.get('limit', 10, type=int)
    history = orchestrator.get_task_history()
    return jsonify({
        'history': history[-limit:],
        'total': len(history)
    })


@app.route('/api/v1/reasoning', methods=['GET'])
def get_reasoning():
    """Get last reasoning trace"""
    summary = orchestrator.get_reasoning_summary()
    return jsonify({'reasoning': summary})


# ============ TOOL ENDPOINTS ============

@app.route('/api/v1/tools', methods=['GET'])
def list_tools():
    """List all available tools"""
    tools = registry.get_all_tools_info()
    return jsonify({
        'tools': tools,
        'count': len(tools)
    })


@app.route('/api/v1/tools/<tool_name>', methods=['GET'])
def get_tool_info(tool_name: str):
    """Get information about a specific tool"""
    info = registry.get_tool_info(tool_name)
    if info:
        return jsonify(info)
    return jsonify({'error': 'Tool not found'}), 404


@app.route('/api/v1/tools/<tool_name>/execute', methods=['POST'])
def execute_tool(tool_name: str):
    """Execute a tool directly"""
    try:
        params = request.get_json() or {}
        result = registry.execute_tool(tool_name, **params)
        
        return jsonify({
            'success': result.success,
            'output': result.output,
            'error': result.error,
            'metadata': result.metadata
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ MACRO ENDPOINTS ============

@app.route('/api/v1/macros', methods=['GET'])
def list_macros():
    """List all saved macros"""
    macros = macro_library.list_all()
    return jsonify({
        'macros': macros,
        'count': len(macros)
    })


@app.route('/api/v1/macros/<macro_name>', methods=['GET'])
def get_macro(macro_name: str):
    """Get macro by name"""
    macro = macro_library.load_by_name(macro_name)
    if macro:
        return jsonify(macro.to_dict())
    return jsonify({'error': 'Macro not found'}), 404


@app.route('/api/v1/macros/<macro_name>/execute', methods=['POST'])
def execute_macro(macro_name: str):
    """Execute a macro"""
    try:
        from macros import player
        
        macro = macro_library.load_by_name(macro_name)
        if not macro:
            return jsonify({'error': 'Macro not found'}), 404
        
        context = request.get_json() or {}
        result = player.play(macro, context)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/macros/search', methods=['POST'])
def search_macros():
    """Search macros"""
    data = request.get_json()
    query = data.get('query', '')
    n_results = data.get('n_results', 5)
    
    macros = macro_library.search(query, n_results)
    
    return jsonify({
        'query': query,
        'results': [m.to_dict() for m in macros],
        'count': len(macros)
    })


# ============ EVENT ENDPOINTS ============

@app.route('/api/v1/events', methods=['GET'])
def get_events():
    """Get event history"""
    limit = request.args.get('limit', 100, type=int)
    event_type_str = request.args.get('type')
    
    event_type = None
    if event_type_str:
        try:
            event_type = EventType(event_type_str)
        except ValueError:
            return jsonify({'error': 'Invalid event type'}), 400
    
    events = event_bus.get_history(event_type, limit)
    
    return jsonify({
        'events': [e.to_dict() for e in events],
        'count': len(events)
    })


@app.route('/api/v1/events/stream', methods=['GET'])
def stream_events():
    """Stream events (SSE)"""
    def generate():
        # Subscribe to events
        queue = []
        
        def callback(event):
            queue.append(event)
        
        # Subscribe to all event types
        for event_type in EventType:
            event_bus.subscribe(event_type, callback)
        
        try:
            while True:
                if queue:
                    event = queue.pop(0)
                    yield f"data: {json.dumps(event.to_dict())}\n\n"
                else:
                    import time
                    time.sleep(0.1)
        finally:
            # Cleanup
            for event_type in EventType:
                event_bus.unsubscribe(event_type, callback)
    
    return Response(generate(), mimetype='text/event-stream')


# ============ HEALTH ENDPOINTS ============

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'agent': 'nexus_evo',
        'tools': len(registry.list_tools()),
        'macros': macro_library.get_count()
    })


@app.route('/api/v1/info', methods=['GET'])
def get_info():
    """Get system information"""
    return jsonify({
        'agent': {
            'name': 'Nexus EVO',
            'version': '2.0',
            'description': 'Autonomous AI Agent with ReAct reasoning'
        },
        'capabilities': {
            'tools': len(registry.list_tools()),
            'macros': macro_library.get_count(),
            'reasoning': 'ReAct',
            'memory': 'ChromaDB (RAG)',
            'interfaces': ['CLI', 'Telegram', 'WebSocket', 'REST']
        },
        'status': orchestrator.get_status()
    })


# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============ SERVER FUNCTIONS ============

def run_rest_api(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """Run the REST API server"""
    logger.info(f"Starting REST API server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


def run_rest_api_thread(host: str = '0.0.0.0', port: int = 5000):
    """Run REST API in background thread"""
    import threading
    thread = threading.Thread(
        target=lambda: run_rest_api(host, port, debug=False),
        daemon=True
    )
    thread.start()
    logger.info(f"REST API started in background thread on http://{host}:{port}")
    return thread
