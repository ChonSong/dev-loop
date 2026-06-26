---
name: ncc-regulatory-gap-mapping
category: construction
description: "Map NCC clauses that implicitly restrict additive manufacturing (3D printing) to concrete design features and mitigation steps."
version: 1.0
created: 2026-06-17
author: sean
---

# NCC Regulatory Gap Mapping

This skill maps the National Construction Code (NCC) Volume 2 (2022) clauses that implicitly restrict 3‑D printing to concrete design features and mitigation steps.

## 1. Clause‑to‑Risk Mapping

| Clause | Requirement | Implicit 3‑D‑Printing Barrier | Source |
|--------|-------------|------------------------------|--------|
| **H1P1** | Structural integrity – load‑bearing members must be “concrete, steel, masonry or timber” (AS 3600/AS 4100) | Printed concrete/polymer members are not listed; must prove strength, fatigue, moisture resistance. | Vol 2, p. 29 |
| **H1D4** | Footings & slabs – concrete with bearing pressure ≥50 kPa (AS 2870) | Printed slab must achieve ≥20 MPa compressive strength and meet AS 2870; no explicit additive clause. | p. 32 |
| **H1D5** | Masonry – cement‑based units per ISO 4928/AS 3600 | Printed panels lack standard bond & mortar; fire/moisture resistance unproven. | p. 35 |
| **H1D6** | Framing – steel/timber per AS 4100/AS 1760 | Printed composite frames not covered; need performance‑solution justification. | p. 43 |
| **H3P1** | Fire safety – 92.6 kW/m² heat flux for 60 min | Printed polymers have low fire rating; must achieve required FRL via testing or evidence‑of‑suitability. | p. 49 |
| **H3D2** | Fire detection & alarm – efficacy >0.95 | Wall assemblies change acoustic/thermal signatures; sensor placement must be re‑validated. | p. 51 |
| **H4P1** | Wet areas – moisture‑penetration barriers per AS 3740 | Printed polymers often lack permeability & surface‑finish for wet‑area compliance. | p. 55 |
| **H6P1** | Energy efficiency – 7‑star NatHERS rating or Specification 44 limits | Printed envelopes have thermal bridges; need validated thermal‑performance assessment. | p. 62 |
| **H8P1** | Livable Housing – step‑free access, accessible bathrooms, grabrail installations | Printed interior finishes must meet accessibility; may need additional fixtures. | p. 68 |

## 2. Feature List – Design Features that Address the Risks

| Feature | Risk Category | NCC Clause(s) | Implementation Hint |
|---------|---------------|-------------|----------------------|
| Material Qualification Report (MQR) | Structural (H1P1, H1D4, H1D5) | 1, 2, 3 | ASTM C39 (compressive) & ASTM D638 (tensile); strength ≥20 MPa; creep & fatigue curves |
| Fire‑Resistive Coating System | Fire (H3P1) | 5 | UL‑certified intumescent/ceramic coating; 60‑min fire rating per AS 1530.4 |
| Water‑Barrier Membrane | Moisture (H4P1) | 7 | 0.2 mm AS 2870 polyethylene under‑layment, sealed laps & penetrations; water‑spray test |
| Thermal‑Bridge Mitigation | Energy (H6P1) | 8 | NatHERS simulation; insulated inserts or sandwich panels; provide U‑value report |
| Acoustic & Vibration Damping Layer | Acoustic (H4P6) | 6 | Attach mineral‑wool or rubber mat behind printed partitions; verify DnT,w + Ctr ≥ 45 |
| Performance‑Solution Evidence Package | General | 1‑10 | Compile test reports, expert judgement, calculations; reference BCA Part A5‑G2/A5‑G4 |
| QA & Inspection Protocol | General (Verification) | 8‑9 | In‑process ultrasonic NDT; log layer adhesion & dimensional tolerance |
| Construction‑Method Statement (CMS) | General (Verification) | 8‑9 | Document printing process, curing, post‑print handling; link each step to a QA checkpoint |

> **How to use this skill**  
> 1. Identify the NCC clause(s) that apply to your project.  
> 2. Map each risk to the corresponding feature in the table.  
> 4. Generate the required evidence (MQR, fire‑rating test, etc.) and include it in your compliance dossier.

---  

*Support file:* `references/ncc-reg-gap.md` – concise mapping and feature list.
```
