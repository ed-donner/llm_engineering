# FFCA Guidance Note GN-2023-04: Cloud Storage Compliance for Financial Data

**Guidance ID:** GN-2023-04  
**Year:** 2023  
**Issuing Authority:** Federal Financial Compliance Authority (FFCA)  
**Related Regulations:** REG-ABC-2021, REG-ABC-2023

---

## Purpose

This guidance note clarifies FFCA expectations for financial institutions that store Consumer Financial Data (CFD) using cloud infrastructure, following the expanded cloud storage requirements introduced in REG-ABC-2023 Section 2.

---

## Approved Cloud Jurisdictions (Appendix A Reference)

Cloud storage providers used for CFD must be physically located in the following approved jurisdictions:
- United States (all regions)
- European Union (GDPR-compliant regions only)
- Canada
- United Kingdom (post-Brexit adequacy decision applies)
- Australia

Data residency in non-approved jurisdictions is prohibited unless a specific FFCA waiver is obtained.

---

## Encryption in Transit and at Rest

All CFD stored in cloud environments must be encrypted:
- **At rest:** AES-256-GCM (as required by REG-ABC-2023; CBC mode deprecated)
- **In transit:** TLS 1.3 minimum (TLS 1.2 acceptable only with explicit FFCA approval until December 2024)

Key management must use a Hardware Security Module (HSM) or a FIPS 140-2 Level 3 certified key management service.

---

## Multi-Tenancy Risks

Institutions using shared cloud infrastructure must implement logical isolation controls to prevent cross-tenant data access. Annual penetration tests must specifically include multi-tenancy isolation tests.

---

## Incident Response in Cloud Environments

Cloud providers must be contractually bound to:
- Notify the institution within **6 hours** of any detected security incident
- Provide forensic data within **48 hours** of a breach
- Cooperate with FFCA investigations including data preservation orders

---

## Recommended Practices

1. Implement Cloud Access Security Broker (CASB) solutions
2. Enable immutable logging for all data access and modification events
3. Use zero-trust network access (ZTNA) for all administrative access to cloud storage
4. Conduct quarterly access reviews and remove stale permissions

---

## Enforcement Note

This guidance is not a new regulation. However, non-compliance with these practices will be considered evidence of inadequate controls during FFCA audits and may trigger enforcement under REG-ABC-2023 Section 7.
