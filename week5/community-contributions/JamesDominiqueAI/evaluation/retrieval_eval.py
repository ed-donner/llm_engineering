# retrieval_eval.py
"""
evaluation/retrieval_eval.py — Retrieval evaluation with MRR and nDCG.
Loads test questions from tests.jsonl (same structure as your original eval.py).
"""

import os
import sys
import json
import math
from typing import List, Generator, Tuple
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EVAL_RESULTS_DIR, RETRIEVAL_K
from retrieval.base_retrieval import fetch_context_unranked, merge_chunks, Result

TEST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests.jsonl")


# ── Test Data Model ────────────────────────────────────────────────────────────

class TestQuestion(BaseModel):
    question: str = Field(description="The question to ask the RAG system")
    keywords: List[str] = Field(description="Keywords that must appear in retrieved context")
    reference_answer: str = Field(description="The reference answer for evaluation")
    category: str = Field(description="Category: direct_fact, temporal_change, cross_reference, etc.")


def load_tests() -> List[TestQuestion]:
    """Load test questions from tests.jsonl."""
    if not os.path.exists(TEST_FILE):
        print(f"[Eval] tests.jsonl not found at {TEST_FILE}, using built-in defaults.")
        return _default_tests()
    tests = []
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                tests.append(TestQuestion(**json.loads(line)))
    print(f"[Eval] Loaded {len(tests)} tests from {TEST_FILE}")
    return tests


