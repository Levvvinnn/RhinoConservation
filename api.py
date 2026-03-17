from flask import Blueprint, jsonify, request
from datetime import datetime
from typing import Any, Dict, Tuple

import db
from models import RhinoStatus

api = Blueprint("api", __name__, url_prefix="/api")


def _error(message: str, status: int = 400) -> Tuple[Any, int]:
    """Uniform error response."""
    return jsonify({"success": False, "error": message}), status


def _get_json() -> Dict:
    """Safely parse JSON payload, returning an empty dict on invalid input."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {}
    return data


# ============ RHINO ENDPOINTS ============


@api.route("/rhinos", methods=["GET"])
def get_rhinos():
    """Get all rhinos."""
    try:
        rhinos = db.get_all_rhinos()
        return jsonify({"success": True, "data": rhinos}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/rhinos/<rhino_id>", methods=["GET"])
def get_rhino(rhino_id):
    """Get a single rhino by ID."""
    try:
        rhino = db.get_rhino(rhino_id)
        if not rhino:
            return jsonify({"success": False, "error": "Rhino not found"}), 404
        return jsonify({"success": True, "data": rhino}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/rhinos", methods=["POST"])
def create_rhino():
    """Create a new rhino.
    
    Expected JSON:
    {
        "id": "RHINO001",
        "name": "Simba",
        "species": "white",
        "collar_id": "COLLAR123",
        "status": "active" (optional)
    }
    """
    data = _get_json()

    required = ["id", "name", "species", "collar_id"]
    if not all(data.get(k) for k in required):
        return _error("Missing required fields", 400)

    status = data.get("status", "active")
    if status not in {s.value for s in RhinoStatus}:
        return _error(f"Invalid status: {status}", 400)

    success = db.create_rhino(data["id"], data["name"], data["species"], data["collar_id"], status)
    if not success:
        return _error("Rhino ID or collar_id already exists", 409)

    return jsonify({"success": True, "message": "Rhino created"}), 201


@api.route("/rhinos/<rhino_id>", methods=["PUT"])
def update_rhino(rhino_id):
    """Update rhino information.
    
    Expected JSON:
    {
        "name": "NewName" (optional),
        "status": "active|inactive|injured|missing" (optional),
        "health_notes": "Some notes" (optional)
    }
    """
    data = _get_json()

    status = data.get("status")
    if status and status not in {s.value for s in RhinoStatus}:
        return _error(f"Invalid status: {status}", 400)

    success = db.update_rhino(
        rhino_id, name=data.get("name"), status=status, health_notes=data.get("health_notes")
    )

    if not success:
        return _error("Failed to update rhino", 400)

    return jsonify({"success": True, "message": "Rhino updated"}), 200


@api.route("/rhinos/<rhino_id>", methods=["DELETE"])
def delete_rhino(rhino_id):
    """Delete (deactivate) a rhino."""
    try:
        success = db.delete_rhino(rhino_id)
        if not success:
            return jsonify({"success": False, "error": "Failed to delete rhino"}), 400
        return jsonify({"success": True, "message": "Rhino deleted"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============ LOCATION ENDPOINTS ============


@api.route("/rhinos/<rhino_id>/location", methods=["POST"])
def add_location(rhino_id):
    """Add a GPS location for a rhino.
    
    Expected JSON:
    {
        "latitude": 12.34567,
        "longitude": 98.76543,
        "altitude": 150.5 (optional),
        "accuracy": 5.0 (optional),
        "sats": 12 (optional)
    }
    """
    data = _get_json()

    if "latitude" not in data or "longitude" not in data:
        return _error("latitude and longitude required", 400)

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
    except (TypeError, ValueError):
        return _error("latitude and longitude must be numeric", 400)

    altitude = data.get("altitude")
    accuracy = data.get("accuracy")
    sats = data.get("sats")

    try:
        altitude = float(altitude) if altitude is not None else None
    except (TypeError, ValueError):
        return _error("altitude must be numeric", 400)

    try:
        accuracy = float(accuracy) if accuracy is not None else None
    except (TypeError, ValueError):
        return _error("accuracy must be numeric", 400)

    try:
        sats = int(sats) if sats is not None else None
    except (TypeError, ValueError):
        return _error("sats must be an integer", 400)

    success = db.add_location(
        rhino_id,
        latitude,
        longitude,
        altitude=altitude,
        accuracy=accuracy,
        sats=sats,
    )

    if not success:
        return _error("Failed to add location", 400)

    return jsonify({"success": True, "message": "Location added"}), 201


@api.route("/rhinos/<rhino_id>/location/latest", methods=["GET"])
def get_latest_location(rhino_id):
    """Get the most recent location for a rhino."""
    try:
        location = db.get_latest_location(rhino_id)
        if not location:
            return jsonify({"success": False, "error": "No location found"}), 404
        return jsonify({"success": True, "data": location}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/rhinos/<rhino_id>/location/history", methods=["GET"])
def get_location_history(rhino_id):
    """Get location history for a rhino.
    
    Query parameters:
    - limit: number of records to return (default: 100)
    """
    try:
        limit = request.args.get("limit", 100, type=int)
        if limit <= 0 or limit > 1000:
            return _error("limit must be between 1 and 1000", 400)

        locations = db.get_location_history(rhino_id, limit)
        return jsonify({"success": True, "data": locations}), 200
    except Exception as e:
        return _error("Internal server error", 500)


@api.route("/locations/latest", methods=["GET"])
def get_all_latest_locations():
    """Get the latest location for all rhinos."""
    try:
        locations = db.get_all_latest_locations()
        return jsonify({"success": True, "data": locations}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============ ALERT ENDPOINTS ============


@api.route("/alerts", methods=["GET"])
def get_alerts():
    """Get all alerts.
    
    Query parameters:
    - rhino_id: filter by rhino (optional)
    - unresolved_only: only show unresolved alerts (default: False)
    """
    try:
        rhino_id = request.args.get("rhino_id")
        unresolved_only = request.args.get("unresolved_only", False, type=bool)
        alerts = db.get_alerts(rhino_id, unresolved_only)
        return jsonify({"success": True, "data": alerts}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/rhinos/<rhino_id>/alerts", methods=["GET"])
def get_rhino_alerts(rhino_id):
    """Get all alerts for a specific rhino.
    
    Query parameters:
    - unresolved_only: only show unresolved alerts (default: False)
    """
    try:
        unresolved_only = request.args.get("unresolved_only", False, type=bool)
        alerts = db.get_alerts(rhino_id, unresolved_only)
        return jsonify({"success": True, "data": alerts}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/rhinos/<rhino_id>/alerts", methods=["POST"])
def create_alert(rhino_id):
    """Create a new alert for a rhino.
    
    Expected JSON:
    {
        "alert_type": "poacher_detected|low_battery|injury|missing",
        "message": "Description of the alert"
    }
    """
    try:
        data = request.get_json()

        if "alert_type" not in data or "message" not in data:
            return jsonify({"success": False, "error": "alert_type and message required"}), 400

        success = db.create_alert(rhino_id, data["alert_type"], data["message"])

        if not success:
            return jsonify({"success": False, "error": "Failed to create alert"}), 400

        return jsonify({"success": True, "message": "Alert created"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api.route("/alerts/<int:alert_id>/resolve", methods=["PUT"])
def resolve_alert(alert_id):
    """Mark an alert as resolved."""
    try:
        success = db.resolve_alert(alert_id)
        if not success:
            return jsonify({"success": False, "error": "Failed to resolve alert"}), 400
        return jsonify({"success": True, "message": "Alert resolved"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
