import pandas as pd
import os
import glob
import hashlib
from datetime import datetime
import csv # Importerer CSV-modulet for bedre kontrol

# ---- KONFIGURATION ----
# Sørg for at disse stier passer til din mappestruktur
# Vi antager at scriptet køres fra 'scripts/' mappen
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Går op til roden af projektet
DATA_DIR = os.path.join(BASE_DIR, 'data')
RECIPE_DATA_DIR = os.path.join(DATA_DIR, 'recipes')
CONTENT_DIR = os.path.join(BASE_DIR, 'content')
INGREDIENTS_PAGE_PATH = os.path.join(CONTENT_DIR, 'ingredients', '_index.md')
RECIPE_CONTENT_DIR = os.path.join(CONTENT_DIR, 'recipes')
STABILIZER_PAGE_PATH = os.path.join(CONTENT_DIR, 'stabilizer-mix', 'index.md') # Sti til den nye side

# ---- HJÆLPEFUNKTION TIL AT SKRIVE FILER KUN VED ÆNDRINGER ----
def write_if_changed(filepath, new_content):
    """
    Skriver kun til filen, hvis det nye indhold er forskelligt fra det eksisterende,
    eller hvis filen ikke eksisterer. Returnerer True hvis filen blev skrevet.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    should_write = True
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        # Sammenlign et hash af indholdet for effektivitet
        if hashlib.md5(new_content.encode()).hexdigest() == hashlib.md5(existing_content.encode()).hexdigest():
            should_write = False
            # print(f"'{os.path.basename(filepath)}' er uændret. Springer over.")
    except FileNotFoundError:
        # Filen eksisterer ikke, så vi skal skrive den
        pass

    if should_write:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Success! '{os.path.basename(filepath)}' er blevet genereret/opdateret!")
        return True
    return False

# ---- FUNKTION TIL AT GENERERE INGREDIENS-SIDEN ----
def generate_ingredients_page():
    # ... (din eksisterende funktion - ingen ændringer nødvendige her)
    # For fuldstændighed, tilføjer vi den også til den betingede logik
    print("Starter generering af Ingrediens-siden...")
    db_path = os.path.join(DATA_DIR, 'Ingrediensdatabase.csv')
    try:
        df = pd.read_csv(db_path, skiprows=11, header=None, encoding='utf-8')
        df.dropna(how='all', inplace=True)
    except Exception as e:
        print(f"FEJL under indlæsning af ingrediensdatabase: {e}")
        return

    markdown_content = """---
title: "Den Komplette Ingrediensdatabase"
date: {now}
lastmod: {now}
draft: false
---

Dette ark er hjertet og den absolutte grundsten i dit is-laboratorium. Det er den centrale kilde, hvorfra "Opskrift Udregneren" henter al sin viden.
""".format(now=datetime.now().strftime('%Y-%m-%d'))
    
    # ... resten af din logik for at bygge tabellen ...
    for index, row in df.iterrows():
        if 'Ingrediens' in str(row.iloc[0]):
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


# ---- DEN DEFINITIVE FUNKTION (V2) TIL STABILIZER MIX ----
def generate_stabilizer_page():
    """
    Genererer den dedikerede side for Ditz3n Stabilizer Mix.
    - Bruger pandas til at læse den rene tabelstruktur.
    - Skaber to separate tabeller: en for ingredienser og en for totaler med overskrift.
    - Er simpel, robust og let at vedligeholde.
    """
    print("\nGenererer Ditz3n Stabilizer Mix side (endelig version)...")
    source_file = os.path.join(DATA_DIR, 'Ditz3n_Stabilizer_Mix.csv')
    
    try:
        # Trin 1: Find startlinjen for tabellen.
        # *** ÆNDRING 1: Leder nu efter "Ingrediens" (ental) ***
        header_row_index = 0
        with open(source_file, 'r', encoding='utf-8-sig') as f:
            for i, line in enumerate(f):
                if 'Ingrediens,Mængde (g)' in line:
                    header_row_index = i
                    break
        
        if header_row_index == 0:
            raise ValueError("Kunne ikke finde tabellens header. Tjek CSV-filen.")

        # Trin 2: Læs kun tabel-data ind med pandas.
        df = pd.read_csv(source_file, skiprows=header_row_index, encoding='utf-8')
        df.dropna(how='all', inplace=True)

        # Trin 3: Opdel data i ingredienser og totaler.
        # Bruger den nye kolonne-header "Ingrediens".
        ingredients_df = df[df['Ingrediens'] != 'Total:'].copy()
        total_df = df[df['Ingrediens'] == 'Total:'].copy()

        # Funktion til at bygge en pæn Markdown-tabel fra en DataFrame
        def build_markdown_table(dataframe):
            header = "| " + " | ".join(dataframe.columns) + " |"
            separator = "|:---|:---|" + ":---:|" * (len(dataframe.columns) - 2)
            body_rows = []
            for _, row in dataframe.iterrows():
                processed_row = [str(cell).replace(',', '.').replace('nan', '') for cell in row]
                body_rows.append("| " + " | ".join(processed_row) + " |")
            return "\n".join([header, separator] + body_rows)

        # Trin 4: Byg de to separate tabeller
        ingredients_table = build_markdown_table(ingredients_df)
        total_table = build_markdown_table(total_df)

    except FileNotFoundError:
        print(f"ADVARSEL: Kunne ikke finde '{source_file}'. Siden bliver ikke genereret.")
        return
    except Exception as e:
        print(f"FEJL under læsning af Stabilizer Mix fil: {e}")
        return

    # Trin 5: Sæt det hele sammen til den endelige side
    markdown_content = f"""---
