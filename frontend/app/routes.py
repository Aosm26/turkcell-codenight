from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import requests
import os
from logging_config import dashboard_logger

app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY", "default-flask-secret-change-in-production"
)

API_URL = os.getenv("API_URL", "http://localhost:8000")  # Auth Service
BUSINESS_URL = os.getenv(
    "BUSINESS_SERVICE_URL", "http://localhost:8001"
)  # Business Service

dashboard_logger.info(
    f"🚀 Flask Dashboard starting... API_URL={API_URL}, BUSINESS_URL={BUSINESS_URL}"
)


# ============ Helper Functions ============


def get_auth_header():
    """Get authorization header if user is logged in"""
    token = session.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def api_get(endpoint, auth=False):
    """Make GET request to API"""
    try:
        headers = get_auth_header() if auth else {}
        dashboard_logger.debug(f"GET {API_URL}{endpoint}")
        response = requests.get(f"{API_URL}{endpoint}", headers=headers)
        if response.ok:
            return response.json()
        dashboard_logger.warning(
            f"API GET failed: {endpoint} -> {response.status_code}"
        )
        return []
    except Exception as e:
        dashboard_logger.error(f"API GET error: {endpoint} -> {e}")
        return []


def api_post(endpoint, data=None, auth=False, form_data=False):
    """Make POST request to API"""
    try:
        headers = get_auth_header() if auth else {}
        dashboard_logger.debug(f"POST {API_URL}{endpoint}")

        if form_data:
            response = requests.post(f"{API_URL}{endpoint}", data=data, headers=headers)
        else:
            response = requests.post(
                f"{API_URL}{endpoint}", json=data or {}, headers=headers
            )

        if response.ok:
            dashboard_logger.info(f"API POST success: {endpoint}")
            return response.json()
        dashboard_logger.warning(
            f"API POST failed: {endpoint} -> {response.status_code}"
        )
        return None
    except Exception as e:
        dashboard_logger.error(f"API POST error: {endpoint} -> {e}")
        return None


def business_api_get(endpoint, auth=False):
    """Make GET request to Business Service"""
    try:
        headers = get_auth_header() if auth else {}
        dashboard_logger.debug(f"GET {BUSINESS_URL}{endpoint}")
        response = requests.get(f"{BUSINESS_URL}{endpoint}", headers=headers)
        if response.ok:
            return response.json()
        dashboard_logger.warning(
            f"Business API GET failed: {endpoint} -> {response.status_code}"
        )
        return []
    except Exception as e:
        dashboard_logger.error(f"Business API GET error: {endpoint} -> {e}")
        return []


def business_api_post(endpoint, data=None, auth=False):
    """Make POST request to Business Service"""
    try:
        headers = get_auth_header() if auth else {}
        dashboard_logger.debug(f"POST {BUSINESS_URL}{endpoint}")
        response = requests.post(
            f"{BUSINESS_URL}{endpoint}", json=data or {}, headers=headers
        )

        if response.ok:
            dashboard_logger.info(f"Business API POST success: {endpoint}")
            return response.json()
        dashboard_logger.warning(
            f"Business API POST failed: {endpoint} -> {response.status_code}"
        )
        return None
    except Exception as e:
        dashboard_logger.error(f"Business API POST error: {endpoint} -> {e}")
        return None


# ============ Decorators ============