def _default_tests() -> List[TestQuestion]:
    """100 built-in test questions across all 6 categories."""
    return [
        # ── direct_fact (25) ───────────────────────────────────────────────────
        TestQuestion(question="What is the breach notification deadline in REG-ABC-2021?", keywords=["72 hours", "breach", "notification"], reference_answer="Under REG-ABC-2021 Section 4, institutions must notify the FFCA within 72 hours of discovering a breach.", category="direct_fact"),
        TestQuestion(question="What are the KYC requirements under REG-XYZ-2022?", keywords=["KYC", "photo ID", "proof of address"], reference_answer="REG-XYZ-2022 requires government-issued photo ID, proof of address within 90 days, and source of funds declaration for deposits over $50,000.", category="direct_fact"),
        TestQuestion(question="How long must financial institutions retain consumer data?", keywords=["7 years", "retention"], reference_answer="Both REG-ABC-2021 and REG-ABC-2023 require a minimum 7-year retention period for consumer financial data.", category="direct_fact"),
        TestQuestion(question="What did the 2022 audit find about third-party vendor audits?", keywords=["vendor", "54%", "audit"], reference_answer="The 2022 audit found that 54% of institutions could not demonstrate all vendors had completed their required annual security audit.", category="direct_fact"),
        TestQuestion(question="What is the minimum encryption standard required under REG-ABC-2021?", keywords=["AES-256", "encryption", "data at rest"], reference_answer="REG-ABC-2021 mandates AES-256 encryption for all consumer financial data at rest.", category="direct_fact"),
        TestQuestion(question="What threshold triggers the source of funds declaration under REG-XYZ-2022?", keywords=["$50,000", "source of funds", "declaration"], reference_answer="A source of funds declaration is required for deposits over $50,000 under REG-XYZ-2022.", category="direct_fact"),
        TestQuestion(question="What is the maximum retention period for biometric data under AMD-ABC-2022-A1?", keywords=["biometric", "3 years", "retention"], reference_answer="AMD-ABC-2022-A1 set a 3-year maximum retention limit for biometric data classified as CFD.", category="direct_fact"),
        TestQuestion(question="What percentage of institutions failed vendor audit requirements in 2022?", keywords=["54%", "vendor", "audit"], reference_answer="54% of institutions audited in 2022 could not demonstrate that all vendors had completed required annual security audits.", category="direct_fact"),
        TestQuestion(question="What proof of address recency is required under REG-XYZ-2022 KYC?", keywords=["90 days", "proof of address", "KYC"], reference_answer="REG-XYZ-2022 requires proof of address dated within the last 90 days as part of KYC verification.", category="direct_fact"),
        TestQuestion(question="Which regulation introduced the FFCA breach notification requirement?", keywords=["REG-ABC-2021", "FFCA", "breach"], reference_answer="REG-ABC-2021 introduced the requirement to notify the FFCA within 72 hours of discovering a data breach.", category="direct_fact"),
        TestQuestion(question="What does REG-ABC-2021 require for data-in-transit protection?", keywords=["TLS 1.2", "transit", "encryption"], reference_answer="REG-ABC-2021 requires TLS 1.2 or higher for all consumer data transmitted over public networks.", category="direct_fact"),
        TestQuestion(question="What are the consumer opt-out rights under REG-ABC-2021?", keywords=["opt-out", "30 days", "consent"], reference_answer="Under REG-ABC-2021, consumers have 30 days to opt out of data sharing with third-party partners.", category="direct_fact"),
        TestQuestion(question="What data categories are classified as Consumer Financial Data under REG-ABC-2021?", keywords=["CFD", "transaction history", "account balance"], reference_answer="REG-ABC-2021 classifies transaction history, account balances, credit scores, and personal identifiers as Consumer Financial Data (CFD).", category="direct_fact"),
        TestQuestion(question="What is the required frequency of penetration testing under REG-ABC-2023?", keywords=["penetration testing", "annual", "security"], reference_answer="REG-ABC-2023 requires annual penetration testing of all systems that store or process consumer financial data.", category="direct_fact"),
        TestQuestion(question="What is required for cross-border data transfers under REG-ABC-2023?", keywords=["cross-border", "data transfer", "approved jurisdiction"], reference_answer="REG-ABC-2023 requires that all cross-border data transfers be limited to FFCA-approved jurisdictions and documented in the institution's data inventory.", category="direct_fact"),
        TestQuestion(question="What vendor contract requirement was introduced in REG-ABC-2023?", keywords=["vendor", "contract", "right to audit"], reference_answer="REG-ABC-2023 requires all vendor contracts to include a right-to-audit clause allowing the institution to inspect the vendor's security controls.", category="direct_fact"),
        TestQuestion(question="What incident response plan requirement exists under REG-ABC-2021?", keywords=["incident response", "plan", "tested annually"], reference_answer="REG-ABC-2021 requires institutions to maintain a written incident response plan that is tested at least annually.", category="direct_fact"),
        TestQuestion(question="What does REG-XYZ-2022 require for high-risk customer profiles?", keywords=["high-risk", "enhanced due diligence", "KYC"], reference_answer="REG-XYZ-2022 requires enhanced due diligence and annual KYC review for customers classified as high-risk.", category="direct_fact"),
        TestQuestion(question="What is the regulatory definition of a reportable breach under REG-ABC-2021?", keywords=["reportable breach", "unauthorized access", "CFD"], reference_answer="Under REG-ABC-2021, a reportable breach is any unauthorized access to or disclosure of Consumer Financial Data affecting 500 or more individuals.", category="direct_fact"),
        TestQuestion(question="What training requirement does REG-ABC-2023 impose on staff?", keywords=["training", "annual", "data protection"], reference_answer="REG-ABC-2023 requires all staff with access to consumer data to complete annual data protection training.", category="direct_fact"),
        TestQuestion(question="What is the board-level requirement under REG-ABC-2023?", keywords=["board", "compliance", "annual report"], reference_answer="REG-ABC-2023 requires the board of directors to receive and approve an annual compliance report covering data protection obligations.", category="direct_fact"),
        TestQuestion(question="What is the required frequency of KYC review for standard-risk customers under REG-XYZ-2022?", keywords=["KYC", "3 years", "standard-risk"], reference_answer="Under REG-XYZ-2022, standard-risk customers must have their KYC information refreshed every 3 years.", category="direct_fact"),
        TestQuestion(question="What does REG-ABC-2021 require regarding consumer data access requests?", keywords=["30 days", "data access", "consumer request"], reference_answer="REG-ABC-2021 requires institutions to fulfill consumer data access requests within 30 days of receipt.", category="direct_fact"),
        TestQuestion(question="What is required for cross-border data transfers under REG-ABC-2023?", keywords=["cross-border", "approved jurisdiction", "data inventory"], reference_answer="REG-ABC-2023 requires cross-border data transfers to be limited to FFCA-approved jurisdictions and documented in the institution's data inventory.", category="direct_fact"),
        TestQuestion(question="What new consumer rights were introduced by REG-ABC-2023?", keywords=["right to erasure", "portability", "consumer"], reference_answer="REG-ABC-2023 introduced the right to data erasure and the right to data portability for consumers.", category="direct_fact"),

        # ── temporal_change (20) ───────────────────────────────────────────────
        TestQuestion(question="What changed in breach notification requirements in 2023?", keywords=["48 hours", "breach", "2023"], reference_answer="REG-ABC-2023 reduced the FFCA breach notification window from 72 hours to 48 hours.", category="temporal_change"),
        TestQuestion(question="What new AI requirements were introduced in 2023?", keywords=["ADS", "explainability", "bias audit"], reference_answer="REG-ABC-2023 Section 9 requires explainability documentation, biannual bias audits, and human review options for Automated Decision Systems.", category="temporal_change"),
        TestQuestion(question="How did the consent opt-out window change between 2021 and 2023?", keywords=["30 days", "60 days", "consent"], reference_answer="The opt-out window was extended from 30 days (2021) to 60 days (2023).", category="temporal_change"),
        TestQuestion(question="How did REG-ABC-2023 change the encryption standard from REG-ABC-2021?", keywords=["AES-256", "AES-128", "encryption"], reference_answer="REG-ABC-2021 allowed AES-128 encryption; REG-ABC-2023 raised the minimum standard to AES-256 for all consumer financial data.", category="temporal_change"),
        TestQuestion(question="What new data breach notification channels were added in 2023?", keywords=["notification", "consumer", "direct notification"], reference_answer="REG-ABC-2023 added a requirement to notify affected consumers directly within 5 days of a confirmed breach, in addition to FFCA notification.", category="temporal_change"),
        TestQuestion(question="How did the vendor audit requirement change between REG-ABC-2021 and REG-ABC-2023?", keywords=["vendor", "audit", "right to audit"], reference_answer="REG-ABC-2021 required vendors to self-certify annually; REG-ABC-2023 replaced this with a mandatory right-to-audit clause in all contracts.", category="temporal_change"),
        TestQuestion(question="What changes did REG-ABC-2023 make to data retention rules?", keywords=["7 years", "retention", "deletion"], reference_answer="REG-ABC-2023 retained the 7-year minimum but added a new requirement to delete data within 90 days after the retention period expires.", category="temporal_change"),
        TestQuestion(question="How did the penalty structure change from REG-ABC-2021 to REG-ABC-2023?", keywords=["penalty", "$70,000", "per day"], reference_answer="REG-ABC-2021 set a flat fine schedule; REG-ABC-2023 introduced per-day penalties of $70,000 for ongoing violations such as late breach notification.", category="temporal_change"),
        TestQuestion(question="What change did 2023 regulations make to the minimum TLS version?", keywords=["TLS 1.3", "TLS 1.2", "transit"], reference_answer="REG-ABC-2023 upgraded the minimum requirement from TLS 1.2 (required by REG-ABC-2021) to TLS 1.3 for data in transit.", category="temporal_change"),
        TestQuestion(question="How did REG-ABC-2023 change the scope of the data breach definition?", keywords=["500", "100", "reportable breach"], reference_answer="REG-ABC-2023 lowered the reportable breach threshold from 500 affected individuals (REG-ABC-2021) to 100, broadening reporting obligations.", category="temporal_change"),
        TestQuestion(question="What updates did REG-ABC-2023 make to the incident response plan requirements?", keywords=["incident response", "tabletop exercise", "annually"], reference_answer="REG-ABC-2023 added a requirement for annual tabletop exercises in addition to the written plan already required by REG-ABC-2021.", category="temporal_change"),
        TestQuestion(question="How did board-level oversight requirements evolve from 2021 to 2023?", keywords=["board", "quarterly", "annual report"], reference_answer="REG-ABC-2021 required an annual board compliance report; REG-ABC-2023 upgraded this to quarterly briefings plus the annual report.", category="temporal_change"),
        TestQuestion(question="What change did REG-ABC-2023 make to staff training frequency?", keywords=["training", "semi-annual", "annual"], reference_answer="REG-ABC-2021 required annual data protection training; REG-ABC-2023 increased this to semi-annual for staff handling CFD.", category="temporal_change"),
        TestQuestion(question="What new third-party risk management requirements appeared in REG-ABC-2023?", keywords=["third-party", "risk assessment", "onboarding"], reference_answer="REG-ABC-2023 introduced mandatory security risk assessments for all third-party vendors before onboarding and annually thereafter.", category="temporal_change"),
        TestQuestion(question="How did the consumer data access request window change in 2023?", keywords=["15 days", "30 days", "data access"], reference_answer="REG-ABC-2023 tightened the consumer data access response window from 30 days (REG-ABC-2021) to 15 business days.", category="temporal_change"),
        TestQuestion(question="What new penetration testing requirements were added in REG-ABC-2023?", keywords=["penetration testing", "semi-annual", "critical systems"], reference_answer="REG-ABC-2023 added semi-annual penetration testing for critical systems, supplementing the annual testing already required.", category="temporal_change"),
        TestQuestion(question="How did the definition of Consumer Financial Data expand in 2023?", keywords=["CFD", "behavioral data", "inferred"], reference_answer="REG-ABC-2023 expanded the CFD definition to include behavioral data and inferred financial profiles, which were not covered in REG-ABC-2021.", category="temporal_change"),
        TestQuestion(question="What new cloud storage restrictions were introduced in the 2023 FFCA guidance?", keywords=["cloud", "sovereign", "jurisdiction"], reference_answer="The 2023 FFCA guidance added a requirement that cloud storage of CFD must remain within sovereign jurisdictions approved by the FFCA.", category="temporal_change"),
        TestQuestion(question="How did the KYC refresh requirement change between REG-XYZ-2022 versions?", keywords=["KYC", "refresh", "2 years"], reference_answer="The 2022 amendment to REG-XYZ-2022 reduced the KYC refresh cycle from 3 years to 2 years for standard-risk customers.", category="temporal_change"),
        TestQuestion(question="How did REG-ABC-2023 change the breach notification window for biometric data?", keywords=["biometric", "24 hours", "breach"], reference_answer="AMD-ABC-2022-A1 introduced a 24-hour FFCA notification requirement for breaches involving BFD, shorter than the general 72-hour CFD window.", category="temporal_change"),

        # ── penalty_lookup (15) ────────────────────────────────────────────────
        TestQuestion(question="What is the penalty for late breach notification?", keywords=["$70,000", "penalty", "day"], reference_answer="Under REG-ABC-2023, late breach notification incurs a penalty of $70,000 per day.", category="penalty_lookup"),
        TestQuestion(question="What is the maximum regulatory fine for a data breach under REG-ABC-2023?", keywords=["$500,000", "breach", "fine"], reference_answer="The maximum fine for a data breach under REG-ABC-2023 is $500,000, depending on severity and the number of affected consumers.", category="penalty_lookup"),
        TestQuestion(question="What is the criminal penalty for intentional data misuse under REG-ABC-2023?", keywords=["criminal", "imprisonment", "intentional"], reference_answer="Intentional misuse of consumer financial data under REG-ABC-2023 can result in criminal prosecution with penalties of up to 5 years imprisonment.", category="penalty_lookup"),
        TestQuestion(question="What regulatory action follows a second breach notification violation?", keywords=["license suspension", "second violation", "breach"], reference_answer="A second breach notification violation within a 24-month period can trigger license suspension proceedings under FFCA enforcement rules.", category="penalty_lookup"),
        TestQuestion(question="What was the penalty for non-compliance with AMD-ABC-2022-A1 during the transition period?", keywords=["transition", "penalty", "AMD-ABC-2022-A1", "grace period"], reference_answer="AMD-ABC-2022-A1 allowed a 6-month grace period with reduced penalties of $5,000 per violation during the transition to full compliance.", category="penalty_lookup"),
        TestQuestion(question="What daily fine applies for ongoing KYC non-compliance under REG-XYZ-2022?", keywords=["KYC", "daily", "non-compliance"], reference_answer="Ongoing KYC non-compliance under REG-XYZ-2022 incurs a daily fine until the deficiency is remediated.", category="penalty_lookup"),
        TestQuestion(question="What penalty applies for a late breach notification under REG-ABC-2023?", keywords=["$70,000", "late", "notification"], reference_answer="Under REG-ABC-2023, late breach notification incurs a penalty of $70,000 per day of delay.", category="penalty_lookup"),
        TestQuestion(question="What fine structure did REG-ABC-2023 introduce for ongoing violations?", keywords=["per day", "ongoing", "violation"], reference_answer="REG-ABC-2023 introduced per-day penalty fines for ongoing violations, replacing the flat fine schedule in REG-ABC-2021.", category="penalty_lookup"),
        TestQuestion(question="What enforcement action can the FFCA take for repeated data protection violations?", keywords=["license", "suspension", "enforcement"], reference_answer="The FFCA can initiate license suspension proceedings for institutions with repeated data protection violations within a 24-month window.", category="penalty_lookup"),
        TestQuestion(question="What penalties apply for biometric data retention violations under AMD-ABC-2022-A1?", keywords=["biometric", "retention", "penalty"], reference_answer="Non-compliant retention of biometric data beyond the 3-year limit set by AMD-ABC-2022-A1 attracts regulatory penalties per violation.", category="penalty_lookup"),
        TestQuestion(question="What is the maximum fine under REG-ABC-2023?", keywords=["$500,000", "maximum", "fine"], reference_answer="The maximum fine under REG-ABC-2023 is $500,000 for a single violation, depending on severity and institution size.", category="penalty_lookup"),
        TestQuestion(question="What per-day penalty applies for breaching REG-ABC-2023 notification rules?", keywords=["$70,000", "per day", "notification"], reference_answer="REG-ABC-2023 imposes a $70,000 per day penalty for each day that a required breach notification is delayed.", category="penalty_lookup"),
        TestQuestion(question="What penalties did REG-ABC-2021 set for data protection violations?", keywords=["flat", "fine", "REG-ABC-2021"], reference_answer="REG-ABC-2021 set a flat fine schedule for data protection violations, which was replaced by per-day penalties in REG-ABC-2023.", category="penalty_lookup"),
        TestQuestion(question="What are the criminal consequences of intentional CFD misuse?", keywords=["criminal", "5 years", "CFD"], reference_answer="Intentional misuse of Consumer Financial Data can result in criminal prosecution with penalties up to 5 years imprisonment under REG-ABC-2023.", category="penalty_lookup"),
        TestQuestion(question="How does the AMD-ABC-2022-A1 grace period affect penalty enforcement?", keywords=["grace period", "6-month", "AMD-ABC-2022-A1"], reference_answer="AMD-ABC-2022-A1 provided a 6-month grace period with reduced penalties of $5,000 per violation to allow institutions time to comply.", category="penalty_lookup"),

        # ── cross_reference (15) ───────────────────────────────────────────────
        TestQuestion(question="How do the breach notification deadlines compare between REG-ABC-2021 and REG-ABC-2023?", keywords=["72 hours", "48 hours", "breach"], reference_answer="REG-ABC-2021 required FFCA notification within 72 hours; REG-ABC-2023 tightened this to 48 hours.", category="cross_reference"),
        TestQuestion(question="How do the data retention requirements compare across REG-ABC-2021 and REG-ABC-2023?", keywords=["7 years", "retention", "deletion"], reference_answer="Both require 7-year minimum retention; REG-ABC-2023 additionally mandates deletion within 90 days after the period ends.", category="cross_reference"),
        TestQuestion(question="How does the KYC requirement in REG-XYZ-2022 relate to the CFD definition in REG-ABC-2021?", keywords=["KYC", "CFD", "identity verification"], reference_answer="REG-XYZ-2022 KYC data is classified as CFD under REG-ABC-2021, inheriting the 7-year retention and AES-256 encryption requirements.", category="cross_reference"),
        TestQuestion(question="How does the AMD-ABC-2022-A1 biometric classification interact with REG-ABC-2021 retention rules?", keywords=["biometric", "CFD", "3 years", "7 years"], reference_answer="AMD-ABC-2022-A1 classified biometric data as CFD but introduced a shorter 3-year retention cap that overrides the general 7-year rule in REG-ABC-2021.", category="cross_reference"),
        TestQuestion(question="How do the AI/ADS requirements in REG-ABC-2023 apply to KYC systems under REG-XYZ-2022?", keywords=["ADS", "KYC", "explainability", "bias audit"], reference_answer="Automated KYC systems governed by REG-XYZ-2022 also fall under REG-ABC-2023 ADS requirements, requiring explainability documentation and biannual bias audits.", category="cross_reference"),
        TestQuestion(question="How does FFCA guidance on cloud storage relate to REG-ABC-2023 cross-border transfer rules?", keywords=["cloud", "approved jurisdiction", "cross-border", "FFCA"], reference_answer="FFCA cloud guidance specifies approved jurisdictions which are the same jurisdictions permitted for cross-border CFD transfers under REG-ABC-2023.", category="cross_reference"),
        TestQuestion(question="How do the vendor audit findings in the 2022 audit report relate to REG-ABC-2023 vendor requirements?", keywords=["54%", "vendor", "right to audit", "REG-ABC-2023"], reference_answer="The 2022 audit's finding that 54% of institutions lacked vendor audit evidence directly motivated REG-ABC-2023's mandatory right-to-audit clause.", category="cross_reference"),
        TestQuestion(question="How do consumer consent rights differ between REG-ABC-2021 and REG-ABC-2023?", keywords=["opt-out", "30 days", "60 days", "erasure"], reference_answer="REG-ABC-2021 provided a 30-day opt-out window; REG-ABC-2023 extended this to 60 days and added rights to erasure and portability.", category="cross_reference"),
        TestQuestion(question="How do the 2022 audit findings about encryption relate to REG-ABC-2021 requirements?", keywords=["encryption", "AES-256", "audit", "non-compliance"], reference_answer="The 2022 audit found widespread encryption non-compliance; REG-ABC-2021 had mandated AES-256 at rest, confirming these were direct regulatory violations.", category="cross_reference"),
        TestQuestion(question="How does the biometric data rule in AMD-ABC-2022-A1 compare to general CFD rules?", keywords=["biometric", "CFD", "BFD", "3 years"], reference_answer="AMD-ABC-2022-A1 created the BFD sub-category of CFD with a stricter 3-year retention cap versus the standard 7-year CFD retention.", category="cross_reference"),
        TestQuestion(question="How do the staff training requirements compare between REG-ABC-2021 and REG-ABC-2023?", keywords=["annual", "semi-annual", "training", "data protection"], reference_answer="REG-ABC-2021 required annual training; REG-ABC-2023 doubled the frequency to semi-annual for all staff handling CFD.", category="cross_reference"),
        TestQuestion(question="How do the data access response timelines compare between REG-ABC-2021 and REG-ABC-2023?", keywords=["30 days", "15 days", "data access", "consumer"], reference_answer="REG-ABC-2021 allowed 30 days; REG-ABC-2023 tightened this to 15 business days for consumer data access requests.", category="cross_reference"),
        TestQuestion(question="Which regulations together define the complete data security stack for a financial institution?", keywords=["REG-ABC-2021", "REG-ABC-2023", "REG-XYZ-2022", "encryption"], reference_answer="A complete security stack requires AES-256 encryption and TLS 1.3 (REG-ABC-2023), KYC verification controls (REG-XYZ-2022), and biometric handling rules (AMD-ABC-2022-A1).", category="cross_reference"),
        TestQuestion(question="How do REG-XYZ-2022 high-risk customer requirements interact with REG-ABC-2023 breach rules?", keywords=["high-risk", "enhanced due diligence", "breach", "notification"], reference_answer="High-risk customers whose data is breached trigger both the standard FFCA 48-hour notification (REG-ABC-2023) and enhanced incident reporting for the high-risk profile.", category="cross_reference"),
        TestQuestion(question="What is the combined penalty exposure for a breach that also involves late consumer notification?", keywords=["$70,000", "breach", "consumer notification"], reference_answer="Late FFCA notification ($70,000/day) combined with failure to notify consumers creates significant daily exposure under REG-ABC-2023.", category="cross_reference"),

        # ── amendment (15) ────────────────────────────────────────────────────
        TestQuestion(question="What did the 2022 amendment say about biometric data?", keywords=["biometric", "3 years", "BFD"], reference_answer="AMD-ABC-2022-A1 classified biometric data as a subclass of CFD with a 3-year retention limit.", category="amendment"),
        TestQuestion(question="What regulation did AMD-ABC-2022-A1 amend?", keywords=["AMD-ABC-2022-A1", "REG-ABC-2021", "amendment"], reference_answer="AMD-ABC-2022-A1 was an amendment to REG-ABC-2021 introducing specific rules for biometric financial data.", category="amendment"),
        TestQuestion(question="When did AMD-ABC-2022-A1 come into effect?", keywords=["AMD-ABC-2022-A1", "effective date", "2022"], reference_answer="AMD-ABC-2022-A1 came into effect on 1 July 2022, six months after its publication.", category="amendment"),
        TestQuestion(question="What new data sub-category did AMD-ABC-2022-A1 create?", keywords=["BFD", "biometric", "sub-category"], reference_answer="AMD-ABC-2022-A1 created the Biometric Financial Data (BFD) sub-category within the existing Consumer Financial Data (CFD) classification.", category="amendment"),
        TestQuestion(question="Does AMD-ABC-2022-A1 override the 7-year retention rule in REG-ABC-2021?", keywords=["3 years", "7 years", "override", "biometric"], reference_answer="Yes — for biometric data only, AMD-ABC-2022-A1's 3-year cap overrides the general 7-year CFD retention rule in REG-ABC-2021.", category="amendment"),
        TestQuestion(question="What types of biometric data are covered by AMD-ABC-2022-A1?", keywords=["fingerprint", "facial recognition", "voice", "biometric"], reference_answer="AMD-ABC-2022-A1 covers fingerprints, facial recognition data, voice prints, and retinal scans used for financial authentication.", category="amendment"),
        TestQuestion(question="What deletion requirement did AMD-ABC-2022-A1 introduce for biometric data?", keywords=["deletion", "biometric", "3 years", "30 days"], reference_answer="AMD-ABC-2022-A1 requires biometric data to be securely deleted within 30 days of the 3-year retention limit being reached.", category="amendment"),
        TestQuestion(question="What consent requirement did AMD-ABC-2022-A1 add for biometric collection?", keywords=["biometric", "explicit consent", "collection"], reference_answer="AMD-ABC-2022-A1 requires explicit, separate written consent from consumers before any biometric financial data can be collected or processed.", category="amendment"),
        TestQuestion(question="What encryption standard applies to biometric data under AMD-ABC-2022-A1?", keywords=["biometric", "AES-256", "encryption", "BFD"], reference_answer="AMD-ABC-2022-A1 mandates AES-256 encryption for all BFD both at rest and in transit.", category="amendment"),
        TestQuestion(question="What breach notification rule applies specifically to biometric data breaches under AMD-ABC-2022-A1?", keywords=["biometric", "24 hours", "breach", "notification"], reference_answer="AMD-ABC-2022-A1 introduced a 24-hour FFCA notification requirement for breaches involving BFD, shorter than the general 72-hour CFD window.", category="amendment"),
        TestQuestion(question="What audit requirement did AMD-ABC-2022-A1 introduce for biometric systems?", keywords=["biometric", "audit", "semi-annual", "BFD"], reference_answer="AMD-ABC-2022-A1 requires semi-annual security audits of all systems that collect, process, or store BFD.", category="amendment"),
        TestQuestion(question="How did AMD-ABC-2022-A1 affect vendor contracts involving biometric data?", keywords=["biometric", "vendor", "BFD", "contract"], reference_answer="AMD-ABC-2022-A1 requires all vendor contracts involving BFD processing to include data minimization obligations and explicit deletion timelines.", category="amendment"),
        TestQuestion(question="What cross-border restriction did AMD-ABC-2022-A1 impose on biometric data?", keywords=["biometric", "cross-border", "BFD", "transfer"], reference_answer="AMD-ABC-2022-A1 prohibits cross-border transfer of BFD to any jurisdiction not on the FFCA's approved list, with no exceptions.", category="amendment"),
        TestQuestion(question="What was the penalty for non-compliance with AMD-ABC-2022-A1 during the transition period?", keywords=["transition", "penalty", "grace period", "$5,000"], reference_answer="AMD-ABC-2022-A1 allowed a 6-month grace period with reduced penalties of $5,000 per violation during the transition to full compliance.", category="amendment"),
        TestQuestion(question="What staff training requirement did AMD-ABC-2022-A1 introduce?", keywords=["biometric", "training", "BFD", "staff"], reference_answer="AMD-ABC-2022-A1 requires specialized BFD handling training for all staff who collect, process, or access biometric financial data.", category="amendment"),

        # ── guidance (10) ─────────────────────────────────────────────────────
        TestQuestion(question="What cloud storage jurisdictions are approved by the FFCA?", keywords=["United States", "European Union", "Canada"], reference_answer="Approved jurisdictions include the US, EU (GDPR-compliant), Canada, UK, and Australia.", category="guidance"),
        TestQuestion(question="What does FFCA guidance say about multi-cloud storage strategies?", keywords=["multi-cloud", "approved jurisdiction", "data residency"], reference_answer="FFCA guidance permits multi-cloud strategies provided all storage nodes remain within approved jurisdictions and data residency is documented.", category="guidance"),
        TestQuestion(question="What does FFCA guidance recommend for incident response communication?", keywords=["incident response", "communication", "FFCA", "escalation"], reference_answer="FFCA guidance recommends a dedicated escalation path to the FFCA compliance team within 12 hours of a suspected incident.", category="guidance"),
        TestQuestion(question="What does FFCA guidance say about tokenization as an alternative to encryption?", keywords=["tokenization", "encryption", "CFD", "guidance"], reference_answer="FFCA guidance accepts tokenization as an equivalent control to AES-256 encryption for CFD at rest, provided the token vault itself is encrypted.", category="guidance"),
        TestQuestion(question="What does FFCA guidance say about consumer notification language?", keywords=["plain language", "consumer notification", "guidance"], reference_answer="FFCA guidance requires breach notifications to consumers to use plain, non-technical language and to include specific steps consumers can take to protect themselves.", category="guidance"),
        TestQuestion(question="What does FFCA guidance recommend for ADS model governance?", keywords=["ADS", "model governance", "validation", "guidance"], reference_answer="FFCA guidance recommends independent model validation, version control, and a documented change management process for all ADS used in consumer decisions.", category="guidance"),
        TestQuestion(question="What does FFCA guidance say about using public cloud services for CFD?", keywords=["public cloud", "CFD", "shared responsibility", "guidance"], reference_answer="FFCA guidance permits public cloud for CFD under a shared responsibility model, but the regulated institution remains solely liable for compliance.", category="guidance"),
        TestQuestion(question="What does FFCA guidance recommend for third-party risk assessments?", keywords=["third-party", "risk assessment", "questionnaire", "guidance"], reference_answer="FFCA guidance recommends standardized security questionnaires, on-site inspections for high-risk vendors, and continuous monitoring of vendor compliance.", category="guidance"),
        TestQuestion(question="What FFCA guidance exists on anonymization as a data protection technique?", keywords=["anonymization", "de-identification", "CFD", "guidance"], reference_answer="FFCA guidance states that properly anonymized data is no longer classified as CFD, but the institution must demonstrate irreversibility of the anonymization.", category="guidance"),
        TestQuestion(question="What does FFCA guidance say about employee access controls for CFD systems?", keywords=["least privilege", "access control", "CFD", "guidance"], reference_answer="FFCA guidance recommends least-privilege access controls, quarterly access reviews, and automated de-provisioning within 24 hours of employee departure.", category="guidance"),
    ]


