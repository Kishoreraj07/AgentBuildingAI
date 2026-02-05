from flask import Flask, request, jsonify
import subprocess
import threading
import signal
import os

app = Flask(__name__)

agent_process = None
agent_lock = threading.Lock()
stop_requested = False


@app.route("/run_agent", methods=["POST"])
def run_agent():
    global agent_process, stop_requested

    data = request.json or {}

    python_executable = data.get("python_executable")
    python_code = data.get("python_code")
    current_dir = data.get("current_dir")
    creation_flags = data.get("creation_flags", 0)

    if not python_executable or not python_code or not current_dir:
        return jsonify({
            "success": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "Missing required parameters"
        }), 400

    try:
        with agent_lock:
            if agent_process and agent_process.poll() is None:
                return jsonify({
                    "success": False,
                    "returncode": 1,
                    "stdout": "",
                    "stderr": "Agent already running"
                }), 409

            if os.name == "nt":
                agent_process = subprocess.Popen(
                    [python_executable, "-c", python_code],
                    cwd=current_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                agent_process = subprocess.Popen(
                    [python_executable, "-c", python_code],
                    cwd=current_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True
                )

        stdout, stderr = agent_process.communicate()
        rc = agent_process.returncode

        with agent_lock:
            if stop_requested:
                stop_requested = False
                return jsonify({
                    "success": False,
                    "returncode": -99,
                    "stdout": stdout or "",
                    "stderr": "stopped_by_user"
                })

        return jsonify({
            "success": rc == 0,
            "returncode": rc,
            "stdout": stdout or "",
            "stderr": stderr or ""
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "returncode": 1,
            "stdout": "",
            "stderr": str(e)
        }), 500

    finally:
        with agent_lock:
            agent_process = None


@app.route("/stop_agent", methods=["POST"])
def stop_agent():
    global agent_process, stop_requested

    with agent_lock:
        stop_requested = True

        if agent_process and agent_process.poll() is None:
            try:
                if os.name == "nt":
                    subprocess.run(
                        f"taskkill /PID {agent_process.pid} /T /F",
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    os.killpg(os.getpgid(agent_process.pid), signal.SIGTERM)

                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "message": str(e)}), 500

        return jsonify({"success": False, "message": "no agent running"}), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050)
