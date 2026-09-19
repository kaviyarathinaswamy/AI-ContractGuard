from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from datetime import datetime


app = Flask(__name__)
CORS(app)


# ==================================================
# RETENTION EXTRACTION
# ==================================================

def find_retention(text):

    patterns = [
        r"(\d+)\s*years?",
        r"(\d+)\s*year"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return int(match.group(1))

    return None


# ==================================================
# TEXT HELPERS
# ==================================================

def contains_any(text, keywords):

    text = text.lower()

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


def extract_sentence(text, keywords):

    sentences = re.split(
        r'(?<=[.!?])\s+',
        text.replace("\n", " ")
    )

    for sentence in sentences:

        if contains_any(sentence, keywords):

            return sentence.strip()

    return None


# ==================================================
# OFFICIAL SOURCE VERIFICATION
# ==================================================

def verify_official_source(regulation_text):

    text = regulation_text.lower()

    government_indicators = [
        "government",
        "official regulation",
        "ministry",
        "act",
        "gazette",
        "regulatory authority",
        "government of india",
        "meity",
        "mca",
        "rbi",
        "sebi",
        "india code"
    ]

    found_indicator = any(
        word in text
        for word in government_indicators
    )

    checked_time = datetime.now().strftime(
        "%d %b %Y, %I:%M %p"
    )

    if found_indicator:

        return {

            "status":
                "SOURCE IDENTIFIED — VERIFICATION REQUIRED",

            "message":
                "The regulation document contains an official-source indicator, "
                "but external government-source verification has not been completed.",

            "source":
                "Government / Regulatory Source Indicated",

            "document_status":
                "MANUAL VERIFICATION REQUIRED",

            "last_checked":
                checked_time,

            "note":
                "Do not treat this document as officially verified until the "
                "corresponding government source is independently confirmed."

        }

    return {

        "status":
            "OFFICIAL SOURCE NOT VERIFIED",

        "message":
            "No reliable official-source indicator was identified in the uploaded regulation.",

        "source":
            "Not identified",

        "document_status":
            "MANUAL VERIFICATION REQUIRED",

        "last_checked":
            checked_time,

        "note":
            "Verify the regulation against the applicable official government source."

    }


# ==================================================
# COMPLIANCE RULE DEFINITIONS
# ==================================================

COMPLIANCE_RULES = {

    "consent": {
        "keywords": [
            "consent",
            "acceptance",
            "permission"
        ]
    },

    "withdrawal": {
        "keywords": [
            "withdraw consent",
            "withdrawal of consent",
            "withdrawal",
            "withdraw"
        ]
    },

    "third_party_sharing": {
        "keywords": [
            "third-party",
            "third party",
            "third parties",
            "affiliated",
            "service providers",
            "share personal data",
            "data sharing"
        ]
    },

    "purpose_limitation": {
        "keywords": [
            "specified purpose",
            "specific purpose",
            "purpose limitation",
            "unrelated purposes",
            "additional business purposes",
            "analytics and marketing"
        ]
    },

    "data_processing": {
        "keywords": [
            "process personal data",
            "processing personal data",
            "personal data",
            "data processing"
        ]
    }
}


# ==================================================
# ANALYZE COMPLIANCE RULE
# ==================================================

def analyze_compliance_rule(
    rule_name,
    contract,
    policy,
    regulation
):

    rule = COMPLIANCE_RULES[rule_name]

    keywords = rule["keywords"]

    contract_evidence = extract_sentence(
        contract,
        keywords
    )

    policy_evidence = extract_sentence(
        policy,
        keywords
    )

    regulation_evidence = extract_sentence(
        regulation,
        keywords
    )

    evidence_items = []

    if contract_evidence:

        evidence_items.append(
            "Contract: " + contract_evidence
        )

    if policy_evidence:

        evidence_items.append(
            "Company Policy: " + policy_evidence
        )

    if regulation_evidence:

        evidence_items.append(
            "Regulation: " + regulation_evidence
        )

    # We need at least two documents to establish
    # a meaningful comparison.

    if len(evidence_items) < 2:

        return None

    # ------------------------------------------------
    # RULE-SPECIFIC CONFLICT DETECTION
    # ------------------------------------------------

    conflict = False

    description = ""

    action = ""

    severity = "MEDIUM"

    # -----------------------------------------------
    # CONSENT
    # -----------------------------------------------

    if rule_name == "consent":

        contract_broad = contains_any(
            contract,
            [
                "continuing consent",
                "future analytics",
                "future marketing",
                "all future"
            ]
        )

        policy_restrictive = contains_any(
            policy,
            [
                "specified",
                "clearly communicated",
                "appropriate"
            ]
        )

        regulation_restrictive = contains_any(
            regulation,
            [
                "specific",
                "informed",
                "unambiguous",
                "withdraw"
            ]
        )

        if contract_broad and (
            policy_restrictive or regulation_restrictive
        ):

            conflict = True
            severity = "HIGH"

            description = (
                "The contract contains a broad continuing-consent "
                "clause while the policy/regulatory requirement "
                "requires more specific consent conditions."
            )

            action = (
                "Review and revise the contract consent clause."
            )

    # -----------------------------------------------
    # WITHDRAWAL
    # -----------------------------------------------

    elif rule_name == "withdrawal":

        contract_continues = contains_any(
            contract,
            [
                "continue processing",
                "continue processing the customer's",
                "up to 12 months",
                "after withdrawal"
            ]
        )

        policy_requires_withdrawal = contains_any(
            policy,
            [
                "effective mechanism",
                "withdrawal of consent",
                "handle subsequent processing"
            ]
        )

        regulation_allows_withdrawal = contains_any(
            regulation,
            [
                "withdraw consent",
                "withdrawal",
                "data principal"
            ]
        )

        if contract_continues and (
            policy_requires_withdrawal
            or regulation_allows_withdrawal
        ):

            conflict = True
            severity = "HIGH"

            description = (
                "The contract permits continued processing after "
                "consent withdrawal, while the policy/regulatory "
                "documents require withdrawal to be respected "
                "where applicable."
            )

            action = (
                "Review the post-withdrawal processing clause "
                "with the Compliance Team."
            )

    # -----------------------------------------------
    # THIRD PARTY SHARING
    # -----------------------------------------------

    elif rule_name == "third_party_sharing":

        contract_allows = contains_any(
            contract,
            [
                "without obtaining separate consent",
                "without separate consent",
                "share collected personal data",
                "share personal data"
            ]
        )

        policy_restricts = contains_any(
            policy,
            [
                "shall not be shared",
                "required consent",
                "lawful basis"
            ]
        )

        if contract_allows and policy_restricts:

            conflict = True
            severity = "HIGH"

            description = (
                "The contract permits third-party data sharing "
                "without separate consent, while the company policy "
                "requires consent or another applicable lawful basis."
            )

            action = (
                "Review the vendor data-sharing clause and "
                "confirm the required lawful basis."
            )

    # -----------------------------------------------
    # PURPOSE LIMITATION
    # -----------------------------------------------

    elif rule_name == "purpose_limitation":

        contract_broad = contains_any(
            contract,
            [
                "additional business purposes",
                "reasonably related",
                "future analytics",
                "marketing"
            ]
        )

        policy_restrictive = contains_any(
            policy,
            [
                "specified purpose",
                "unrelated purposes",
                "appropriate legal basis"
            ]
        )

        if contract_broad and policy_restrictive:

            conflict = True
            severity = "MEDIUM"

            description = (
                "The contract permits broader additional uses of "
                "personal data than the purpose restrictions stated "
                "in the company policy."
            )

            action = (
                "Review the permitted purposes and align the "
                "contract with the company's purpose limitation policy."
            )

    # -----------------------------------------------
    # DATA PROCESSING
    # -----------------------------------------------

    elif rule_name == "data_processing":

        if (
            contract_evidence
            and policy_evidence
            and regulation_evidence
        ):

            # Presence of processing requirements across all
            # three documents is useful evidence, but not
            # automatically a conflict.

            conflict = False

    if not conflict:

        return {
            "rule": rule_name,
            "conflict": False,
            "severity": "LOW",
            "evidence": evidence_items,
            "description":
                "The relevant requirement was identified across "
                "the uploaded documents, but no direct conflict "
                "was detected by the current rule set.",
            "action":
                "Continue compliance monitoring."
        }

    return {

        "rule":
            rule_name,

        "conflict":
            True,

        "severity":
            severity,

        "evidence":
            evidence_items,

        "description":
            description,

        "action":
            action
    }


# ==================================================
# ANALYZE
# ==================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    data = request.get_json(
        silent=True
    ) or {}

    contract = data.get(
        "contract",
        ""
    )

    policy = data.get(
        "policy",
        ""
    )

    regulation = data.get(
        "regulation",
        ""
    )

    # ------------------------------------------------
    # RETENTION
    # ------------------------------------------------

    contract_years = find_retention(
        contract
    )

    policy_years = find_retention(
        policy
    )

    regulation_years = find_retention(
        regulation
    )

    conflicts = []

    evidence = []

    actions = []

    # ==================================================
    # OLD RETENTION LOGIC
    # ==================================================

    if (
        contract_years is not None
        and policy_years is not None
        and regulation_years is not None
    ):

        retention_evidence = [

            f"Contract requires {contract_years} years retention.",

            f"Company Policy requires {policy_years} years retention.",

            f"Regulation requires {regulation_years} years retention."

        ]

        evidence.extend(
            retention_evidence
        )

        if (
            contract_years != policy_years
            or contract_years != regulation_years
        ):

            conflicts.append({

                "type":
                    "Data Retention Conflict",

                "severity":
                    "HIGH",

                "description":
                    "The contract retention period does not align "
                    "with the company policy and applicable regulation."

            })

            actions.extend([

                "Review the contract retention clause.",

                "Align the contract with the applicable policy and regulation.",

                "Escalate the conflict to the Compliance Team."

            ])

    # ==================================================
    # NEW COMPLIANCE RULE ENGINE
    # ==================================================

    rule_results = []

    for rule_name in COMPLIANCE_RULES:

        result = analyze_compliance_rule(
            rule_name,
            contract,
            policy,
            regulation
        )

        if result:

            rule_results.append(
                result
            )

            if result["conflict"]:

                conflicts.append({

                    "type":
                        result["rule"].replace(
                            "_",
                            " "
                        ).title() + " Conflict",

                    "severity":
                        result["severity"],

                    "description":
                        result["description"]

                })

                actions.append(
                    result["action"]
                )

                evidence.extend(
                    result["evidence"]
                )

    # ==================================================
    # REMOVE DUPLICATE EVIDENCE
    # ==================================================

    evidence = list(
        dict.fromkeys(evidence)
    )

    actions = list(
        dict.fromkeys(actions)
    )

    # ==================================================
    # RISK CALCULATION
    # ==================================================

    high_conflicts = sum(
        1
        for c in conflicts
        if c["severity"] == "HIGH"
    )

    medium_conflicts = sum(
        1
        for c in conflicts
        if c["severity"] == "MEDIUM"
    )

    if high_conflicts >= 2:

        risk_score = 95
        severity = "HIGH"

    elif high_conflicts == 1:

        risk_score = 90
        severity = "HIGH"

    elif medium_conflicts >= 2:

        risk_score = 70
        severity = "MEDIUM"

    elif medium_conflicts == 1:

        risk_score = 60
        severity = "MEDIUM"

    elif (
        contract_years is None
        or policy_years is None
        or regulation_years is None
    ) and not rule_results:

        risk_score = 40
        severity = "MEDIUM"

        conflicts.append({

            "type":
                "Missing Information",

            "severity":
                "MEDIUM",

            "description":
                "The system could not identify sufficient "
                "compliance information in the uploaded documents."

        })

        actions.extend([

            "Review the documents manually.",

            "Verify the applicable compliance requirement."

        ])

    else:

        risk_score = 5
        severity = "LOW"

    # ==================================================
    # RISK DESCRIPTION
    # ==================================================

    if conflicts:

        risk_description = (
            f"{len(conflicts)} compliance issue(s) detected "
            "across the analyzed documents."
        )

    else:

        risk_description = (
            "No direct compliance conflict was detected "
            "across the analyzed documents."
        )

    # ==================================================
    # FALLBACK ACTION
    # ==================================================

    if not actions:

        actions = [

            "Continue monitoring compliance.",

            "Maintain an audit record of the reviewed documents."

        ]

    # ==================================================
    # OFFICIAL SOURCE VERIFICATION
    # ==================================================

    verification = verify_official_source(
        regulation
    )

    # ==================================================
    # RESPONSE
    # ==================================================

    return jsonify({

        "status":
            "success",

        "risk_score":
            risk_score,

        "severity":
            severity,

        "risk_description":
            risk_description,

        "conflicts":
            conflicts,

        "recommended_actions":
            actions,

        "evidence":
            evidence,

        "retention": {

            "contract":
                contract_years,

            "policy":
                policy_years,

            "regulation":
                regulation_years

        },

        "verification":
            verification

    })


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():

    return "AI ContractGuard Backend is Running!"


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )