import pandas as pd
import os
import glob
import hashlib
import shutil
import re
from datetime import datetime

# ---- KONFIGURATION ----
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CONTENT_DIR = os.path.join(BASE_DIR, 'content')

EXCEL_FILE_PATH = os.path.join(DATA_DIR, 'laboratorie_data.xlsx')

CALCULATOR_PAGE_PATH = os.path.join(CONTENT_DIR, 'calculator', 'index.md')
STABILIZER_PAGE_PATH = os.path.join(CONTENT_DIR, 'stabilizer', 'index.md')
INGREDIENTS_PAGE_PATH = os.path.join(CONTENT_DIR, 'ingredients', '_index.md')
JSON_OUTPUT_PATH = os.path.join(BASE_DIR, 'static', 'ingredients.json')
RECIPE_CONTENT_DIR = os.path.join(CONTENT_DIR, 'recipes')

# ---- HJÆLPEFUNKTIONER ----
def write_if_changed(filepath, new_content):
    """Skriver kun til filen, hvis indholdet er ændret."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        if hashlib.md5(new_content.encode()).hexdigest() == hashlib.md5(existing_content.encode()).hexdigest():
            return False
    except FileNotFoundError:
        pass

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"  ✅ Success! '{os.path.basename(filepath)}' er blevet genereret/opdateret!")
    return True

def get_existing_date(filepath):
    """Læser en markdown-fil og returnerer 'date'-værdien fra front matter."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        in_front_matter = False
        
        for i, line in enumerate(lines):
            if i == 0 and line.strip() == '---':
                in_front_matter = True
                continue
            elif line.strip() == '---' and in_front_matter:
                break
            elif in_front_matter:
                match = re.match(r'^date:\s*"?([^"\s]+)"?', line)
                if match:
                    return match.group(1)
    except FileNotFoundError:
        return None
    return None