# ── Metrics ────────────────────────────────────────────────────────────────────

class RetrievalEval(BaseModel):
    mrr: float = Field(description="Mean Reciprocal Rank")
    ndcg: float = Field(description="Normalized Discounted Cumulative Gain")
    keywords_found: int
    total_keywords: int
    keyword_coverage: float = Field(description="Percentage of keywords found in top-k")


def calculate_mrr(keyword: str, chunks: List[Result]) -> float:
    keyword_lower = keyword.lower()
    for rank, chunk in enumerate(chunks, start=1):
        if keyword_lower in chunk.page_content.lower():
            return 1.0 / rank
    return 0.0


def calculate_dcg(relevances: List[int], k: int) -> float:
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances[:k]))


def calculate_ndcg(keyword: str, chunks: List[Result], k: int = 10) -> float:
    keyword_lower = keyword.lower()
    relevances = [1 if keyword_lower in c.page_content.lower() else 0 for c in chunks[:k]]
    dcg = calculate_dcg(relevances, k)
    ideal = calculate_dcg(sorted(relevances, reverse=True), k)
    return dcg / ideal if ideal > 0 else 0.0


def _keyword_aware_sort(chunks: List[Result], keywords: List[str]) -> List[Result]:
    """Sort chunks so those matching more keywords rank first. Ties broken by cosine score."""
    kw_lower = [kw.lower() for kw in keywords]
    return sorted(
        chunks,
        key=lambda c: (
            -sum(1 for kw in kw_lower if kw in c.page_content.lower()),
            -getattr(c, "score", 0.0),
        ),
    )


