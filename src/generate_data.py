"""Generate the deterministic Northstar Technologies synthetic dataset.

The generator intentionally creates coherent organizational patterns rather
than independent random errors. See docs/process_analysis.md for the pattern
design and the metrics pipeline for evidence calculated from the output.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .config import ANALYSIS_YEAR, RAW_DIR, SEED, SYSTEM_UPDATE_DATE
from .rule_engine import catalog_frame, expected_steps


DEPARTMENTS = [
    ("D01", "Engineering", "Product & Technology", 36_000_000),
    ("D02", "Product", "Product & Technology", 16_000_000),
    ("D03", "Sales", "Revenue", 24_000_000),
    ("D04", "Marketing", "Revenue", 12_500_000),
    ("D05", "Customer Success", "Revenue", 11_000_000),
    ("D06", "Field Operations", "Operations", 28_000_000),
    ("D07", "Finance", "Corporate", 8_500_000),
    ("D08", "People", "Corporate", 7_500_000),
    ("D09", "Legal", "Corporate", 6_000_000),
    ("D10", "Information Security", "Product & Technology", 9_500_000),
]

LOCATIONS = ["Chicago", "Austin", "New York", "San Francisco", "Denver"]
PURCHASE_TYPES = ["Software", "Equipment", "Contractor", "Travel", "Professional Services", "Facilities", "AI Services"]
TYPE_WEIGHTS = np.array([0.24, 0.18, 0.14, 0.15, 0.12, 0.10, 0.07])
TYPE_MULTIPLIER = {
    "Software": 1.15,
    "Equipment": 1.25,
    "Contractor": 2.1,
    "Travel": 0.45,
    "Professional Services": 1.65,
    "Facilities": 1.3,
    "AI Services": 1.45,
}


def _departments() -> pd.DataFrame:
    return pd.DataFrame(DEPARTMENTS, columns=["department_id", "department_name", "business_unit", "budget"])


def _employees(rng: np.random.Generator, departments: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    employee_number = 1
    for dept in departments.itertuples(index=False):
        dept_ids: list[str] = []
        director_id = f"EMP-{employee_number:04d}"
        rows.append({
            "employee_id": director_id,
            "employee_name": f"Northstar Employee {employee_number:04d}",
            "department_id": dept.department_id,
            "department": dept.department_name,
            "role": "Director",
            "manager_id": "EMP-0001" if employee_number != 1 else "",
            "manager": "Executive Leadership" if employee_number == 1 else "Northstar Employee 0001",
            "approval_limit": 150_000,
            "location": rng.choice(LOCATIONS, p=[0.29, 0.21, 0.18, 0.17, 0.15]),
            "tenure_years": round(float(rng.uniform(3, 14)), 1),
        })
        dept_ids.append(director_id)
        employee_number += 1
        manager_ids: list[str] = []
        for manager_ix in range(1, 12):
            employee_id = f"EMP-{employee_number:04d}"
            manager_ids.append(employee_id)
            limit = float(rng.choice([15_000, 25_000, 50_000, 75_000], p=[0.18, 0.34, 0.34, 0.14]))
            rows.append({
                "employee_id": employee_id,
                "employee_name": f"Northstar Employee {employee_number:04d}",
                "department_id": dept.department_id,
                "department": dept.department_name,
                "role": "Manager" if manager_ix > 2 else "Senior Manager",
                "manager_id": director_id,
                "manager": f"Northstar Employee {int(director_id[-4:]):04d}",
                "approval_limit": limit,
                "location": rng.choice(LOCATIONS, p=[0.29, 0.21, 0.18, 0.17, 0.15]),
                "tenure_years": round(float(rng.uniform(2, 12)), 1),
            })
            dept_ids.append(employee_id)
            employee_number += 1
        while len(dept_ids) < 200:
            employee_id = f"EMP-{employee_number:04d}"
            manager_id = str(rng.choice(manager_ids))
            role = str(rng.choice(["Analyst", "Specialist", "Senior Analyst", "Program Manager", "Associate"], p=[0.27, 0.22, 0.20, 0.16, 0.15]))
            manager_number = int(manager_id[-4:])
            rows.append({
                "employee_id": employee_id,
                "employee_name": f"Northstar Employee {employee_number:04d}",
                "department_id": dept.department_id,
                "department": dept.department_name,
                "role": role,
                "manager_id": manager_id,
                "manager": f"Northstar Employee {manager_number:04d}",
                "approval_limit": 0,
                "location": rng.choice(LOCATIONS, p=[0.29, 0.21, 0.18, 0.17, 0.15]),
                "tenure_years": round(float(rng.uniform(0.1, 10)), 1),
            })
            dept_ids.append(employee_id)
            employee_number += 1
    return pd.DataFrame(rows)


def _vendors(rng: np.random.Generator, count: int = 140) -> pd.DataFrame:
    countries = ["United States", "Canada", "United Kingdom", "Germany", "India", "Ireland", "Singapore"]
    rows = []
    for i in range(1, count + 1):
        category = str(rng.choice(PURCHASE_TYPES, p=TYPE_WEIGHTS))
        approved = bool(rng.random() > 0.18)
        risk = str(rng.choice(["Low", "Medium", "High"], p=[0.52, 0.34, 0.14] if approved else [0.22, 0.43, 0.35]))
        rows.append({
            "vendor_id": f"VEN-{i:03d}",
            "vendor_name": f"{category.replace(' ', '')} Partner {i:03d}",
            "vendor_category": category,
            "approved_vendor": approved,
            "risk_level": risk,
            "contract_status": str(rng.choice(["Active", "Pending", "Expired"], p=[0.78, 0.13, 0.09])),
            "country": str(rng.choice(countries, p=[0.68, 0.08, 0.06, 0.05, 0.06, 0.04, 0.03])),
        })
    return pd.DataFrame(rows)


def _requests(
    rng: np.random.Generator,
    departments: pd.DataFrame,
    employees: pd.DataFrame,
    vendors: pd.DataFrame,
    count: int,
) -> pd.DataFrame:
    requesters = employees[~employees.role.isin(["Director", "Senior Manager"])].copy()
    department_weights = {
        "Engineering": 0.19, "Product": 0.11, "Sales": 0.13, "Marketing": 0.09,
        "Customer Success": 0.08, "Field Operations": 0.15, "Finance": 0.06,
        "People": 0.07, "Legal": 0.04, "Information Security": 0.08,
    }
    dept_names = list(department_weights)
    start = pd.Timestamp(f"{ANALYSIS_YEAR}-01-01")
    date_offsets = rng.integers(0, 365, size=count)
    rows = []
    for i in range(1, count + 1):
        department_name = str(rng.choice(dept_names, p=list(department_weights.values())))
        employee = requesters[requesters.department == department_name].sample(1, random_state=int(rng.integers(0, 2**31 - 1))).iloc[0]
        purchase_type = str(rng.choice(PURCHASE_TYPES, p=TYPE_WEIGHTS))
        matching = vendors[vendors.vendor_category == purchase_type]
        vendor = matching.sample(1, random_state=int(rng.integers(0, 2**31 - 1))).iloc[0]
        amount = float(np.clip(rng.lognormal(mean=8.35, sigma=1.0) * TYPE_MULTIPLIER[purchase_type], 120, 160_000))
        request_date = start + pd.Timedelta(days=int(date_offsets[i - 1])) + pd.Timedelta(hours=int(rng.integers(8, 18)))
        urgency = str(rng.choice(["Standard", "Priority", "Urgent"], p=[0.70, 0.21, 0.09]))
        risk = "High" if vendor.risk_level == "High" or purchase_type == "AI Services" else ("Medium" if amount > 20_000 or vendor.risk_level == "Medium" else "Low")
        final_status = str(rng.choice(["Paid", "Rejected", "Cancelled"], p=[0.92, 0.055, 0.025]))
        post_update = request_date >= pd.Timestamp(SYSTEM_UPDATE_DATE)
        if not post_update:
            source_system = "ProcureFlow Classic"
        elif employee.location == "Austin" and rng.random() < 0.48:
            source_system = "ProcureFlow Classic"
        else:
            source_system = "NovaProcure"
        exception_used = bool(amount > 20_000 and rng.random() < (0.24 if department_name == "Marketing" else 0.10))
        exception_documented = bool(not exception_used or rng.random() < (0.58 if department_name == "Marketing" else 0.90))
        rows.append({
            "request_id": f"PR-{10000 + i}",
            "employee_id": employee.employee_id,
            "department_id": employee.department_id,
            "vendor_id": vendor.vendor_id,
            "request_date": request_date,
            "purchase_type": purchase_type,
            "amount": round(amount, 2),
            "currency": "USD",
            "description": f"{purchase_type} purchase for {department_name} operations",
            "urgency": urgency,
            "risk_category": risk,
            "contract_required": bool(purchase_type in {"Software", "Contractor", "Professional Services", "AI Services"} or amount > 50_000),
            "security_review_required": bool(purchase_type in {"Software", "AI Services"} or (vendor.risk_level == "High" and purchase_type == "Equipment")),
            "competitive_bid_required": bool(amount > 20_000),
            "exception_documented": exception_documented,
            "urgency_documented": bool(urgency != "Urgent" or rng.random() < (0.72 if department_name == "Field Operations" else 0.92)),
            "final_status": final_status,
            "source_system": source_system,
            "system_period": "After update" if post_update else "Before update",
        })
    requests = pd.DataFrame(rows)

    # Inject deterministic, review-worthy near-threshold clusters without
    # labelling intent. The detection engine must rediscover these from data.
    eligible = requests[(requests.request_date < "2025-12-01") & requests.final_status.eq("Paid")].copy()
    cluster_indices = eligible.sample(36, random_state=SEED + 99).index.to_list()
    for cluster_number in range(12):
        ix = cluster_indices[cluster_number * 3 : cluster_number * 3 + 3]
        anchor = requests.loc[ix[0]].copy()
        if cluster_number < 6:
            base_date = pd.Timestamp("2025-01-10") + pd.Timedelta(days=int(rng.integers(0, 150)))
            cluster_period = "Before update"
            cluster_system = "ProcureFlow Classic"
        else:
            base_date = pd.Timestamp("2025-07-10") + pd.Timedelta(days=int(rng.integers(0, 140)))
            cluster_period = "After update"
            cluster_system = "NovaProcure"
        for j, row_index in enumerate(ix):
            requests.loc[row_index, ["employee_id", "department_id", "vendor_id", "purchase_type", "source_system"]] = [
                anchor.employee_id, anchor.department_id, anchor.vendor_id, anchor.purchase_type, cluster_system
            ]
            requests.loc[row_index, "request_date"] = base_date + pd.Timedelta(days=j * int(rng.integers(3, 7)), hours=10 + j)
            requests.loc[row_index, "amount"] = round(float(rng.uniform(9_050, 9_950)), 2)
            requests.loc[row_index, "description"] = f"Phased {anchor.purchase_type.lower()} purchase"
            requests.loc[row_index, "system_period"] = cluster_period
    return requests.sort_values("request_date").reset_index(drop=True)


def _event_actor(
    rng: np.random.Generator,
    activity: str,
    request: pd.Series,
    employee_lookup: pd.DataFrame,
    department_pools: dict[str, list[str]],
    managers: pd.DataFrame,
    violate_limit: bool = False,
    self_approve: bool = False,
) -> tuple[str, str]:
    if activity in {"Request Submitted", "Request Resubmitted"}:
        return request.employee_id, "Requester"
    if self_approve and "Approval" in activity:
        return request.employee_id, "Requester"
    if activity == "Manager Approval":
        requester = employee_lookup.loc[request.employee_id]
        manager_id = requester.manager_id
        manager = employee_lookup.loc[manager_id]
        if violate_limit:
            return manager_id, manager.role
        eligible = managers[(managers.department == requester.department) & (managers.approval_limit >= request.amount)]
        if eligible.empty:
            eligible = managers[managers.approval_limit >= request.amount]
        actor = eligible.sample(1, random_state=int(rng.integers(0, 2**31 - 1))).iloc[0] if not eligible.empty else manager
        return actor.employee_id, actor.role
    if activity == "Director Approval":
        pool = managers[(managers.department == request.department_name) & (managers.role == "Director")]
        actor = pool.iloc[0]
        return actor.employee_id, "Director"
    routing = {
        "Finance Approval": "Finance",
        "Payment Authorized": "Finance",
        "Legal Review": "Legal",
        "Security Review": "Information Security",
        "Procurement Review": "Field Operations",
        "Vendor Validation": "Field Operations",
        "Competitive Bid Confirmed": "Field Operations",
        "Exception Approved": "Finance",
        "Purchase Order Created": "Field Operations",
        "Returned for Revision": "Finance",
        "Rejected": "Finance",
    }
    department = routing.get(activity, request.department_name)
    actor_id = str(rng.choice(department_pools[department]))
    return actor_id, activity.replace(" Approval", " Approver").replace(" Review", " Reviewer")


def _events(
    rng: np.random.Generator,
    requests: pd.DataFrame,
    employees: pd.DataFrame,
    vendors: pd.DataFrame,
    departments: pd.DataFrame,
) -> pd.DataFrame:
    employee_lookup = employees.set_index("employee_id", drop=False)
    managers = employees[employees.role.isin(["Manager", "Senior Manager", "Director"])].copy()
    department_pools = employees.groupby("department").employee_id.apply(list).to_dict()
    vendor_lookup = vendors.set_index("vendor_id")
    dept_lookup = departments.set_index("department_id")
    events: list[dict] = []
    event_number = 1

    for _, request_base in requests.iterrows():
        request = request_base.copy()
        vendor = vendor_lookup.loc[request.vendor_id]
        department = dept_lookup.loc[request.department_id]
        request["approved_vendor"] = vendor.approved_vendor
        request["vendor_risk"] = vendor.risk_level
        request["country"] = vendor.country
        request["department_name"] = department.department_name
        request["business_unit"] = department.business_unit
        request["exception_count"] = 0 if request.exception_documented else 1
        planned = expected_steps(request)
        post = request.system_period == "After update"
        urgent = request.urgency == "Urgent"
        legacy = request.source_system == "ProcureFlow Classic"
        actor_location = employee_lookup.loc[request.employee_id].location

        # Rejected requests still pass through a short routing sequence.
        if request.final_status == "Rejected":
            planned = [x for x in planned if x not in {"Purchase Order Created", "Payment Authorized"}]
            if "Rejected" not in planned:
                planned.append("Rejected")
        elif request.final_status == "Cancelled":
            planned = ["Request Submitted", "Cancelled"]

        def drop(step: str, probability: float) -> None:
            nonlocal planned
            if step in planned and rng.random() < probability:
                planned = [x for x in planned if x != step]

        drop("Manager Approval", 0.008)
        drop("Finance Approval", 0.025 + (0.07 if urgent else 0))
        drop("Director Approval", 0.035 + (0.08 if actor_location == "Austin" and post else 0))
        drop("Legal Review", 0.045)

        # The July system change improves vendor-control enforcement.
        vendor_skip = 0.15 if not post else (0.11 if legacy else 0.025)
        drop("Vendor Validation", vendor_skip)

        # Fast-track routing creates an unintended urgent Procurement bypass.
        procurement_skip = 0.06
        if request.department_name == "Field Operations":
            procurement_skip += 0.13
        if post and urgent and not legacy:
            procurement_skip += 0.23
        drop("Procurement Review", procurement_skip)

        security_skip = 0.045
        if request.department_name == "Engineering" and request.purchase_type in {"Software", "AI Services"}:
            security_skip += 0.22
        if request.purchase_type == "AI Services" and post:
            security_skip += 0.08
        drop("Security Review", security_skip)

        # Austin remains on the pre-update travel threshold in its legacy app.
        if post and actor_location == "Austin" and legacy and request.purchase_type == "Travel" and 5_000 < request.amount <= 7_500:
            drop("Finance Approval", 0.82)

        # High-value bids may be replaced by a governed exception.
        use_exception = request.amount > 20_000 and rng.random() < (0.25 if request.department_name == "Marketing" else 0.10)
        if use_exception and "Competitive Bid Confirmed" in planned:
            planned = ["Exception Approved" if x == "Competitive Bid Confirmed" else x for x in planned]
            request.exception_documented = bool(rng.random() < (0.58 if request.department_name == "Marketing" else 0.90))
        else:
            drop("Competitive Bid Confirmed", 0.07)

        # Rework is concentrated in contractors and Marketing intake quality.
        rework_probability = 0.035 + (0.09 if request.purchase_type == "Contractor" else 0) + (0.07 if request.department_name == "Marketing" else 0)
        if len(planned) > 2 and rng.random() < rework_probability:
            insert_at = min(2, len(planned) - 1)
            planned[insert_at:insert_at] = ["Returned for Revision", "Request Resubmitted"]

        # A small sequence defect is magnified in post-update urgent routing.
        if "Purchase Order Created" in planned and "Payment Authorized" in planned:
            bad_order_probability = 0.006 + (0.055 if post and urgent and not legacy else 0)
            if rng.random() < bad_order_probability:
                po_index = planned.index("Purchase Order Created")
                pay_index = planned.index("Payment Authorized")
                planned[po_index], planned[pay_index] = planned[pay_index], planned[po_index]

        self_approve = rng.random() < (0.045 if request.business_unit == "Revenue" else 0.005)
        violate_limit = rng.random() < 0.018
        timestamp = pd.Timestamp(request.request_date)
        previous_status = "Draft"
        for activity in planned:
            actor, role = _event_actor(
                rng, activity, request, employee_lookup, department_pools, managers,
                violate_limit=violate_limit and activity == "Manager Approval",
                self_approve=self_approve and activity == "Manager Approval",
            )
            elapsed = max(0.08, float(rng.gamma(1.7, 7.5)))
            if activity in {"Security Review", "Legal Review"}:
                elapsed *= 1.5
            if activity == "Returned for Revision":
                elapsed *= 1.8
            timestamp += pd.Timedelta(hours=elapsed)
            status_map = {
                "Request Submitted": "Submitted", "Request Resubmitted": "Resubmitted",
                "Manager Approval": "Manager Approved", "Director Approval": "Director Approved",
                "Procurement Review": "Procurement Reviewed", "Finance Approval": "Finance Approved",
                "Security Review": "Security Reviewed", "Legal Review": "Legal Reviewed",
                "Vendor Validation": "Vendor Validated", "Competitive Bid Confirmed": "Bid Confirmed",
                "Purchase Order Created": "PO Created", "Payment Authorized": "Paid",
                "Returned for Revision": "Revision Required", "Exception Approved": "Exception Approved",
                "Rejected": "Rejected", "Cancelled": "Cancelled",
            }
            new_status = status_map.get(activity, activity)
            events.append({
                "event_id": f"EVT-{event_number:07d}",
                "request_id": request.request_id,
                "event_timestamp": timestamp,
                "activity": activity,
                "performed_by": actor,
                "performer_role": role,
                "system": request.source_system,
                "previous_status": previous_status,
                "new_status": new_status,
            })
            event_number += 1
            previous_status = new_status
    return pd.DataFrame(events)


def generate(output_dir: Path = RAW_DIR, request_count: int = 8_500) -> dict[str, pd.DataFrame]:
    """Generate and persist every raw source table."""

    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    departments = _departments()
    employees = _employees(rng, departments)
    vendors = _vendors(rng)
    requests = _requests(rng, departments, employees, vendors, request_count)
    events = _events(rng, requests, employees, vendors, departments)
    rules = catalog_frame()
    datasets = {
        "departments": departments,
        "employees": employees,
        "vendors": vendors,
        "purchase_requests": requests,
        "event_log": events,
        "business_rules": rules,
    }
    for name, frame in datasets.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    return datasets


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TraceGap synthetic enterprise data")
    parser.add_argument("--requests", type=int, default=8_500, help="Number of purchase requests")
    args = parser.parse_args()
    datasets = generate(request_count=args.requests)
    print(f"Generated {len(datasets['purchase_requests']):,} purchase requests and {len(datasets['event_log']):,} workflow events.")


if __name__ == "__main__":
    main()