# ---- FORSIDE GENERATOR ----
def generate_homepage():
    """Genererer forsiden med dynamisk indhold som seneste opskrift."""
    print("Genererer Forside...")
    
    homepage_path = os.path.join(CONTENT_DIR, '_index.md')
    now_date = datetime.now().strftime('%Y-%m-%d')

    # Find seneste opskrift
    latest_recipe = None
    latest_date = datetime.min
    
    recipe_files = glob.glob(os.path.join(RECIPE_CONTENT_DIR, '*', 'index.md'))
    
    for recipe_file in recipe_files:
        try:
            with open(recipe_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            date_match = re.search(r'^date:\s*"?([^"\s]+)"?', content, re.MULTILINE)
            title_match = re.search(r'^title:\s*"?([^"]+)"?', content, re.MULTILINE)
            
            if date_match and title_match:
                recipe_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                if recipe_date > latest_date:
                    latest_date = recipe_date
                    recipe_title = title_match.group(1).replace('"', '').replace('"', '').replace('"', '')
                    recipe_slug = os.path.basename(os.path.dirname(recipe_file))
                    latest_recipe = {
                        'title': recipe_title,
                        'slug': recipe_slug,
                        'date': latest_date.strftime('%d. %B %Y')
                    }
        except Exception as e:
            print(f"  -> Advarsel: Kunne ikke læse data fra '{os.path.basename(recipe_file)}': {e}")

    # Håndter ental/flertal for opskrifter
    num_recipes = len(recipe_files)
    recipe_text = "opskrift" if num_recipes == 1 else "opskrifter"
    recipe_count_string = f"Siden indeholder i øjeblikket **{num_recipes} {recipe_text}**."
    
    # Byg Markdown-indholdet
    markdown_content = f"""---
title: "Ditz3n's Ninja CREAMi Laboratorium"
date: "2025-08-19"
lastmod: "{now_date}"
layout: "home"
hero_image: "front_page.png"
---

## Om Siden
En samling af mine personligt testede og godkendte Ninja CREAMi-opskrifter. Målet er at bygge en database af teknisk velfunderede opskrifter, der fokuserer på de vigtige metrikker som FPDF og MSNF for at sikre et perfekt resultat hver gang.

{recipe_count_string}
"""

    # Shortcode generering
    if latest_recipe:
        slug = latest_recipe['slug']
        title = latest_recipe['title']
        date = latest_recipe['date']
        
        markdown_content += f'\n{{{{< latestRecipe slug="{slug}" title="{title}" date="{date}" >}}}}\n'

    markdown_content += """
## Hvordan Siden Bruges
Brug menuen i toppen til at navigere til **Opskrifter**, den interaktive **Udregner**, **Stabilizer**-blandingen eller den komplette **Ingrediensdatabase**. Hver sektion er designet til at give dig de værktøjer og den viden, du skal bruge i dit eget is-laboratorium. Hvis du støder på tekniske termer, du ikke kender, kan du finde en fuld forklaring i vores nye [**Ordliste**](/glossary/).

## Hvordan Den Er Bygget
Denne hjemmeside er bygget med **Hugo**, et lynhurtigt værktøj til at generere statiske sider. Kernen i siden er en centraliseret Excel-fil (`laboratorie_data.xlsx`), som indeholder al data om ingredienser.

Et specialskrevet **Python-script** (med `pandas`) læser denne data og genererer automatisk alle kernesiderne, inklusiv den `ingredients.json`-fil, som den interaktive udregner bruger. Hele processen – fra opdatering af data til publicering af nye opskrifter – er fuldt automatiseret via **GitHub Actions**.
"""

    changed = write_if_changed(homepage_path, markdown_content)
    if not changed:
        print("  -> Ingen ændringer påkrævet. Alt er up-to-date.")

# ---- ORDLISTE GENERATOR ----
def generate_glossary_page():
    """Genererer den statiske side for Ordlisten."""
    print("\nGenererer Ordliste side...")
    
    glossary_page_path = os.path.join(CONTENT_DIR, 'glossary', 'index.md')
    now_date = datetime.now().strftime('%Y-%m-%d')

    existing_date = get_existing_date(glossary_page_path)
    creation_date = existing_date if existing_date else now_date

    markdown_content = f"""---
title: "Ordliste"
date: {creation_date}
lastmod: {now_date}
layout: "glossary"
toc: true
---

En oversigt over de vigtigste tekniske termer og koncepter, der bruges på denne side til at opnå de perfekte is.

## MSNF (Milk Solids-Not-Fat)
**Mælketørstof uden fedt**

MSNF, også kendt som "fedtfrit mælketørstof", dækker over alle de faste komponenter i mælk, undtagen fedt og vand. Dette inkluderer primært proteiner (kasein og valle) og laktose (mælkesukker) samt mineraler. MSNF er afgørende for isens tekstur, krop og modstandsdygtighed over for smeltning.

For lidt MSNF kan give en is, der føles tynd, vandet og iset. For meget kan føre til en sandet tekstur på grund af krystallisering af laktose.

#### Retningslinjer for MSNF %
Den optimale procentdel af MSNF afhænger af istypen og dens fedtindhold. Her er nogle generelle retningslinjer, du kan sigte efter baseret på de **samlede procenter** i din færdige opskrift:

| Istype | Typisk Fedt %<sup>1</sup> | Anbefalet MSNF %<sup>2</sup> | Noter |
|:---|:---:|:---:|:---|
| Sorbet | 0% | 0 - 2% | Typisk ingen mælkeprodukter. Lidt MSNF kan forbedre teksturen. |
| Fedtfattig Is / Protein-is | 0 - 4% | 10 - 14% | Højere MSNF er nødvendigt for at kompensere for den manglende struktur fra fedt. |
| Klassisk Is / Gelato | 4 - 9% | 8 - 11% | Den gyldne standard, der balancerer cremethed og tekstur. |
| Fedtrig Is (Premium) | 10 - 16%+ | 7 - 9% | Lavere MSNF er nødvendigt for at undgå sandethed, da det høje fedtindhold allerede giver masser af krop. |

<div class="footnote-container">

1.  **Typisk Fedt %:** Procentdelen af fedt i den **samlede opskrift**.  
    *Formel:* `(Total Fedt (g) / Total Vægt (g)) * 100`  
    *Eksempel:* `(15g fedt / 500g total) * 100 = 3%`

2.  **Anbefalet MSNF %:** Procentdelen af MSNF i den **samlede opskrift**.  
    *Formel:* `((Total Kulhydrater (g) + Total Protein (g)) / Total Vægt (g)) * 100`  
    *Eksempel:* `((80g kulhydrat + 40g protein) / 500g total) * 100 = 24%`

</div>

## PAC / FPDF (Potere Anti Congelante / Freezing Point Depression Factor)
**Frysepunktsnedsættende Faktor**

PAC (italiensk) og FPDF (engelsk) er to navne for det samme: et mål for, hvor meget en ingrediens sænker vands frysepunkt. Alle opløselige stoffer (især sukkerarter, salte og alkoholer) bidrager til at sænke frysepunktet.

Dette er den vigtigste faktor for isens "scoopabilitet" direkte fra fryseren. En højere samlet PAC-værdi giver en blødere is ved en given temperatur.

- **Sukrose (alm. sukker)** har en referenceværdi på **100**.
- **Dextrose** er næsten dobbelt så effektiv (PAC **~175**).
- **Salt** er ekstremt potent (PAC **~590**).

For en standard fryser ved -18°C sigtes der typisk efter en samlet PAC-værdi på **24-28** for mælkebaseret is og **30-36** for sorbet for at opnå en god konsistens.

## POD (Potere Dolcificante)
**Sødningskraft**

POD er et mål for en ingrediens' sødme relativt til sukrose (alm. sukker), som har en referenceværdi på **100**. For eksempel har dextrose en POD på ca. **70**, hvilket betyder, at den er mindre sød end sukker. Ved at kombinere forskellige sukkerarter kan man justere PAC (blødhed) og POD (sødme) uafhængigt af hinanden.

## Dextrose-ækvivalent (DE)
Et mål for mængden af reducerende sukkerarter i et sukkerprodukt (f.eks. glukosesirup), udtrykt som en procentdel i forhold til ren dextrose. En høj DE-værdi (tæt på 100) indikerer en sirup, der primært består af simple sukkerarter (som dextrose), hvilket giver høj PAC og sødme. En lav DE-værdi indikerer en sirup med flere komplekse kulhydrater (stivelse), som bidrager mere til krop og tekstur end til blødhed og sødme.

## Emulgatorer & Stabilisatorer
- **Emulgatorer** (f.eks. æggeblomme, lecithin, GMS) er stoffer, der hjælper med at binde fedt og vand sammen. Dette skaber en mere homogen og stabil emulsion, hvilket resulterer i en glattere tekstur og forhindrer fedtet i at klumpe sammen under frysning.
- **Stabilisatorer** (f.eks. guargummi, xanthangummi, LBG) er hydrokolloider, der er ekstremt gode til at binde vand. De forhindrer dannelsen af store iskrystaller under frysning og genfrysning, hvilket giver en mere cremet mundfølelse og forbedrer isens holdbarhed.
"""

    changed = write_if_changed(glossary_page_path, markdown_content)
    if not changed:
        print("  -> Ingen ændringer påkrævet. Alt er up-to-date.")

# ---- UDREGNER GENERATOR ----
def generate_calculator_page():
    """Genererer den statiske side for den interaktive udregner."""
    print("\nGenererer Interaktiv Udregner side...")
    
    existing_date = get_existing_date(CALCULATOR_PAGE_PATH)
    now_date = datetime.now().strftime('%Y-%m-%d')
    creation_date = existing_date if existing_date else now_date
    
    markdown_content = f"""---
title: "Interaktiv Opskrift Udregner"
date: {creation_date}
lastmod: {now_date}
layout: "calculator"
---

Velkommen til siden hvor du kan bygge dine egne Ninja CREAMi-opskrifter fra bunden!

Vælg ingredienser fra databasen, indtast mængder, og se øjeblikkeligt hvordan det påvirker FPDF og MSNF. Samtidigt kan du også få et overblik over præcis det næringsindhold din bøtte indeholder.

God fornøjelse i is-laboratoriet!
"""
    
    changed = write_if_changed(CALCULATOR_PAGE_PATH, markdown_content)
    if not changed:
        print("  -> Ingen ændringer påkrævet. Alt er up-to-date.")

# ---- INGREDIENS GENERATOR ----
def generate_ingredients_page():
    """Genererer Ingrediens-siden fra Excel."""
    print("\nGenererer Ingrediens-siden fra Excel...")
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Ingrediensdatabase', skiprows=11, header=None)
        df.dropna(how='all', inplace=True)
    except Exception as e:
        print(f"  ❌ FEJL! {e}")
        return

    existing_date = get_existing_date(INGREDIENTS_PAGE_PATH)
    now_date = datetime.now().strftime('%Y-%m-%d')
    creation_date = existing_date if existing_date else now_date

    markdown_content = f"""---
title: "Den Komplette Ingrediensdatabase"
date: {creation_date}
lastmod: {now_date}
---

Dette ark er hjertet og den absolutte grundsten i dit is-laboratorium. Det er den centrale kilde, hvorfra "Opskrift Udregneren" henter al sin viden.
"""
    
    for index, row in df.iterrows():
        if str(row.iloc[0]).strip() == 'Ingrediens':
            markdown_content += "\n| Ingrediens | Energi (kcal) | Fedt | Kulh. | Sukker | Protein | Salt | PAC | MSNF | HF | Kommentar |\n"
            markdown_content += "|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|\n"
        elif pd.notna(row.iloc[0]) and row.iloc[1:].isnull().all():
            markdown_content += f"\n## {row.iloc[0]}\n\n"
        elif pd.notna(row.iloc[0]):
            row = row.fillna('')
            markdown_content += (
                f"| {row.iloc[0]} | {row.iloc[1]} | {row.iloc[2]} | {row.iloc[3]} | "
                f"{row.iloc[4]} | {row.iloc[5]} | {row.iloc[6]} | {row.iloc[7]} | "
                f"{row.iloc[8]} | {row.iloc[9]} | {row.iloc[10]} |\n"
            )

    changed = write_if_changed(INGREDIENTS_PAGE_PATH, markdown_content)
    if not changed:
        print("  -> Ingen ændringer påkrævet. Alt er up-to-date.")

# ---- STABILIZER GENERATOR ----
def generate_stabilizer_page():
    """Genererer Stabilizer Mix side fra Excel."""
    print("\nGenererer Stabilizer Mix side fra Excel...")
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Stabilizer Mix', skiprows=20)
        df.dropna(how='all', inplace=True)

        ingredients_df = df[df['Ingrediens'] != 'Total:'].copy()
        total_df = df[df['Ingrediens'] == 'Total:'].copy()

        def build_markdown_table(dataframe):
            header = "| " + " | ".join(dataframe.columns) + " |"
            separator = "|:---|:---|" + ":---:|" * (len(dataframe.columns) - 2)
            body_rows = []
            for _, row in dataframe.iterrows():
                processed_row = []
                for i, cell in enumerate(row):
                    if i == 0:
                        processed_row.append(str(cell).replace('nan', ''))
                    else:
                        if pd.isna(cell) or cell == '' or str(cell) == 'nan':
                            processed_row.append('')
                        else:
                            try:
                                num_value = float(str(cell).replace(',', '.'))
                                formatted_value = f"{num_value:.1f}"
                                if formatted_value.endswith('.0'):
                                    formatted_value = formatted_value[:-2]
                                processed_row.append(formatted_value)
                            except (ValueError, TypeError):
                                processed_row.append(str(cell).replace(',', '.').replace('nan', ''))
                body_rows.append("| " + " | ".join(processed_row) + " |")
            return "\n".join([header, separator] + body_rows)

        ingredients_table = build_markdown_table(ingredients_df)
        total_table = build_markdown_table(total_df)

    except Exception as e:
        print(f"  ❌ FEJL! Stabilizer Mix: {e}")
        return

    # Tjek for billede
    image_filename = None
    static_images_dir = os.path.join(BASE_DIR, 'static', 'images')
    os.makedirs(static_images_dir, exist_ok=True)

    if os.path.exists(os.path.join(static_images_dir, 'stabilizer.jpg')):
        image_filename = 'stabilizer.jpg'
    elif os.path.exists(os.path.join(static_images_dir, 'stabilizer.png')):
        image_filename = 'stabilizer.png'

    existing_date = get_existing_date(STABILIZER_PAGE_PATH)
    now_date = datetime.now().strftime('%Y-%m-%d')
    creation_date = existing_date if existing_date else now_date

    front_matter = f"""---
title: "Ditz3n Stabilizer Mix"
date: {creation_date}
lastmod: {now_date}
showReadingTime: false
layout: "stabilizer"
"""
    
    if image_filename:
        front_matter += f'image: "{image_filename}"\n'
    
    front_matter += "---\n"

    markdown_content = front_matter + f"""
At lave denne blanding handler om præcision og om at undgå klumper. Følg disse trin, og du vil have succes hver gang.

### Ingredienser
{ingredients_table}

### Totaler
{total_table}

### Nødvendigt udstyr:
- En præcis digitalvægt (en juvelérvægt, der kan måle 0.01g, er ideel til de små mængder gummi).
- Et rent, tørt glas med et tætsluttende låg (f.eks. et stort syltetøjsglas).

### Trin-for-trin guide:
1.  **Afvej de store ingredienser:** Start med at afveje de "store" pulvere direkte ned i dit tørre glas. Først 100g Erythritol og derefter 100g Inulin.
2.  **Afvej de små ingredienser:** Nu kommer det vigtigste. Afvej de små, men potente ingredienser: 10g CMC, 3,5g Guargummi, 1,0g Xanthangummi og 3,5g Salt. Tilføj dem oven på de store pulvere i glasset.
3.  **Den vigtige tørblanding:** Sæt låget på glasset og sørg for, at det er helt tæt. Ryst nu glasset kraftigt i 30-60 sekunder. Dette trin er altafgørende. Formålet er at fordele de små gummi-partikler (CMC, guar, xanthan) jævnt mellem de større krystaller af erythritol og inulin. Dette forhindrer dem i at klistre sammen og danne uopløselige klumper, når de rammer væske. Blandingen skal se helt homogen og ensartet ud.

### Opbevaring:
Din "Ditz3n Stabilizer Mix" er nu klar. Opbevar den i det tætsluttende glas ved stuetemperatur. Den er nu en potent alt-i-én ingrediens.

### Sådan bruger du den:
Når din Ninja CREAMi-opskrift kræver sødning og stabilisering, skal du blot afveje den anbefalede mængde af din nye blanding (f.eks. 30g for en Deluxe pint) og tilføje den til dine andre tørre ingredienser (som proteinpulver), før du pisker det hele sammen med dine våde ingredienser (mælk, vand osv.).

Ved at lave denne blanding på forhånd, har du fjernet besværet og usikkerheden ved at skulle afveje små, flyvske mængder gummi hver eneste gang. Det gør hele processen hurtigere, nemmere og langt mere præcis. 😇
"""
    
    changed = write_if_changed(STABILIZER_PAGE_PATH, markdown_content)
    if not changed:
        print("  -> Ingen ændringer påkrævet. Alt er up-to-date.")

# ---- JSON DATABASE GENERATOR ----
def generate_ingredients_json():
    """Genererer ingrediens JSON-database fra Excel."""
    print("\nGenererer ingrediens JSON-database fra Excel...")
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Ingrediensdatabase', skiprows=11, header=None)
        df.dropna(how='all', inplace=True)
        
        # Find header row
        header_row_index = None
        for i, row in df.iterrows():
            if 'Ingrediens' in str(row.iloc[0]):
                header_row_index = i
                break
        
        if header_row_index is None:
            print("❌ FEJL! Kunne ikke finde header-rækken")
            return
        
        # Set column names og fjern header rows
        df.columns = df.iloc[header_row_index].fillna('').astype(str).str.strip().tolist()
        df = df.iloc[header_row_index + 1:].reset_index(drop=True)
        
        # Clean up data
        df.dropna(how='all', inplace=True)
        df = df[~df.iloc[:, 1:].isnull().all(axis=1)]
        df = df[df['Ingrediens'].astype(str).str.strip() != '']
        
        # Convert numeric columns
        numeric_cols = ['Energi (kcal)', 'Fedt', 'Kulhydrater', 'Sukker', 'Protein', 'Salt', 'PAC', 'MSNF', 'HF']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
        
        # Tjek om filen allerede eksisterer og sammenlign
        old_ingredient_count = 0
        if os.path.exists(JSON_OUTPUT_PATH):
            try:
                with open(JSON_OUTPUT_PATH, 'r', encoding='utf-8') as f:
                    import json
                    old_data = json.load(f)
                    old_ingredient_count = len(old_data)
            except:
                old_ingredient_count = 0
        
        # Gem ny JSON
        df.to_json(JSON_OUTPUT_PATH, orient='records', indent=2, force_ascii=False)
        
        new_ingredient_count = len(df)
        
        if old_ingredient_count == 0:
            ingredient_text = "ingrediens" if new_ingredient_count == 1 else "ingredienser"
            print(f"  ✅ Success! 'ingredients.json' genereret med {new_ingredient_count} {ingredient_text}.")
        elif new_ingredient_count == old_ingredient_count:
            print("  -> Ingen ændringer påkrævet. Alt er up-to-date.")
        else:
            added_count = new_ingredient_count - old_ingredient_count
            if added_count > 0:
                ingredient_text = "ingrediens" if added_count == 1 else "ingredienser"
                ny_text = "ny" if added_count == 1 else "nye"
                print(f"  ✅ Success! 'ingredients.json' opdateret - {added_count} {ny_text} {ingredient_text} tilføjet (total: {new_ingredient_count}).")
            else:
                removed_count = abs(added_count)
                ingredient_text = "ingrediens" if removed_count == 1 else "ingredienser"
                print(f"  ✅ Success! 'ingredients.json' opdateret - {removed_count} {ingredient_text} fjernet (total: {new_ingredient_count}).")

    except Exception as e:
        print(f"  ❌ FEJL! JSON generering: {e}")

# ---- OPSKRIFT PROCESSOR ----
def process_pending_recipes():
    """Finder, behandler og publicerer nye opskrifter fra 'pending_recipes'-mappen."""
    print("\nScanner efter nye opskrifter i 'pending_recipes'...")
    
    pending_dir = os.path.join(BASE_DIR, 'scripts', 'pending_recipes')
    os.makedirs(pending_dir, exist_ok=True)

    pending_files = glob.glob(os.path.join(pending_dir, '*.md'))
    actual_recipe_files = [f for f in pending_files if os.path.basename(f).lower() != 'readme.md']

    if not actual_recipe_files:
        print("  -> Ingen nye opskrifter fundet (kun README.md). Alt er up-to-date.")
        return

    print(f"Fandt {len(actual_recipe_files)} ny(e) opskrift(er). Starter publicering...")
    processed_count = 0

    for md_file_path in actual_recipe_files:
        try:
            # Læs indhold og find titel
            with open(md_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines or not lines[0].startswith('# '):
                print(f"  ⚠️ ADVARSEL: Filen '{os.path.basename(md_file_path)}' har ikke en valid titel. Springer over.")
                continue

            recipe_title = lines[0].replace('# ', '').strip()
            recipe_content = "".join(lines[1:])

            # Find ALLE tilhørende billeder
            base_filename = os.path.splitext(os.path.basename(md_file_path))[0]
            found_images = []
            
            # Søg efter hovedbillede
            for ext in ['jpg', 'jpeg', 'png', 'webp']:
                potential_image = os.path.join(pending_dir, f"{base_filename}.{ext}")
                if os.path.exists(potential_image):
                    found_images.append(os.path.basename(potential_image))
                    break
            
            # Søg efter nummererede billeder
            image_counter = 1
            while True:
                found_numbered = False
                for ext in ['jpg', 'jpeg', 'png', 'webp']:
                    potential_numbered = os.path.join(pending_dir, f"{base_filename}{image_counter}.{ext}")
                    if os.path.exists(potential_numbered):
                        found_images.append(os.path.basename(potential_numbered))
                        found_numbered = True
                        break
                
                if not found_numbered:
                    break
                image_counter += 1
            
            # Byg den nye fil med Front Matter
            now_date = datetime.now().strftime('%Y-%m-%d')
            front_matter = f"""---
title: "{recipe_title}"
date: {now_date}
lastmod: {now_date}
layout: "recipes"
"""
            
            # Tilføj billeder til front matter
            if len(found_images) == 1:
                front_matter += f'image: "{found_images[0]}"\n'
            elif len(found_images) > 1:
                front_matter += 'images:\n'
                for img in found_images:
                    front_matter += f'  - "{img}"\n'
            
            front_matter += "---\n"
            final_content = front_matter + recipe_content

            # Opret mappe og gem den nye index.md
            clean_title = recipe_title.split('(')[0].strip()
            recipe_slug = clean_title.lower().replace(' ', '_').replace('æ', 'ae').replace('ø', 'oe').replace('å', 'aa')
            new_recipe_dir = os.path.join(RECIPE_CONTENT_DIR, recipe_slug)
            os.makedirs(new_recipe_dir, exist_ok=True)

            destination_md_path = os.path.join(new_recipe_dir, 'index.md')
            with open(destination_md_path, 'w', encoding='utf-8') as f:
                f.write(final_content)

            # Flyt ALLE billeder og slet den gamle .md
            for image_filename in found_images:
                source_image_path = os.path.join(pending_dir, image_filename)
                destination_image_path = os.path.join(new_recipe_dir, image_filename)
                shutil.move(source_image_path, destination_image_path)
                print(f"     -> Fandt og flytter billede: '{image_filename}'")

            os.remove(md_file_path)
            
            if found_images:
                print(f"  -> Behandlet: '{clean_title}' (med {len(found_images)} billede(r))")
            else:
                print(f"  -> Behandlet: '{clean_title}' (ingen billeder)")
            processed_count += 1

        except Exception as e:
            print(f"  ❌ FEJL under behandling af '{os.path.basename(md_file_path)}': {e}")

    if processed_count > 0:
        print(f"  ✅ Success! {processed_count} ny(e) opskrift(er) er blevet publiceret.")

# ---- HOVEDPROGRAM ----
if __name__ == "__main__":
    generate_homepage()
    generate_glossary_page()
    generate_calculator_page()
    generate_stabilizer_page()
    generate_ingredients_page()
    generate_ingredients_json()
    process_pending_recipes()  
    
    print("\n✅ Alle opgaver er fuldført! Du kan nu køre 'hugo server'.")