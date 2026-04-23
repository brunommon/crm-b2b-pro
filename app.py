from datetime import datetime, timezone

from flask import Flask, jsonify, request

import storage

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _next_id(records):
    return str(max((int(r["id"]) for r in records), default=0) + 1)


def _utcnow():
    return datetime.now(timezone.utc).isoformat()


def _paginate(records, page, per_page):
    """Return a page slice plus metadata envelope."""
    total = len(records)
    start = (page - 1) * per_page
    items = records[start : start + per_page]
    return {
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": max(1, -(-total // per_page)),  # ceiling division
    }


def _pagination_params():
    """Parse and validate ?page= and ?per_page= query params."""
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except ValueError:
        return None, None, (jsonify({"error": "page and per_page must be integers"}), 400)
    if page < 1:
        return None, None, (jsonify({"error": "page must be >= 1"}), 400)
    if not (1 <= per_page <= 100):
        return None, None, (jsonify({"error": "per_page must be between 1 and 100"}), 400)
    return page, per_page, None


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------

@app.route("/companies", methods=["GET"])
def list_companies():
    page, per_page, err = _pagination_params()
    if err:
        return err
    data = storage.load()
    return jsonify(_paginate(data["companies"], page, per_page))


@app.route("/companies", methods=["POST"])
def create_company():
    body = request.get_json(silent=True) or {}
    if not body.get("name"):
        return jsonify({"error": "name is required"}), 400
    # TODO: Validate that website is a well-formed URL when provided
    data = storage.load()
    company = {
        "id": _next_id(data["companies"]),
        "name": body["name"],
        "industry": body.get("industry", ""),
        "website": body.get("website", ""),
        "created_at": _utcnow(),
    }
    data["companies"].append(company)
    storage.save(data)
    return jsonify(company), 201


@app.route("/companies/<company_id>", methods=["GET"])
def get_company(company_id):
    data = storage.load()
    company = next((c for c in data["companies"] if c["id"] == company_id), None)
    if company is None:
        return jsonify({"error": "company not found"}), 404
    return jsonify(company)


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------

@app.route("/contacts", methods=["GET"])
def list_contacts():
    page, per_page, err = _pagination_params()
    if err:
        return err
    data = storage.load()
    return jsonify(_paginate(data["contacts"], page, per_page))


@app.route("/contacts", methods=["POST"])
def create_contact():
    body = request.get_json(silent=True) or {}
    if not body.get("name"):
        return jsonify({"error": "name is required"}), 400
    if not body.get("email"):
        return jsonify({"error": "email is required"}), 400
    # TODO: Validate email format with a regex before persisting
    data = storage.load()
    contact = {
        "id": _next_id(data["contacts"]),
        "name": body["name"],
        "email": body["email"],
        "phone": body.get("phone", ""),
        "company_id": body.get("company_id"),
        "created_at": _utcnow(),
    }
    data["contacts"].append(contact)
    storage.save(data)
    return jsonify(contact), 201


@app.route("/contacts/<contact_id>", methods=["GET"])
def get_contact(contact_id):
    data = storage.load()
    contact = next((c for c in data["contacts"] if c["id"] == contact_id), None)
    if contact is None:
        return jsonify({"error": "contact not found"}), 404
    return jsonify(contact)


# ---------------------------------------------------------------------------
# Deals
# ---------------------------------------------------------------------------

DEAL_STAGES = ("prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost")


@app.route("/deals", methods=["GET"])
def list_deals():
    page, per_page, err = _pagination_params()
    if err:
        return err
    data = storage.load()
    return jsonify(_paginate(data["deals"], page, per_page))


@app.route("/deals", methods=["POST"])
def create_deal():
    body = request.get_json(silent=True) or {}
    if not body.get("title"):
        return jsonify({"error": "title is required"}), 400
    stage = body.get("stage", "prospecting")
    if stage not in DEAL_STAGES:
        return jsonify({"error": f"stage must be one of {DEAL_STAGES}"}), 400
    data = storage.load()
    deal = {
        "id": _next_id(data["deals"]),
        "title": body["title"],
        "value": body.get("value", 0),
        "stage": stage,
        "company_id": body.get("company_id"),
        "contact_id": body.get("contact_id"),
        "created_at": _utcnow(),
    }
    data["deals"].append(deal)
    storage.save(data)
    return jsonify(deal), 201


@app.route("/deals/<deal_id>", methods=["GET"])
def get_deal(deal_id):
    data = storage.load()
    deal = next((d for d in data["deals"] if d["id"] == deal_id), None)
    if deal is None:
        return jsonify({"error": "deal not found"}), 404
    return jsonify(deal)


if __name__ == "__main__":
    app.run(debug=True)
