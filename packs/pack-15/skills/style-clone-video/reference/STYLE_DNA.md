# The STYLE DNA - 13 dimensions

The lock is a JSON document. `analyze_frames.py` fills the **measured** half,
you fill the **semantic** half in `style_notes.json`, and
`plan_shots.py` merges both into the block that is injected into every prompt.

| # | dimension | measured by | notes / filled by you |
|---|---|---|---|
| 1 | **Style line** | - | one sentence naming mood, medium, grade, camera, finish |
| 2 | **Technical** | ffprobe | resolution, aspect, fps, duration, frame count |
| 3 | **Palette** | k-means, 6 clusters | hex + share per cluster; add *what each hex is used for* |
| 4 | **Backgrounds** | - | flat / gradient / textured / grid / 3D / noise / grain / vignette |
| 5 | **Illustration & icon language** | - | 2D flat, isometric, 3D clay, glass, line art; stroke weight, corner radius, shadow style, depth |
| 6 | **UI elements** | - | none / which ones; buttons, labels, cards |
| 7 | **Typography** | text-band detection | family, weights, size hierarchy, letter spacing, colour, how text animates in and out |
| 8 | **Lighting, shadows, texture, finish** | grain + vignette + bloom | key light, shadow style, halation, film finish |
| 9 | **Camera language** | - | static, slow push, parallax, handheld, framing habit |
| 10 | **Motion language** | motion delta per shot | easing, entrances, gap between elements, transition types |
| 11 | **Recurring motifs** | - | the elements that repeat; they become the master panel content |
| 12 | **Cut rhythm** | scene detection | cuts per 10 s, median shot length, shot-length distribution |
| 13 | **Forbidden** | - | what must never be cloned (logos, characters, exact copy) |

## What the measurement actually gives you

| metric | how it is computed | how to use it |
|---|---|---|
| palette | k-means (k=6, seeded, deterministic) on downsampled pixels | the only hexes the new video may use |
| mean luma / p01 / p99 | luminance percentiles | the exposure window; p99 is where highlights blow out |
| contrast_std | std of luminance | how hard the key light is |
| saturation | mean HSV saturation | near 0 = strictly monochrome; that is a lock, not a preference |
| bloom_fraction | share of pixels above 0.93 luma | halation strength |
| grain | std of the high-frequency residual in flat areas only | film-grain amount; a real estimate, not a global std |
| vignette_db | 20*log10(core mean / edge mean) | the falloff the new render must reproduce |
| sharpness | variance of the Laplacian | soft focus vs crisp |
| edge_density | mean gradient magnitude | how much structure the frame carries |
| text_bands | rows whose gradient energy exceeds 1.9x the median band, grouped | burned-in title geometry: y-range, colour, height. On the reference clip this found the two lyric lines and the `kurdî9` mark automatically |
| composition | gradient-energy centroid + rule-of-thirds bias | where the subject sits |
| motion | mean abs delta between consecutive sampled frames | how much movement a shot carries |
| cut rhythm | ffmpeg scene score at a threshold | shot length and cut density |

## The locked block

`plan_shots.py` turns the DNA into a paragraph that is repeated verbatim in every scene
prompt: frame, palette hexes, exposure figures, finish (grain, vignette, bloom), background,
lighting, illustration language, camera, composition, typography, motifs, forbidden.

**Never hand-edit that paragraph per scene.** If a scene needs something different, the
style lock is wrong - fix the lock, not the scene.

## Copy the style, not the content

The `forbidden` list is not decoration. A style clone means: the grade, the framing
habit, the pacing, the typography geometry, the motifs. It does not mean the reference's
characters, logos, brand names or exact lines. Burned-in text in the reference (song
lyrics, watermarks) is **not** part of the style - it is content, and it is reproduced in
the new video as a clean, separately-added title card.
