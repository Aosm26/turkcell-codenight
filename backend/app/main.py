from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from models import User, Resource, Request, AllocationRule
from routers import auth, dashboard, notifications
from middleware import RequestLoggingMiddleware
from logging_config import api_logger, database_logger
import csv
import os
from datetime import datetime

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Turkcell Smart Allocation API",
    description="Dinamik Kaynak ve Öncelik Yönetim Platformu",
    version="1.0.0",
)

# Logging middleware (en dışta olmalı)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)


@app.get("/")
def root():
    return {"message": "Turkcell Smart Allocation API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}


def load_seed_data():
    """Load initial data from CSV files"""
    db = SessionLocal()

    try:
        # Check if data already exists
        if db.query(User).count() > 0:
            database_logger.info("Seed data already loaded, skipping...")
            return

        seed_dir = "/app/seed_data"
        if not os.path.exists(seed_dir):
            seed_dir = "./seed_data"
        if not os.path.exists(seed_dir):
            seed_dir = "../seed_data"
        if not os.path.exists(seed_dir):
            database_logger.warning("Seed data directory not found")
            return

        database_logger.info(f"Loading seed data from: {seed_dir}")

        # Load services
        services_file = os.path.join(seed_dir, "services.csv")
        if os.path.exists(services_file):
            from models import Service

            with open(services_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                services_count = 0
                for row in reader:
                    service = Service(
                        service_id=row["service_id"],
                        name=row["name"],
                        icon=row.get("icon"),
                        description=row.get("description"),
                    )
                    db.add(service)
                    services_count += 1
                database_logger.info(f"Loaded {services_count} services")

        # Load request types
        request_types_file = os.path.join(seed_dir, "request_types.csv")
        if os.path.exists(request_types_file):
            from models import RequestType

            with open(request_types_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                types_count = 0
                for row in reader:
                    req_type = RequestType(
                        type_id=row["type_id"],
                        service_id=row["service_id"],
                        name=row["name"],
                        description=row.get("description"),
                        icon=row.get("icon"),
                    )
                    db.add(req_type)
                    types_count += 1
                database_logger.info(f"Loaded {types_count} request types")

        # Load users
        users_file = os.path.join(seed_dir, "users.csv")
        if os.path.exists(users_file):
            from auth import get_password_hash

            with open(users_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                users_count = 0
                for row in reader:
                    user = User(
                        user_id=row["user_id"],
                        name=row["name"],
                        city=row["city"],
                        service_id=row.get("service_id") or None,
                        password_hash=get_password_hash(row.get("password", "user123")),
                        role=row.get("role", "USER"),
                    )
                    db.add(user)
                    users_count += 1
                database_logger.info(f"Loaded {users_count} users")

        # Load resources
        resources_file = os.path.join(seed_dir, "resources.csv")
        if os.path.exists(resources_file):
            with open(resources_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                resources_count = 0
                for row in reader:
                    resource = Resource(
                        resource_id=row["resource_id"],
                        resource_type=row["resource_type"],
                        capacity=int(row["capacity"]),
                        city=row["city"],
                        status=row["status"],
                    )
                    db.add(resource)
                    resources_count += 1
                database_logger.info(f"Loaded {resources_count} resources")

        # Load requests
        requests_file = os.path.join(seed_dir, "requests.csv")
        if os.path.exists(requests_file):
            with open(requests_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                requests_count = 0
                for row in reader:
                    req = Request(
                        request_id=row["request_id"],
                        user_id=row["user_id"],
                        service_id=row["service_id"],
                        request_type_id=row["request_type_id"],
                        urgency=row["urgency"],
                        created_at=datetime.fromisoformat(
                            row["created_at"].replace("Z", "+00:00")
                        ),
                        status="PENDING",
                    )
                    db.add(req)
                    requests_count += 1
                database_logger.info(f"Loaded {requests_count} requests")

        # Load allocation rules
        rules_file = os.path.join(seed_dir, "allocation_rules.csv")
        if os.path.exists(rules_file):
            with open(rules_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rules_count = 0
                for row in reader:
                    rule = AllocationRule(
                        rule_id=row["rule_id"],
                        condition=row["condition"],
                        weight=int(row["weight"]),
                        is_active=row["is_active"].lower() == "true",
                    )
                    db.add(rule)
                    rules_count += 1
                database_logger.info(f"Loaded {rules_count} allocation rules")

        # Load derived variables
        variables_file = os.path.join(seed_dir, "derived_variables.csv")
        if os.path.exists(variables_file):
            from models import DerivedVariable

            with open(variables_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                vars_count = 0
                for row in reader:
<<<<<<< HEAD
                    var = DerivedVariable(
                        variable_id=row["variable_id"],
                        name=row["name"],
                        formula=row["formula"],
                        description=row.get("description"),
=======
                    option = AppOption(
                        category=row["category"],
                        key=row["key"],
                        value=row["value"],
                        icon=row.get("icon") or None,
                        order=int(row.get("order", 0)),
>>>>>>> dfbe5a019b945a033813f1830a57ca3ebe1b91a1
                    )
                    db.add(var)
                    vars_count += 1
                database_logger.info(f"Loaded {vars_count} derived variables")

        db.commit()
        database_logger.info("✅ Seed data loaded successfully")

    except Exception as e:
        database_logger.error(f"Error loading seed data: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    api_logger.info("🚀 Turkcell Smart Allocation API starting...")
    load_seed_data()
    api_logger.info("✅ API startup complete")