title: "Ditz3n Stabilizer Mix"
date: {datetime.now().strftime('%Y-%m-%d')}
lastmod: {datetime.now().strftime('%Y-%m-%d')}
draft: false
showReadingTime: false
---

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

> Ved at lave denne blanding på forhånd, har du fjernet besværet og usikkerheden ved at skulle afveje små, flyvske mængder gummi hver eneste gang. Det gør hele processen hurtigere, nemmere og langt mere præcis. 😇
"""
    
    write_if_changed(STABILIZER_PAGE_PATH, markdown_content)

# ---- FUNKTION TIL AT GENERERE OPSKRIFTS-SIDER ----
def generate_all_recipe_pages():
    recipe_files = glob.glob(os.path.join(RECIPE_DATA_DIR, '*.csv'))
    if not recipe_files:
        print("\nADVARSEL: Ingen opskrifts-filer fundet i 'data/recipes/'.")
        return
    
    print(f"\nFandt {len(recipe_files)} opskrift(er). Starter generering...")
    for recipe_file in recipe_files:
        filename = os.path.basename(recipe_file)
        recipe_name = os.path.splitext(filename)[0].replace('_', ' ')
        try:
            # ... (eksisterende logik til at læse og parse opskrifter)
            df = pd.read_csv(recipe_file, header=9, encoding='utf-8')
            numeric_cols = df.columns[1:]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.', regex=False), errors='coerce')
            
            total_row = df[df.iloc[:, 0].str.contains('Næringsindhold', na=False)].iloc[0]
            fpdf_row = df[df.iloc[:, 0].str.contains('Samlet FPDF', na=False)].iloc[0]
            msnf_row = df[df.iloc[:, 0].str.contains('MSNF %', na=False)].iloc[0]
            recipe_df = df.dropna(subset=[df.columns[1]])

            # Byg Markdown-indhold
            markdown_content = f"""---
title: "{recipe_name}"
date: {datetime.now().strftime('%Y-%m-%d')}
lastmod: {datetime.now().strftime('%Y-%m-%d')}
draft: false
---

## Nøgle-tal for Opskriften
| Kalorier i alt | FPDF | MSNF % | Protein i alt |
|:---|:---|:---|:---|
| **{total_row.iloc[2]:.0f} kcal** | **{fpdf_row.iloc[1]:.2f}** | **{msnf_row.iloc[1]:.1f}%** | **{total_row.iloc[6]:.1f}g** |

## Ingredienser
| Ingrediens | Mængde (g) |
|:---|---:|
"""
            for index, row in recipe_df.iterrows():
                if not row.iloc[0].startswith(('Næringsindhold', 'Samlet FPDF', 'MSNF %')):
                    markdown_content += f"| {row.iloc[0]} | {row.iloc[1]:.1f}g |\n"

            markdown_content += """
## Fremgangsmåde
*Dette er en standard-skabelon. Juster den efter behov.*

1.  Blend alle ingredienser grundigt.
2.  Hæld i bøtten og frys i minimum 24 timer.
3.  Kør på det relevante program.
"""
            # Definer output sti
            output_dir = os.path.join(RECIPE_CONTENT_DIR, recipe_name.replace(' ', '_'))
            output_path = os.path.join(output_dir, 'index.md')
            
            # Brug den nye smarte funktion til at skrive filen
            write_if_changed(output_path, markdown_content)

        except Exception as e:
            print(f"FEJL under generering af '{recipe_name}': {e}")


# ---- HOVED-BLOK: KØR HELE SYSTEMET ----
if __name__ == "__main__":
    generate_ingredients_page()
    generate_stabilizer_page() # <-- KALD TIL DEN NYE FUNKTION
    generate_all_recipe_pages()
    print("\nAlle sider er blevet tjekket og eventuelt opdateret. Du er klar til at køre 'hugo server'.")