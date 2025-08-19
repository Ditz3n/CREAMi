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

# Output paths
CALCULATOR_PAGE_PATH = os.path.join(CONTENT_DIR, 'calculator', 'index.md')
STABILIZER_PAGE_PATH = os.path.join(CONTENT_DIR, 'stabilizer', 'index.md')
INGREDIENTS_PAGE_PATH = os.path.join(CONTENT_DIR, 'ingredients', '_index.md')
JSON_OUTPUT_PATH = os.path.join(BASE_DIR, 'static', 'ingredients.json')
RECIPE_CONTENT_DIR = os.path.join(CONTENT_DIR, 'recipes')

# ---- HJÆLPEFUNKTION TIL AT SKRIVE FILER KUN VED ÆNDRINGER ----
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
    print(f"✅ Success! '{os.path.basename(filepath)}' er blevet genereret/opdateret!")
    return True

# ---- HJÆLPEFUNKTION TIL AT HENTE EXISTING DATE ----
def get_existing_date(filepath):
    """
    Læser en markdown-fil og returnerer 'date'-værdien fra front matter, hvis den findes.
    Returnerer None, hvis filen ikke findes, eller datoen ikke kan findes.
    """
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
                # Vi har nået slutningen af front matter
                break
            elif in_front_matter:
                # Finder linjen, der starter med 'date:'
                match = re.match(r'^date:\s*"?([^"\s]+)"?', line)
                if match:
                    return match.group(1)
    except FileNotFoundError:
        return None
    return None

# ---- GENERER UDREGNER-SIDEN ----
def generate_calculator_page():
    """
    Genererer den statiske side for den interaktive udregner.
    """
    print("\nGenererer Interaktiv Udregner side...")
    
    # Hent den eksisterende oprettelsesdato, hvis filen findes
    existing_date = get_existing_date(CALCULATOR_PAGE_PATH)
    now_date = datetime.now().strftime('%Y-%m-%d')

    # Brug den gamle dato, hvis den findes, ellers brug dags dato
    creation_date = existing_date if existing_date else now_date
    
    # Byg indholdet med den korrekte dato
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
    write_if_changed(CALCULATOR_PAGE_PATH, markdown_content)
    print("✅ Success! Interaktiv Udregner siden er blevet genereret!")

# ---- INGREDIENS-SIDEN ----
def generate_ingredients_page():
    print("\nGenererer Ingrediens-siden fra Excel...")
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Ingrediensdatabase', skiprows=11, header=None)
        df.dropna(how='all', inplace=True)
    except Exception as e:
        print(f"❌ FEJL! {e}")
        return

    # Hent den eksisterende oprettelsesdato, hvis filen findes
    existing_date = get_existing_date(INGREDIENTS_PAGE_PATH)
    now_date = datetime.now().strftime('%Y-%m-%d')

    # Brug den gamle dato, hvis den findes, ellers brug dags dato
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

    write_if_changed(INGREDIENTS_PAGE_PATH, markdown_content)
    print("✅ Success! Ingrediens-siden er blevet genereret!")

# ---- STABILIZER SIDEN ----
def generate_stabilizer_page():
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
                    if i == 0:  # First column (Ingrediens) - keep as string
                        processed_row.append(str(cell).replace('nan', ''))
                    else:  # Numeric columns - format to 1 decimal place
                        if pd.isna(cell) or cell == '' or str(cell) == 'nan':
                            processed_row.append('')
                        else:
                            try:
                                # Convert to float and format to 1 decimal place
                                num_value = float(str(cell).replace(',', '.'))
                                formatted_value = f"{num_value:.1f}"
                                # Remove trailing .0 for whole numbers
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
        print(f"❌ FEJL! Stabilizer Mix: {e}")
        return

     # --- LOGIK TIL AT FINDE BILLEDE ---
    image_filename = None
    static_images_dir = os.path.join(BASE_DIR, 'static', 'images')
    
    # Tjek om mappen 'static/images' findes, opret den hvis ikke
    os.makedirs(static_images_dir, exist_ok=True)

    if os.path.exists(os.path.join(static_images_dir, 'stabilizer.jpg')):
        image_filename = 'stabilizer.jpg'
    elif os.path.exists(os.path.join(static_images_dir, 'stabilizer.png')):
        image_filename = 'stabilizer.png'

    # Hent den eksisterende oprettelsesdato, hvis filen findes
    existing_date = get_existing_date(STABILIZER_PAGE_PATH)
    now_date = datetime.now().strftime('%Y-%m-%d')

    # Brug den gamle dato, hvis den findes, ellers brug dags dato
    creation_date = existing_date if existing_date else now_date

    # Byg front matter dynamisk
    front_matter = f"""---
title: "Ditz3n Stabilizer Mix"
date: {creation_date}
lastmod: {now_date}
showReadingTime: false
layout: "stabilizer"
"""
    # Tilføj kun billedet til front matter, hvis det blev fundet
    if image_filename:
        front_matter += f'image: "{image_filename}"\n'
    
    front_matter += "---\n"

    # Byg resten af sidens indhold
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
    
    write_if_changed(STABILIZER_PAGE_PATH, markdown_content)
    print("✅ Success! Stabilizer Mix siden er blevet genereret!")

