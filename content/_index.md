---
title: "Ditz3n's Ninja CREAMi Laboratorium"
date: "2025-08-19"
lastmod: "2025-09-05"
layout: "home"
hero_image: "front_page.png"
---

## Om Siden
En samling af mine personligt testede og godkendte Ninja CREAMi-opskrifter. Målet er at bygge en database af teknisk velfunderede opskrifter, der fokuserer på de vigtige metrikker som FPDF og MSNF for at sikre et perfekt resultat hver gang.

Siden indeholder i øjeblikket **0 opskrifter**.

## Hvordan Siden Bruges
Brug menuen i toppen til at navigere til **Opskrifter**, den interaktive **Udregner**, **Stabilizer**-blandingen eller den komplette **Ingrediensdatabase**. Hver sektion er designet til at give dig de værktøjer og den viden, du skal bruge i dit eget is-laboratorium. Hvis du støder på tekniske termer, du ikke kender, kan du finde en fuld forklaring i vores nye [**Ordliste**](/glossary/).

## Hvordan Den Er Bygget
Denne hjemmeside er bygget med **Hugo**, et lynhurtigt værktøj til at generere statiske sider. Kernen i siden er en centraliseret Excel-fil (`laboratorie_data.xlsx`), som indeholder al data om ingredienser.

Et specialskrevet **Python-script** (med `pandas`) læser denne data og genererer automatisk alle kernesiderne, inklusiv den `ingredients.json`-fil, som den interaktive udregner bruger. Hele processen – fra opdatering af data til publicering af nye opskrifter – er fuldt automatiseret via **GitHub Actions**.
