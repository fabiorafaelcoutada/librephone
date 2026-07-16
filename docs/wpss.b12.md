# wpss.b12 — X.509 Secure Boot Certificates (Fairphone FP6 / LineageOS)

SPDX-License-Identifier: CC-BY-SA-4.0
SPDX-FileCopyrightText: 2026 Gustavo Paredes <lu2jgp@gmail.com>

The `wpss.b12` segment contains the **OEM Secure Boot certificate chain** for the
WPSS (Wireless SubSystem, Qualcomm Hexagon DSP) firmware. These certificates
authenticate the DSP firmware image during the PIL (Peripheral Image Loader)
boot process via SCM (Secure Channel Manager) calls to the TrustZone.

The chain is compared against two other firmware sources to distinguish
**production** from **test/development** builds.

## Certificate Chain: wpss.b12 (LineageOS FP6 — PRODUCTION)

Located in `code_offset` metadata region of the ELF (offset `0x3f8`–`0x137a`,
file `image/qca6750/wpss.b12` inside `modem.img`).

```
┌─────────────────────────────────────────────────────────────────────┐
│ Generated OEM Root CA (SELF-SIGNED) ← burned in SoC eFuse          │
│   OU: Fairphone BV, T2MO OEM Key, Amsterdam, NL                   │
│   Validity: 2025-03-05 → 2045-02-28                                │
│   SHA256: 9dda957ad47e1ac4bc0a5403f3a0c3e58212d6e73cb86a7c8635...  │
│           ↓ signs                                                   │
│ Generated OEM Attestation CA                                        │
│   O: SecTools, L: San Diego, NL                                    │
│   Validity: 2025-03-05 → 2045-02-28                                │
│   SHA256: 9538b9ce43da2bd5900477d3a5d73fcb55f15a0af30f70499acc...  │
│           ↓ signs                                                   │
│ OEM Device Certificate (leaf)                                       │
│   O: SecTools, L: San Diego, USA                                   │
│   Validity: 2026-05-29 → 2046-05-24                                │
│   SHA256: 4c8b30bbe99e6111c58a7eeffa271debba555ca25b3049c1b12f...  │
└─────────────────────────────────────────────────────────────────────┘
```

### Cert #1 — OEM Device (Leaf)

| Field | Value |
|-------|-------|
| Subject | `C=US, ST=California, O=SecTools, L=San Diego` (no CN) |
| Issuer | `Generated OEM Attestation CA (NL)` |
| Serial | `0x1` |
| Validity | 2026-05-29 → 2046-05-24 |
| SHA256 | `4c8b30bbe99e6111c58a7eeffa271debba555ca25b3049c1b12ffd7864078e3f` |
| Key Usage | Digital Signature |
| CA Flag | `False` |
| Purpose | Attests individual firmware image during PIL load |

### Cert #2 — OEM Attestation CA (Intermediate)

| Field | Value |
|-------|-------|
| Subject | `C=NL, ST=North Holland, O=SecTools, L=San Diego, CN=Generated OEM Attestation CA` |
| Issuer | `C=NL, CN=Generated OEM Root CA, OU=Fairphone BV, OU=T2MO OEM Key, O=SecTools, ST=North Holland, L=Amsterdam` |
| Serial | `0x1` |
| Validity | 2025-03-05 → 2045-02-28 |
| SHA256 | `9538b9ce43da2bd5900477d3a5d73fcb55f15a0af30f70499acc707ca3e89b5f` |
| Key Usage | Certificate Signing |
| CA Flag | `True` |
| Purpose | Signs OEM device certificates for individual firmware images |

### Cert #3 — OEM Root CA (Root)

| Field | Value |
|-------|-------|
| Subject | `C=NL, CN=Generated OEM Root CA, OU=Fairphone BV, OU=T2MO OEM Key, O=SecTools, ST=North Holland, L=Amsterdam` |
| Issuer | Same as subject (self-signed) |
| Serial | `0x1` |
| Validity | 2025-03-05 → 2045-02-28 |
| SHA256 | `9dda957ad47e1ac4bc0a5403f3a0c3e58212d6e73cb86a7c86350cc5bec9bacf` |
| Key Usage | Certificate Signing + CRL Sign |
| CA Flag | `True` |
| Purpose | Trust anchor; must be fused (eFuse) into SoC OTP memory |

