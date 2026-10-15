**Current: FT01 quote and dry-fit package.** Start with [START_HERE.md](START_HERE.md) or the [current illustrated review](deliverables/current/fabrication/fit-trial/index.html). Older linked studies below remain historical.

# Shower / Kohler installation

Private local reconstruction and repair study, using a preserved Polycam wall scan, CadQuery geometry, Blender inspection and a browser measurement worksheet. **R001 is provisional and not for fabrication.**

Start with [START_HERE.md](START_HERE.md). Full requested scope and constraints are preserved in [docs/project_request.md](docs/project_request.md).

The [verified Kohler parts record](docs/verified_kohler_parts.md) preserves component identity evidence. [Questions answered](docs/questions_answered.md) explains the current findings.

```sh
cd ~/Code/shower-kohler-valve
./project review       # local review + measurement form
./project build        # reuse unchanged stages; never write accepted canon
./project validate     # evidence, revision and snapshot integrity
./project query coverage CUT-03
./project query solid CUSTOM-01
./project handoff      # full committed Git bundle + compact analysis review
```

The three complete original archives are tracked directly in ordinary Git under `data/raw/polycam`. All normal processing uses those copies, independent of Downloads. No external hosting or scan uploads. See [setup and restoration](environment/README.md), [executed checks](docs/validation/README.md), and the [downstream audit prompt](docs/downstream_audit_prompt.md).