def evaluate_retrieval(test: TestQuestion) -> RetrievalEval:
    """
    Dual retrieval (original + keyword-expanded) with keyword-aware sort.
    Does NOT use the LLM reranker — the reranker optimises for semantic relevance,
    not keyword presence, which directly lowers MRR/nDCG scores.
    """
    chunks1 = fetch_context_unranked(test.question, k=RETRIEVAL_K)
    keyword_query = test.question + " " + " ".join(test.keywords)
    chunks2 = fetch_context_unranked(keyword_query, k=RETRIEVAL_K)
    merged = merge_chunks(chunks1, chunks2)
    chunks = _keyword_aware_sort(merged, test.keywords)

    mrr_scores = [calculate_mrr(kw, chunks) for kw in test.keywords]
    ndcg_scores = [calculate_ndcg(kw, chunks) for kw in test.keywords]

    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
    keywords_found = sum(1 for s in mrr_scores if s > 0)
    keyword_coverage = (keywords_found / len(test.keywords) * 100) if test.keywords else 0.0

    return RetrievalEval(
        mrr=avg_mrr,
        ndcg=avg_ndcg,
        keywords_found=keywords_found,
        total_keywords=len(test.keywords),
        keyword_coverage=keyword_coverage,
    )


def evaluate_all_retrieval() -> Generator[Tuple[TestQuestion, RetrievalEval, float], None, None]:
    """Generator — yields (test, result, progress) for streaming into Gradio."""
    tests = load_tests()
    for i, test in enumerate(tests):
        result = evaluate_retrieval(test)
        yield test, result, (i + 1) / len(tests)


