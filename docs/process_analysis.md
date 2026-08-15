# Purchase-to-Pay Process Analysis

## Central analytical model

TraceGap treats policy and system behavior as two independently testable representations:

```mermaid
flowchart LR
    A["Expected process<br/>Policy + business rules"] --> C["Conformance comparison"]
    B["Observed process<br/>Timestamped system events"] --> C
    C --> D["Rule violations"]
    C --> E["Process Drift Score"]
    C --> F["Change and root-cause analysis"]
```

The expected path is constructed from request amount, category, vendor approval and risk, contract attributes, urgency, and effective date. The observed path is reconstructed by ordering every event for the request. A difference becomes a finding only when reusable logic can identify it and retain the rule and evidence that explain the result.

## AS-IS workflow

```mermaid
flowchart TD
    A["Employee submits request"] --> B{"Amount at least $1K?"}
    B -- Yes --> C["Manager approval"]
    B -- No --> H{"Special controls apply?"}
    C --> D{"Above local limit?"}
    D -- Yes --> E["Director approval"]
    D -- No --> H
    E --> H
    H --> I{"Vendor / category / contract checks"}
    I -->|"Unapproved vendor or contractor"| J["Procurement review"]
    I -->|"Software, AI, or high-risk technology"| K["Security review"]
    I -->|"High-value contract or international high risk"| L["Legal review"]
    I -->|"High value"| M["Bid evidence or exception"]
    J --> N{"Finance approval required?"}
    K --> N
    L --> N
    M --> N
    H --> N
    N -- Yes --> O["Finance approval"]
    N -- No --> P["Purchase order created"]
    O --> P
    P --> Q["Payment authorized"]

    X["Manual exception email"] -. "sometimes outside event log" .-> M
    Y["ProcureFlow Classic"] -. "legacy threshold/configuration" .-> N
    Z["NovaProcure urgent route"] -. "may bypass Procurement rejoin" .-> P
```

### AS-IS observations

- **Manual exceptions:** exception rationale may exist in email or attachments, while the event log only confirms that an exception activity occurred.
- **System limitation:** the legacy application does not consistently enforce Vendor Validation and continues to apply the former travel threshold in part of Austin.
- **Policy/system mismatch:** effective-dated policy can change independently of application configuration.
- **Approval bottleneck:** Legal and Security reviews add longer average inter-event time than routine routing.
- **Inconsistent enforcement:** Engineering technology intake, Marketing bid exceptions, Field Operations Procurement routing, and Revenue approval delegation show different drift patterns.
- **Release side effect:** the July update reduces Vendor Validation violations but increases Procurement-related violations for urgent work.

## TO-BE workflow

```mermaid
flowchart TD
    A["Employee enters purchase facts"] --> B["Dynamic rule evaluation"]
    B --> C["Show required approvals, evidence, and expected SLA"]
    C --> D{"Submission complete?"}
    D -- No --> E["Return precise validation message"]
    E --> A
    D -- Yes --> F["Create immutable request + policy version"]
    F --> G["Automatic parallel/sequential routing"]
    G --> H["Validate requester / approver separation"]
    H --> I["Validate approval limit in real time"]
    I --> J{"Exception requested?"}
    J -- Yes --> K["Require reason, evidence, owner, expiry"]
    J -- No --> L["Complete mandatory control gates"]
    K --> L
    L --> M{"Every required control complete?"}
    M -- No --> N["Block PO/payment and alert owner"]
    N --> G
    M -- Yes --> O["Create purchase order"]
    O --> P["Authorize payment"]
    P --> Q["Continuous conformance monitoring"]
    Q --> R["Drift alert + accountable queue"]
    Q --> S["Release and policy-effectiveness reporting"]
```

## AS-IS vs TO-BE

| Dimension | AS-IS | TO-BE |
|---|---|---|
| Rule evaluation | Distributed across policy, local practice, and application configuration | Versioned central rule service evaluates facts at submission |
| Routing | Mixed manual and application-specific branches | Generated from applicable controls with explicit joins after fast-track paths |
| Approval limits | Can be checked after approval or not at all | Real-time authorization check before approval is accepted |
| Segregation of duties | Delegated groups may allow requester overlap | Identity validation blocks requester self-approval |
| Effective dates | Policy and application changes can diverge | Policy version and effective date stored with each request |
| Exceptions | Rationale quality varies and may live outside the workflow | Structured reason, evidence, owner, expiry, and reporting |
| Downstream enforcement | PO/payment can occur with incomplete controls | Mandatory gate blocks PO and payment until controls are complete |
| Monitoring | Periodic sampling and retrospective analysis | Continuous conformance metrics and accountable drift queue |
| Change validation | Overall adoption metrics | Rule-, route-, office-, and application-level regression checks |

