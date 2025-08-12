# Venterum for Opskrifter

Placer de `.md`-filer, der er downloadet fra udregneren, i denne mappe.
Eventuelle billeder, der hører til en opskrift, skal have samme filnavn (f.eks. `min_opskrift.md` og `min_opskrift.jpg`) og placeres også her.

Når `generate_content.py`-scriptet køres, vil det automatisk:
1. Oprette en ny side-mappe i `content/recipes/`.
2. Flytte og omdøbe `.md`-filen til `index.md` i den nye mappe.
3. Flytte eventuelle tilhørende billeder med over.
4. Tømme denne mappe (bortset fra denne fil).