def login_required(f):
    """Decorator to require login"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Lütfen giriş yapın", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Lütfen giriş yapın", "error")
            return redirect(url_for("login"))
        if session.get("role") != "ADMIN":
            flash("Bu sayfaya erişim yetkiniz yok", "error")
            return redirect(url_for("user_dashboard"))
        return f(*args, **kwargs)

    return decorated_function


# ============ Auth Routes ============


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        user_id = request.form.get("user_id")
        password = request.form.get("password")

        result = api_post(
            "/auth/login", {"username": user_id, "password": password}, form_data=True
        )

        if result:
            session["access_token"] = result["access_token"]
            session["user_id"] = result["user_id"]
            session["name"] = result["name"]
            session["role"] = result["role"]

            dashboard_logger.info(
                f"✅ User logged in: {result['user_id']} ({result['role']})"
            )
            flash(f"Hoş geldiniz, {result['name']}!", "success")

            return redirect(url_for("home"))
        else:
            flash("Kullanıcı adı veya şifre hatalı", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        data = {
            "user_id": request.form.get("user_id"),
            "name": request.form.get("name"),
            "city": request.form.get("city"),
            "password": request.form.get("password"),
        }

        result = api_post("/auth/register", data)

        if result:
            flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
            return redirect(url_for("login"))
        else:
            flash(
                "Kayıt başarısız. Kullanıcı adı zaten kullanılıyor olabilir.", "error"
            )

    return render_template("register.html")


@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    session.clear()
    dashboard_logger.info(f"User logged out: {user_id}")
    flash("Çıkış yapıldı", "success")
    return redirect(url_for("login"))


# ============ Home Route (Redirects based on role) ============


@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") == "ADMIN":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("user_dashboard"))


# ============ USER Routes ============


@app.route("/user")
@login_required
def user_dashboard():
    """User dashboard - my requests and notifications"""
    user_id = session.get("user_id")
    my_requests = api_get(f"/requests?user_id={user_id}", auth=True)
    notifications = api_get(f"/notifications/{user_id}", auth=True)

    return render_template(
        "user/dashboard.html", requests=my_requests, notifications=notifications
    )


@app.route("/user/new-request", methods=["GET", "POST"])
@login_required
def user_new_request():
    """Create a new service request"""
    if request.method == "POST":
        data = {
            "user_id": session.get("user_id"),
            "service": request.form.get("service"),
            "request_type": request.form.get("request_type"),
            "urgency": request.form.get("urgency"),
        }
        result = business_api_post("/requests", data, auth=True)
        if result:
            flash("Talebiniz başarıyla oluşturuldu!", "success")
            return redirect(url_for("user_dashboard"))
        else:
            flash("Talep oluşturulamadı!", "error")

    return render_template("user/new_request.html")


@app.route("/user/requests")
@login_required
def user_requests():
    """View all my requests"""
    user_id = session.get("user_id")
    my_requests = api_get(f"/requests?user_id={user_id}", auth=True)
    return render_template("user/requests.html", requests=my_requests)


# ============ ADMIN Routes ============


@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    try:
        # Fetch data from business service
        headers = get_auth_header()

        # Get all requests
        requests_resp = requests.get(f"{BUSINESS_API_URL}/requests", headers=headers)
        all_requests = requests_resp.json() if requests_resp.ok else []

        # Get all allocations
        allocations_resp = requests.get(
            f"{BUSINESS_API_URL}/allocations", headers=headers
        )
        all_allocations = allocations_resp.json() if allocations_resp.ok else []

        # Get all resources
        resources_resp = requests.get(f"{BUSINESS_API_URL}/resources", headers=headers)
        all_resources = resources_resp.json() if resources_resp.ok else []

        # Calculate stats
        pending_count = sum(1 for r in all_requests if r.get("status") == "PENDING")
        active_allocations = sum(
            1 for a in all_allocations if a.get("status") == "ASSIGNED"
        )
        available_resources = sum(
            1 for r in all_resources if r.get("status") == "AVAILABLE"
        )
        total_resources = len(all_resources)
        utilization = (
            (active_allocations / total_resources * 100) if total_resources > 0 else 0
        )

        dashboard_logger.info(
            f"Admin dashboard: {pending_count} pending, {active_allocations} active"
        )

        return render_template(
            "admin/dashboard.html",
            pending_requests=pending_count,
            active_allocations=active_allocations,
            available_resources=available_resources,
            utilization=round(utilization, 1),
            recent_allocations=all_allocations[:10],  # Last 10
            resources=all_resources,
        )
    except Exception as e:
        dashboard_logger.error(f"Error loading admin dashboard: {e}")
        return render_template(
            "admin/dashboard.html",
            pending_requests=0,
            active_allocations=0,
            available_resources=0,
            utilization=0,
            recent_allocations=[],
            resources=[],
        )


@app.route("/admin/requests")
@admin_required
def admin_requests():
    """View all requests"""
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

    requests_list = api_get(endpoint, auth=True)
    return render_template("admin/requests.html", requests=requests_list)


@app.route("/admin/resources")
@admin_required
def admin_resources():
    """View and manage resources"""
    resources = api_get("/resources", auth=True)
    allocations = api_get("/allocations?status=ASSIGNED", auth=True)

    for res in resources:
        active = sum(
            1 for a in allocations if a.get("resource_id") == res["resource_id"]
        )
        res["active_allocations"] = active
        res["utilization"] = (
            (active / res["capacity"] * 100) if res["capacity"] > 0 else 0
        )

    return render_template("admin/resources.html", resources=resources)


@app.route("/admin/allocations")
@admin_required
def admin_allocations():
    """View all allocations"""
    allocations = api_get("/allocations", auth=True)
    return render_template("admin/allocations.html", allocations=allocations)


@app.route("/admin/allocate", methods=["POST"])
@admin_required
def admin_allocate():
    """Run automatic allocation"""
    result = api_post("/allocations/allocate", auth=True)
    if result:
        flash(f"{len(result)} talep başarıyla atandı!", "success")
    else:
        flash("Atama yapılamadı!", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/rules")
@admin_required
def admin_rules():
    """View and manage allocation rules"""
    rules = api_get("/rules", auth=True)
    return render_template("admin/rules.html", rules=rules)


# ============ Context Processor ============


@app.context_processor
def inject_user():
    """Inject user info into all templates"""
    return {
        "current_user": {
            "user_id": session.get("user_id"),
            "name": session.get("name"),
            "role": session.get("role"),
            "is_authenticated": "user_id" in session,
            "is_admin": session.get("role") == "ADMIN",
        }
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