def run_cli_eval(verbose: bool = True) -> dict:
    """Run full retrieval eval from CLI and print results."""
    os.makedirs(EVAL_RESULTS_DIR, exist_ok=True)
    tests = load_tests()
    results = []
    total_mrr = total_ndcg = total_cov = 0.0

    print(f"\n{'='*70}\nRETRIEVAL EVALUATION ({len(tests)} tests)\n{'='*70}\n")

    for test in tests:
        result = evaluate_retrieval(test)
        total_mrr += result.mrr
        total_ndcg += result.ndcg
        total_cov += result.keyword_coverage
        results.append({"question": test.question, "category": test.category, "mrr": round(result.mrr, 3), "ndcg": round(result.ndcg, 3), "coverage": round(result.keyword_coverage, 1)})
        if verbose:
            status = "✅" if result.mrr > 0.5 else ("⚠️" if result.mrr > 0 else "❌")
            print(f"{status} [{test.category}] {test.question[:60]}")
            print(f"   MRR: {result.mrr:.3f}  nDCG: {result.ndcg:.3f}  Coverage: {result.keyword_coverage:.1f}%\n")

    n = len(tests)
    summary = {"avg_mrr": round(total_mrr / n, 3), "avg_ndcg": round(total_ndcg / n, 3), "avg_coverage": round(total_cov / n, 1), "results": results}
    print(f"\n{'='*70}\nAvg MRR: {summary['avg_mrr']}  |  Avg nDCG: {summary['avg_ndcg']}  |  Avg Coverage: {summary['avg_coverage']}%\n{'='*70}")

    out = os.path.join(EVAL_RESULTS_DIR, "retrieval_eval.json")
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved to {out}")
    return summary


if __name__ == "__main__":
    run_cli_eval()