# ---- JSON DATABASE ----
def generate_ingredients_json():
    print("\nGenererer ingrediens JSON-database fra Excel...")
    try:
        # Read raw data
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Ingrediensdatabase', skiprows=11, header=None)
        df.dropna(how='all', inplace=True)
        
        # Find header row containing "Ingrediens"
        header_row_index = None
        for i, row in df.iterrows():
            if 'Ingrediens' in str(row.iloc[0]):
                header_row_index = i
                break
        
        if header_row_index is None:
            print("❌ FEJL! Kunne ikke finde header-rækken")
            return
        
        # Set column names and remove header rows
        df.columns = df.iloc[header_row_index].fillna('').astype(str).str.strip().tolist()
        df = df.iloc[header_row_index + 1:].reset_index(drop=True)
        
        # Clean up data
        df.dropna(how='all', inplace=True)
        df = df[~df.iloc[:, 1:].isnull().all(axis=1)]  # Remove section headers
        df = df[df['Ingrediens'].astype(str).str.strip() != '']  # Remove empty ingredients
        
        # Convert numeric columns
        numeric_cols = ['Energi (kcal)', 'Fedt', 'Kulhydrater', 'Sukker', 'Protein', 'Salt', 'PAC', 'MSNF', 'HF']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
        
        # Save to JSON
        df.to_json(JSON_OUTPUT_PATH, orient='records', indent=2, force_ascii=False)
        print(f"✅ Success! 'ingredients.json' genereret med {len(df)} ingredienser.")

    except Exception as e:
        print(f"❌ FEJL! JSON generering: {e}")

# ---- PROCES PENDING OPSKRIFTER ----
def process_pending_recipes():
    """
    Finder, behandler og publicerer nye opskrifter fra 'pending_recipes'-mappen.
    Nu med support for flere billeder (image1.png, image2.jpg, etc.)
    """
    print("\nScanner efter nye opskrifter i 'pending_recipes'...")
    
    pending_dir = os.path.join(BASE_DIR, 'scripts', 'pending_recipes')
    os.makedirs(pending_dir, exist_ok=True)

    pending_files = glob.glob(os.path.join(pending_dir, '*.md'))

    if not pending_files:
        print("Ingen nye opskrifter fundet. Alt er up-to-date.")
        return

    # Filtrer README.md fra listen, før vi tæller
    actual_recipe_files = [f for f in pending_files if os.path.basename(f).lower() != 'readme.md']

    if not actual_recipe_files:
        print("Ingen nye opskrifter fundet (kun README.md). Alt er up-to-date.")
        return

    print(f"Fandt {len(actual_recipe_files)} ny(e) opskrift(er). Starter publicering...")
    processed_count = 0

    for md_file_path in actual_recipe_files:
        try:
            # --- Trin 1: Læs indhold og find titel ---
            with open(md_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines or not lines[0].startswith('# '):
                print(f"⚠️ ADVARSEL: Filen '{os.path.basename(md_file_path)}' har ikke en valid titel. Springer over.")
                continue

            recipe_title = lines[0].replace('# ', '').strip()
            recipe_content = "".join(lines[1:])

            # --- Trin 2: Find ALLE tilhørende billeder ---
            base_filename = os.path.splitext(os.path.basename(md_file_path))[0]
            found_images = []
            
            # Først: søg efter hovedbillede (uden nummer)
            for ext in ['jpg', 'jpeg', 'png', 'webp']:
                potential_image = os.path.join(pending_dir, f"{base_filename}.{ext}")
                if os.path.exists(potential_image):
                    found_images.append(os.path.basename(potential_image))
                    break
            
            # Derefter: søg efter nummererede billeder (1, 2, 3, etc.)
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
            
            # --- Trin 3: Byg den nye fil med Front Matter ---
            now_date = datetime.now().strftime('%Y-%m-%d')
            front_matter = f"""---
title: "{recipe_title}"
date: {now_date}
lastmod: {now_date}
layout: "recipes"
"""
            
            # Tilføj billeder til front matter
            if len(found_images) == 1:
                # Kun ét billede - brug den gamle måde
                front_matter += f'image: "{found_images[0]}"\n'
            elif len(found_images) > 1:
                # Flere billeder - brug array
                front_matter += 'images:\n'
                for img in found_images:
                    front_matter += f'  - "{img}"\n'
            
            front_matter += "---\n"

            final_content = front_matter + recipe_content

            # --- Trin 4: Opret mappe og gem den nye index.md ---
            clean_title = recipe_title.split('(')[0].strip()
            recipe_slug = clean_title.lower().replace(' ', '_').replace('æ', 'ae').replace('ø', 'oe').replace('å', 'aa')
            new_recipe_dir = os.path.join(RECIPE_CONTENT_DIR, recipe_slug)
            os.makedirs(new_recipe_dir, exist_ok=True)

            destination_md_path = os.path.join(new_recipe_dir, 'index.md')
            with open(destination_md_path, 'w', encoding='utf-8') as f:
                f.write(final_content)

            # --- Trin 5: Flyt ALLE billeder og slet den gamle .md ---
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
            print(f"❌ FEJL under behandling af '{os.path.basename(md_file_path)}': {e}")

    if processed_count > 0:
        print(f"✅ Success! {processed_count} ny(e) opskrift(er) er blevet publiceret.")

# ---- HOVEDPROGRAM ----
if __name__ == "__main__":
    generate_calculator_page()
    generate_stabilizer_page()
    generate_ingredients_page()
    generate_ingredients_json()
    process_pending_recipes()  
    
    print("\n✅ Alle opgaver er fuldført! Du kan nu køre 'hugo server'.")