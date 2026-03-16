from flask import Blueprint, jsonify, request
from datetime import datetime
import db

api = Blueprint("api", __name__, url_prefix="/api")


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
    try:
        data = request.get_json()

        # Validate required fields
        required = ["id", "name", "species", "collar_id"]
        if not all(k in data for k in required):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        status = data.get("status", "active")
        success = db.create_rhino(data["id"], data["name"], data["species"], data["collar_id"], status)

        if not success:
            return jsonify({"success": False, "error": "Rhino ID or collar_id already exists"}), 409

        return jsonify({"success": True, "message": "Rhino created"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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
    try:
        data = request.get_json()
        success = db.update_rhino(
            rhino_id, name=data.get("name"), status=data.get("status"), health_notes=data.get("health_notes")
        )

        if not success:
            return jsonify({"success": False, "error": "Failed to update rhino"}), 400

        return jsonify({"success": True, "message": "Rhino updated"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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
    try:
        data = request.get_json()

        # Validate required fields
        if "latitude" not in data or "longitude" not in data:
            return jsonify({"success": False, "error": "latitude and longitude required"}), 400

        success = db.add_location(
            rhino_id,
            data["latitude"],
            data["longitude"],
            altitude=data.get("altitude"),
            accuracy=data.get("accuracy"),
            sats=data.get("sats"),
        )

        if not success:
            return jsonify({"success": False, "error": "Failed to add location"}), 400

        return jsonify({"success": True, "message": "Location added"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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
        locations = db.get_location_history(rhino_id, limit)
        return jsonify({"success": True, "data": locations}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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
