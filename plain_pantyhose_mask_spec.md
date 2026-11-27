# Plain pantyhose reconstruction specification

Status: design basis and acceptance criteria. The garment geometry is not yet approved.

## Correct interpretation of the reference archive
All 12 photographs in `ScreenShot_2026-11-26_211016_216.7z` depict the SAME pantyhose design/construction. The visible colors, lace, leopard print, stripes, and other surface patterns vary; they are not separate garment patterns. Use all photographs together as complementary views of the same item. Ignore surface decoration and reproduce the common garment silhouette as a plain, single-color version.

### Reference photographs
- `ScreenShot_2026-11-26_210926_408.png`: standing front/full-body view; overall silhouette and waist-to-leg appearance.
- `ScreenShot_2026-11-26_210916_725.png`: close view of upper legs/pelvis; useful for upper-thigh and crotch construction.
- `ScreenShot_2026-11-26_211123_092.png`: close view of legs and feet; useful for opacity, leg coverage, and foot/toe continuation.
- `ScreenShot_2026-11-26_211104_413.png` and `ScreenShot_2026-11-26_211116_825.png`: standing front views, useful for waist, hip, thigh and full-leg silhouette.
- `ScreenShot_2026-11-26_211005_202.png`, `211016_216.png`, `211025_154.png`, `211041_953.png`, `211049_141.png`, `211056_048.png`, and `211132_617.png`: complementary poses/views of the same garment; use them to resolve areas hidden in other views.

## Separate technical reference set
- `ScreenShot_2026-11-26_193601_620.png` is a VaM side-view technical screenshot.
- `21_pantyhose_tr.jpg` is the texture used by the garment shown in 620.
- The two horizontal marks on the right buttock in 620 correspond to the two horizontal marks in 21_pantyhose_tr.jpg. They are temporary alignment/calibration marks for calculating texture placement, NOT garment decorations. Do not reproduce them on the final garment.
- `ScreenShot_2026-11-26_233158_512.png` is an old VaM front-view garment screenshot, not the real-wear visual target.
- `ScreenShot_2026-11-26_232916_446.png` is an earlier incorrect VaM version, not the target.

## Target appearance and construction
- Make the common real-wear garment silhouette from the photo set, but remove all pattern/color differences and ornamentation: plain, single-color fabric.
- Reproduce realistic sheer fabric appearance: translucency, subtle sheen, and close skin fit. Do not turn it into opaque briefs or leggings.
- One garment surface covers the intended waist/hip/pelvis area and continues through the crotch into both legs and down over the feet/toes, following the actual photographed construction.
- Preserve the full Genesis 2 Female body mesh. Never delete hips, pelvis, crotch, torso, leg, or foot geometry from the body reference.
- Do not add lace, bows, decorative garters, stripes, leopard print, or the calibration marks.
- Use the different photos as complementary views of the same item, not as different garment designs.

## Tutorial-aligned build sequence
1. Work on a duplicate of the full body mesh; preserve the untouched source.
2. Subdivide the duplicate sufficiently for a clean painted mask. Do not assume a specific interpretation of “subdivide to 3” until the tutorial operation is verified.
3. Define the garment coverage mask from the shared silhouette visible across the real-wear photos, not from material names alone.
4. Run Mesh Extract with Extra as Solid disabled and smoothing set to zero for the initial extraction.
5. Inspect waist, pelvis/crotch, inner thighs, knees, ankles, and toe boundaries before any remesh.
6. Only after the extracted shell passes visual inspection, quad-remesh to the tutorial's approximate 2,000–6,000 vertex range.
7. Shrinkwrap to the untouched original Genesis 2 body with Outside snap and 0.0004 m offset, then validate in VaM.

## Mandatory acceptance checks
- Front, side, and back views match the common silhouette across the real-wear photo set.
- Surface is plain and single-color; pattern and calibration marks are absent.
- Waist/hip/pelvis coverage follows the photos and remains sheer rather than becoming opaque underwear.
- Crotch and inner-thigh transitions are continuous as required by the photographed construction.
- Both feet and toe tips are covered.
- Original body object remains unchanged.
- Report boundary loops by anatomical location; do not treat a raw boundary-edge count as proof of correctness.
- Do not proceed to the next stage if any check fails.

## Current known limitation
The existing automatic material-based mask and its 542 boundary edges are diagnostic only and are not accepted as the final mask. No final garment has been produced.