---

## Certificate Chain: wpss.mbn (PostmarketOS/Mobian — TEST/DEV)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Generated Test Root CA (SELF-SIGNED)                                │
│   OU: CDMA Technologies, General Use Test Key (for testing only)   │
│   Validity: 2016-04-08 → 2036-04-03                                │
│   SHA256: 959b8d0549ef41befabc24f51efe84fee366ac169ab04a0db30c...  │
│           ↓ signs                                                   │
│ Generated Test Attestation CA                                       │
│   Validity: 2016-04-08 → 2036-04-03                                │
│   SHA256: c0a692567dfbf1ef513cbcf7e22737494f724e830eb6372a675e...  │
│           ↓ signs                                                   │
│ SecTools Test User (leaf)                                           │
│   Validity: 2023-01-09 → 2043-01-04                                │
│   SHA256: 92fd1d23d48ba497c3cf7cff8499e0631b5ee458933690e7ba01...  │
└─────────────────────────────────────────────────────────────────────┘
```

All three certificates live inside `wpss.mbn` at offsets:
- Root CA: `0x17d5` (734 bytes)
- Attestation CA: `0x151a` (699 bytes)
- Device cert: `0x12c0` (602 bytes) — within `.b01` (boot config) segment

---

## Comparison Summary

| Property | wpss.b12 (LineageOS) | wpss.mbn (PMOS) | wlanmdsp.mbn (ath10k) |
|----------|---------------------|------------------|-----------------------|
| **Root CA CN** | Generated OEM Root CA | Generated Test Root CA | Generated Test Root CA |
| **Root CA Org/OU** | Fairphone BV, T2MO OEM Key | CDMA Technologies (Test Key) | CDMA Technologies (Test Key) |
| **Root Validity** | 2025-03-05 → 2045-02-28 | 2016-04-08 → 2036-04-03 | 2015-09-10 → 2035-09-05 |
| **Root SHA256** | `9dda957a...` | `959b8d05...` | `f8ab2052...` |
| **Root Locale** | Amsterdam, NL 🇳🇱 | San Diego, US 🇺🇸 | San Diego, US 🇺🇸 |
| **Leaf Subject** | SecTools (no CN) | SecTools Test User | SecTools Test User (+debug OUs) |
| **Purpose** | ✅ Production | ❌ Test/Development | ❌ Test/Development |

## SCM (Secure Channel Manager) Call IDs

The PIL driver uses SCM calls (SMC #0 on ARM) to authenticate firmware images
with the TrustZone. The function IDs typically follow this pattern:

- `0xC20000xx` / `0xC30000xx` — Qualcomm SCM fastcall
- The certificate region index is passed as a parameter

For the WPSS firmware, the SCM call flow is:

1. PIL reads the `.b12` segment (or equivalent cert region from `.mbn`)
2. Passes cert pointer and length to TrustZone via `qcom_scm_pas_auth_and_reset()`
3. TrustZone validates the certificate chain against the eFused Root CA
4. If chain is valid: DSP image is authenticated and started
5. If chain is invalid: image load is rejected (device may not boot)

## Replaceability Assessment

| Component | Replaceable? | Condition |
|-----------|-------------|-----------|
| Root CA (eFuse) | ❌ No | Fused in SoC OTP during manufacturing |
| OEM Device Cert | ✅ Yes | Part of firmware image, can be signed differently |
| Attestation CA | 🔶 If Root CA supports it | Must be signed by unknown Root CA |
| Firmware Code | 🟡 Only if Secure Boot disabled | Qualcomm secure boot must be off |

The **root trust anchor** is the OEM Root CA burned into the SoC eFuse array
during manufacturing. This means:
- Production devices will only boot firmware signed by the **Fairphone BV** chain
- Test firmware (from PMOS/Mobian) uses the CDMA Technologies test chain and
  **will NOT boot on production hardware** unless Secure Boot is disabled
- The test chain is used during development with unsigned/engineering bootloaders

---

*SPDX-License-Identifier: CC-BY-SA-4.0*
