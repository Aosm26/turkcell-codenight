from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import os

app = Flask(__name__)
app.secret_key = "turkcell-smart-allocation-2024"

API_URL = os.getenv("API_URL", "http://localhost:8000")


def api_get(endpoint):
    try:
        response = requests.get(f"{API_URL}{endpoint}")
        return response.json() if response.ok else []
    except:
        return []


def api_post(endpoint, data=None):
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=data or {})
        return response.json() if response.ok else None
    except:
        return None


@app.route("/")
def dashboard():
    summary = api_get("/dashboard/summary")
    requests_list = api_get("/requests?status=PENDING")
    allocations = api_get("/allocations?status=ASSIGNED")
    resources = api_get("/resources")

    return render_template(
        "dashboard.html",
        summary=summary,
        requests=requests_list[:10],
        allocations=allocations[:10],
        resources=resources,
    )


@app.route("/requests")
def requests_page():
    status = request.args.get("status", "")
    urgency = request.args.get("urgency", "")

    endpoint = "/requests"
    params = []
    if status:
        params.append(f"status={status}")
    if urgency:
        params.append(f"urgency={urgency}")
    if params:
        endpoint += "?" + "&".join(params)

    requests_list = api_get(endpoint)
    return render_template("requests.html", requests=requests_list)


@app.route("/requests/new", methods=["GET", "POST"])
def new_request():
    if request.method == "POST":
        data = {
            "user_id": request.form["user_id"],
            "service": request.form["service"],
            "request_type": request.form["request_type"],
            "urgency": request.form["urgency"],
        }
        result = api_post("/requests", data)
        if result:
            flash("Talep başarıyla oluşturuldu!", "success")
            return redirect(url_for("requests_page"))
        else:
            flash("Talep oluşturulamadı!", "error")

    return render_template("new_request.html")


@app.route("/resources")
def resources_page():
    resources = api_get("/resources")
    allocations = api_get("/allocations?status=ASSIGNED")

    # Calculate utilization per resource
    for res in resources:
        active = sum(
            1 for a in allocations if a.get("resource_id") == res["resource_id"]
        )
        res["active_allocations"] = active
        res["utilization"] = (
            (active / res["capacity"] * 100) if res["capacity"] > 0 else 0
        )

    return render_template("resources.html", resources=resources)


@app.route("/allocations")
def allocations_page():
    allocations = api_get("/allocations")
    return render_template("allocations.html", allocations=allocations)


@app.route("/allocate", methods=["POST"])
def allocate():
    result = api_post("/allocations/allocate")
    if result:
        flash(f"{len(result)} talep başarıyla atandı!", "success")
    else:
        flash("Atama yapılamadı!", "error")
    return redirect(url_for("dashboard"))


@app.route("/rules")
def rules_page():
    rules = api_get("/rules")
    return render_template("rules.html", rules=rules)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