## Process Drift Score

The score is an explainable prioritization aid, not a prediction or machine-learning output.

| Component | Calculation | Maximum |
|---|---|---:|
| Rule violations | Low 4, Medium 8, High 14, Critical 22 points per violation | 65 |
| Ordering anomalies | 12 points per detected sequence issue | 20 |
| Rework | 5 points per return-for-revision loop | 10 |
| Exceptions | 3 points per exception event | 6 |
| Rare path | 4 points when path frequency is at or below the rarity threshold | 4 |
| Final score | Sum of components, capped | 100 |

The score does not state that a high-drift request is fraudulent or harmful. It ranks requests by observable deviation so a person can review the evidence.

## Temporal system change

NovaProcure went live on July 1, 2025. Synthetic behavior models two linked effects:

1. A required vendor gate improves Vendor Validation compliance.
2. An urgent fast-track route can fail to rejoin the mandatory Procurement branch.

Legacy traffic remains disproportionately visible in Austin, where a subset of travel requests still follows the former $7,500 Finance threshold instead of the new $5,000 threshold. TraceGap separates policy design, application behavior, and office adoption so an overall post-release metric cannot hide those differences.

## System architecture

```mermaid
flowchart LR
    A["Synthetic enterprise data<br/>6 connected source tables"] --> B["Data processing<br/>deterministic pipeline"]
    B --> C[("SQLite<br/>relational model")]
    C --> D["Process reconstruction engine"]
    C --> E["Business rule engine"]
    D --> F["Drift scoring"]
    E --> F
    C --> G["SQL / Python analytics"]
    F --> H["Streamlit application"]
    G --> H
    H --> I["Decision support<br/>investigate · prioritize · simulate"]
```

## Entity-relationship model

```mermaid
erDiagram
    DEPARTMENTS ||--o{ EMPLOYEES : contains
    DEPARTMENTS ||--o{ PURCHASE_REQUESTS : owns
    EMPLOYEES ||--o{ PURCHASE_REQUESTS : submits
    VENDORS ||--o{ PURCHASE_REQUESTS : receives
    PURCHASE_REQUESTS ||--o{ WORKFLOW_EVENTS : generates
    EMPLOYEES ||--o{ WORKFLOW_EVENTS : performs
    PURCHASE_REQUESTS ||--|| PROCESS_INSTANCES : reconstructs
    PURCHASE_REQUESTS ||--o{ RULE_VIOLATIONS : has
    BUSINESS_RULES ||--o{ RULE_VIOLATIONS : explains
    EMPLOYEES ||--o{ THRESHOLD_PATTERNS : associated_with
    VENDORS ||--o{ THRESHOLD_PATTERNS : associated_with

    DEPARTMENTS {
        string department_id PK
        string department_name
        string business_unit
        decimal budget
    }
    EMPLOYEES {
        string employee_id PK
        string department_id FK
        string manager_id
        decimal approval_limit
        string location
    }
    VENDORS {
        string vendor_id PK
        boolean approved_vendor
        string risk_level
        string country
    }
    PURCHASE_REQUESTS {
        string request_id PK
        string employee_id FK
        string department_id FK
        string vendor_id FK
        datetime request_date
        decimal amount
        string purchase_type
    }
    WORKFLOW_EVENTS {
        string event_id PK
        string request_id FK
        datetime event_timestamp
        string activity
        string performed_by FK
    }
    PROCESS_INSTANCES {
        string request_id PK
        string expected_path
        string observed_path
        integer drift_score
        boolean aligned
    }
    BUSINESS_RULES {
        string rule_id PK
        string condition
        string required_step
        string severity
    }
    RULE_VIOLATIONS {
        string violation_id PK
        string request_id FK
        string rule_id FK
        string evidence
    }
    THRESHOLD_PATTERNS {
        string pattern_id PK
        string employee_id FK
        string vendor_id FK
        decimal combined_value
    }
```

## Analysis limitations

- The event log shows what the synthetic applications recorded, not off-system communication or attachment quality.
- Parallel approvals are represented in a linear timestamp sequence for interpretability.
- Rule applicability is tailored to this case study and would require policy-owner validation in a real organization.
- Root-cause statements are hypotheses; workshops, configuration review, and user research would be required to confirm them.

