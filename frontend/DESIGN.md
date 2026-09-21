# AegisHealth clinical review workspace

Audience: a clinical researcher reviewing one synthetic or consented case. Single
job: compare observed patient measurements, model reasoning and retrieved evidence
before interpreting the generated summary.

Tokens: paper #FFFFFF, workspace #F3F6F7, ink #203238, slate #60757D,
clinical teal #166C66, rising-contribution rose #B04A57. White/gray dominate;
semantic color distinguishes signed contributions, not validated risk strata.

Type: IBM Plex Sans for headings and the probability number, Source Sans 3 for
forms and evidence, IBM Plex Mono for units and provenance. All fonts are bundled.

Layout: a quiet application header and research label above a 360px intake rail
and a wider results workspace. On mobile these become one continuous reading
order. No marketing hero or fake patient activity.

[ AegisHealth                         research workspace ]
[ cardiovascular review             service availability ]
[ patient intake ][ probability gauge | signed SHAP chart ]
[ observed data  ][ evidence passages, DOI and source     ]
[ analyze       ][ three-sentence synthesis              ]

Signature: an evidence bracket linking the model's signed contributions to exact
source passages, styled as an annotated clinical worksheet. Spend visual emphasis
on this reasoning chain, not decoration. Gauge stays neutral until real results;
no invented low/moderate/high clinical cutoffs.

Critique: a generic analytics layout would overemphasize a giant risk percentage
and hide missing evidence. This layout keeps source text and model limitations
visible beside the probability. A narrow teal measurement rail, spacious panels
and grouped fieldsets evoke a diagnostic instrument rather than a newspaper.

States: initially empty; explicit synthetic-example fill (never auto-submit);
loading; partial result without cloud synthesis; complete; validation and network
errors. Editing fields invalidates old results. No browser patient persistence.
Focus, reduced motion, mobile layout and accessible chart alternatives are required.

## Simplified assessment interface

The previous view repeated technical labels, service status, and explanatory
headlines at every level. These competed with the patient measurements and made
small text harder to scan. The revised view uses one descriptive page title,
sentence-case section headings, and no service configuration banner. Setup
instructions belong in project documentation. An unavailable summary remains
clearly identified beside its results without exposing environment settings.

Keep the existing restrained teal, white, and slate palette. Use a 350px form rail,
42px controls, larger supporting text, and flat bordered panels. Remove numbered
field groups, redundant section labels, and decorative summary accents. Preserve
source passages, uncertainty, consent information, keyboard focus, and a single
mobile reading order. No additional ornament or marketing copy is needed.
