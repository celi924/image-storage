# Plain pantyhose mask specification

Status: design/acceptance specification only. No garment geometry is approved by this document.

## Visual source
- Use `ScreenShot_2026-11-26_233158_512.png` as the original front-view garment reference.
- Do not use `ScreenShot_2026-11-26_232916_446.png` as the target; it is the earlier incorrect version.
- The target is a plain, single-color, sheer pantyhose. Remove visual details from the reference garment: lace waistband, lace thigh bands, bows/garter decorations, and all other ornamentation.

## Coverage requirements
- One continuous garment surface from the waist/upper hip, across the pelvis and crotch, down both legs, and over both feet/toes.
- Preserve the full Genesis 2 Female body mesh. Never delete the hips, pelvis, crotch, torso, leg, or foot geometry from the body reference.
- No opaque underwear/briefs section. The fabric appearance must remain consistently sheer and plain.
- Waist opening is a single continuous boundary around the waist. Foot coverage must include toes; no ankle cutoff.
- Crotch must be continuous with no split, hole, or disconnected left/right leg panels.

## Tutorial-aligned build sequence
1. Work on a duplicate of the full body mesh; preserve the untouched source.
2. Subdivide the duplicate sufficiently for a clean painted mask. Do not assume a specific interpretation of “subdivide to 3” until the tutorial operation is verified.
3. Paint/define the garment coverage mask from the reference silhouette, not from material names alone.
4. Run Mesh Extract with Extra as Solid disabled and smoothing set to zero for the initial extraction.
5. Inspect the waist, crotch, inner thighs, ankles, and toe boundaries before any remesh.
6. Only after the extracted shell passes visual inspection, quad-remesh to the tutorial's approximate 2,000–6,000 vertex range.
7. Shrinkwrap to the untouched original Genesis 2 body with Outside snap and 0.0004 m offset, then validate in VaM.

## Mandatory acceptance checks
- Front and back views show one continuous plain garment, with no lace/bows/straps.
- Waist boundary is even and anatomically placed; pelvis remains covered.
- No crotch gap, inner-thigh gap, or leg-to-foot discontinuity.
- Both feet and toe tips are covered.
- Original body object remains unchanged.
- Report boundary loops by anatomical location; do not treat a raw boundary-edge count as proof of correctness.
- Do not proceed to the next stage if any check fails.

## Current known limitation
The existing automatic material-based mask and its 542 boundary edges are diagnostic only and are not accepted as the final mask. No final garment has been produced.
