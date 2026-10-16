GPT Pro review package for the Kohler shower backing plates

This package asks Pro to review the design independently and write concrete instructions for the local agent to revise the CAD and prepare the fabricator, plumber and homeowner handoffs. It does not itself change or release the current CAD.

GP04 CLARIFICATIONS

The inner-plate face measurements were taken within one plane, and the owner considers the caliper readings highly accurate. They need no tip-depth correction. The six installed tip-to-tip measurements remain 3D distances spanning different wall depths. Numeric R005 and all FT01 CAD are unchanged. GP01, GP02 and GP03 are retained as history; use this GP04 package for the review.

The expert is expected to assemble and install the parts, not supply new expert measurements or a CAD survey. The owner found measuring difficult but will supply a handful of indispensable machining dimensions if needed. Use existing evidence first. Ask only when a value directly changes the custom main or diverter plate aperture, outside profile, thickness or an essential locator; do not request readings merely to refine the scan or complete a broad checklist. For each indispensable request, identify the affected CAD decision, why existing evidence or a simpler design cannot resolve it, exact illustrated contacts and reference plane, easiest method, required precision, and how the answer changes the machining file. Send one short prioritized batch, or request none if the chosen machining scope needs no new dimensions. Ordinary assembly, fit and water checks remain the installer's work, distinct from this measurement burden.

PLATE-ONLY MACHINING DELIVERABLES

Distill the CAD down to the smallest justified set of standalone custom main and diverter plates that should actually be fabricated. Evaluate which prototype/thickness/diameter/locator variants are worth keeping; do not carry every historical alternative forward. For each retained scenario give its purpose, exact nominal dimensions or explicit unresolved parameters, stock/material/process, quantity, revision/status and exact output filenames. Distinguish mutually exclusive choices from parts needed together. Each manufacturing STEP must contain exactly one valid custom plate solid in mm at a documented local origin, with no wall, scan, valve, plumbing, factory trim or assembly. Provide matching clean DXF and STL where useful, dimensioned drawings, isolated part previews, a short upload list and hashes. Keep assembly/reference files outside all manufacturing folders and ZIPs. Reimport the actual exports and verify their geometry and contents before delivery.

06_PLATE_ONLY_FILE_GUIDE.txt identifies the current standalone candidate files. Pro must evaluate and prune these, not assume all six should be made.

HOW TO USE IT

1. Extract GPT_PRO_PROMPT_PACKAGE_GP04.zip on your computer.
2. Give Pro 02_PROJECT_BRIEF.txt, 03_VISUAL_EVIDENCE.pdf, 04_TECHNICAL_REFERENCE.zip and 06_PLATE_ONLY_FILE_GUIDE.txt. If the technical ZIP cannot be inspected, extract its repo_snapshot/ folder and provide the specific CAD, reports or manufacturer PDFs Pro needs. The brief and visual PDF are sufficient to begin; Pro must identify anything it could not inspect.
3. Copy the complete contents of 01_PASTE_INTO_GPT_PRO.txt into your message. No previous conversation is required. Do not send only the old FT01 prompt from inside the technical archive.
4. Bring Pro's full response, especially BEGIN AGENT INSTRUCTIONS through END AGENT INSTRUCTIONS, back to this local agent. The agent should implement supported revisions, verify the files and make the new handoffs. Pro's review is not a physical fit or water test.

No files have been uploaded and no message to Pro or any vendor has been sent. This is a private review package containing home photographs. It is different from the custom-only quote ZIPs intended for fabricators.

CONTENTS

01_PASTE_INTO_GPT_PRO.txt - full review prompt and required response structure.
02_PROJECT_BRIEF.txt - current facts, all key measurements, decisions and unresolved fit conditions.
03_VISUAL_EVIDENCE.pdf - readable measured photographs, actual rear/attached-scan observations, current geometry and scope-labeled historical diagrams.
04_TECHNICAL_REFERENCE.zip - current CAD, selected canon/observation records, reports, source scripts, manufacturer PDFs and existing FT01 guide/drawings/templates. Paths under repo_snapshot/ match the local repository. It is not a complete runnable checkout. Its 82 repo_snapshot files are unchanged from GP01; review_addenda/ contains the measurement-method clarification, owner/expert responsibility constraint and plate-only machining deliverables requirement. These override older measurement assignments in the snapshot. Later software maintenance is not incorporated into this frozen snapshot.
05_RETURN_TO_AGENT.txt - short message to accompany Pro's response when returning it to the agent.
06_PLATE_ONLY_FILE_GUIDE.txt - exact candidate CAD paths, dimensions and separation from assembly references.
MANIFEST.json - hashes, sizes, source snapshot and explicit omissions.

DESIGN STATUS

FT01 remains the quote and sacrificial dry-fit baseline, not a permanent-installation release. Main 220 mm with upright capsule 116.35 x 151.10 mm; diverter 124/80 mm with 120/80 fallback; 1.524 mm and 3 mm stocks. Pro is expressly invited to challenge these choices. Current files have no bolt locators. A new notched or tabbed version must be justified and checked before being included in order files.

Large original scan ZIPs, the Blender scene and generated mesh caches are deliberately omitted. Their source identities are recorded; all remain in the local project. The visual packet does not replace raw geometry for a new numerical scan check. The agent can perform that work after the review.

Rebuild this package locally with .venv/bin/python scripts/prepare_pro_review.py. This packages existing evidence and CAD; it does not rebuild or change FT01. Source text lives in docs/gpt_pro_review/. Recheck snapshot hashes when updating the package after a later design revision.
