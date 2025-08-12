document.addEventListener('DOMContentLoaded', () => {
    let ingredientsData = [];
    let customIngredients = {}; // Opbevar brugerdefinerede ingredienser
    const ingredientsTbody = document.getElementById('ingredients-tbody');
    const datalist = document.getElementById('ingredient-options');

    // Initialiseringsfunktion
    async function init() {
        try {
            const response = await fetch(siteBaseURL + 'ingredients.json');
            ingredientsData = await response.json();
            populateDatalist();
            setupInitialRows();
            setupEventListeners();
            createModal(); // Opret modal når siden indlæses
        } catch (error) {
            console.error('Kunne ikke indlæse ingrediens-database:', error);
        }
    }

    function populateDatalist() {
        ingredientsData.forEach(ing => {
            const option = document.createElement('option');
            option.value = ing.Ingrediens;
            datalist.appendChild(option);
        });
    }

    function createRow() {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div class="ingredient-input-container">
                    <input type="text" list="ingredient-options" class="ingredient-input" placeholder="Søg efter ingrediens...">
                    <button type="button" class="manual-input-btn hidden" title="Indtast næringsværdier manuelt">!</button>
                </div>
            </td>
            <td><input type="number" class="quantity-input" placeholder="0" min="0"></td>
        `;
        ingredientsTbody.appendChild(tr);
        setupRowEventListeners(tr);
    }

    function setupRowEventListeners(row) {
        const ingredientInput = row.querySelector('.ingredient-input');
        const manualBtn = row.querySelector('.manual-input-btn');

        // Vis/skjul manual knap baseret på om ingrediensen findes
        ingredientInput.addEventListener('input', () => {
            const value = ingredientInput.value.trim();
            const exists = ingredientsData.some(ing => ing.Ingrediens === value) || customIngredients[value];
            
            if (value && !exists) {
                manualBtn.style.display = 'flex';
            } else {
                manualBtn.style.display = 'none';
            }
        });

        // Åbn modal når der klikkes på udråbstegnet
        manualBtn.addEventListener('click', () => {
            openModal(row);
        });
    }

    function createModal() {
        const modalHTML = `
            <div id="nutrition-modal" class="modal-overlay" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Indtast Næringsindhold per 100g</h3>
                        <button type="button" class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="ingredient-name-display">
                            <strong>Ingrediens:</strong> <span id="modal-ingredient-name"></span>
                        </div>
                        
                        <div class="lactose-free-option">
                            <label>
                                <input type="checkbox" id="modal-lactose-free-checkbox"> 
                                Laktosefrit produkt (højere PAC-værdi)
                            </label>
                        </div>

                        <div class="nutrition-grid">
                            <div class="nutrition-row">
                                <label>Energi (kcal):</label>
                                <input type="number" id="modal-energy" min="0" placeholder="0">
                            </div>
                            <div class="nutrition-row">
                                <label>Fedt (g):</label>
                                <input type="number" id="modal-fat" min="0" step="0.1" placeholder="0">
                            </div>
                            <div class="nutrition-row">
                                <label>Kulhydrater (g):</label>
                                <input type="number" id="modal-carbs" min="0" step="0.1" placeholder="0">
                            </div>
                            <div class="nutrition-row">
                                <label>Sukker (g):</label>
                                <input type="number" id="modal-sugar" min="0" step="0.1" placeholder="0">
                            </div>
                            <div class="nutrition-row">
                                <label>Protein (g):</label>
                                <input type="number" id="modal-protein" min="0" step="0.1" placeholder="0">
                            </div>
                            <div class="nutrition-row">
                                <label>Salt (g):</label>
                                <input type="number" id="modal-salt" min="0" step="0.1" placeholder="0">
                            </div>
                        </div>

                        <div class="calculated-values">
                            <h4>Beregnede værdier:</h4>
                            <div class="calc-grid">
                                <div>PAC: <strong><span id="modal-calc-pac">0.0</span></strong></div>
                                <div>MSNF: <strong><span id="modal-calc-msnf">0.0</span></strong></div>
                                <div>HF: <strong><span id="modal-calc-hf">0.0</span></strong></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="modal-footer">
                        <button type="button" id="modal-save-btn" class="save-btn">Gem Ingrediens</button>
                        <button type="button" id="modal-cancel-btn" class="cancel-btn">Annuller</button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        setupModalEventListeners();
    }

    function setupModalEventListeners() {
        const modal = document.getElementById('nutrition-modal');
        const closeBtn = document.querySelector('.modal-close');
        const cancelBtn = document.getElementById('modal-cancel-btn');
        const saveBtn = document.getElementById('modal-save-btn');
        const inputs = modal.querySelectorAll('input[type="number"]');
        const lactoseFreeCheckbox = document.getElementById('modal-lactose-free-checkbox');

        // Luk modal ved klik på X eller Annuller
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        
        // Luk modal ved klik udenfor
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });

        // Luk modal med Escape-tasten
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.style.display !== 'none') {
                closeModal();
            }
        });

        // Auto-beregning når værdier ændres
        inputs.forEach(input => {
            input.addEventListener('input', updateModalCalculations);
        });
        
        lactoseFreeCheckbox.addEventListener('change', updateModalCalculations);

        // Gem ingrediens
        saveBtn.addEventListener('click', saveFromModal);
    }

    function openModal(row) {
        const modal = document.getElementById('nutrition-modal');
        const ingredientName = row.querySelector('.ingredient-input').value.trim();
        
        // Sæt ingrediensnavn
        document.getElementById('modal-ingredient-name').textContent = ingredientName;
        
        // Nulstil alle felter
        modal.querySelectorAll('input[type="number"]').forEach(input => input.value = '');
        document.getElementById('modal-lactose-free-checkbox').checked = false;
        
        // Nulstil beregnede værdier
        document.getElementById('modal-calc-pac').textContent = '0.0';
        document.getElementById('modal-calc-msnf').textContent = '0.0';
        document.getElementById('modal-calc-hf').textContent = '0.0';
        
        // Gem reference til den aktuelle række
        modal.dataset.currentRow = Array.from(ingredientsTbody.querySelectorAll('tr')).indexOf(row);
        
        // Vis modal
        modal.style.display = 'flex';
        
        // Focus på første input
        document.getElementById('modal-energy').focus();
    }

    function closeModal() {
        const modal = document.getElementById('nutrition-modal');
        modal.style.display = 'none';
    }

    function updateModalCalculations() {
        const energy = parseFloat(document.getElementById('modal-energy').value) || 0;
        const fat = parseFloat(document.getElementById('modal-fat').value) || 0;
        const carbs = parseFloat(document.getElementById('modal-carbs').value) || 0;
        const sugar = parseFloat(document.getElementById('modal-sugar').value) || 0;
        const protein = parseFloat(document.getElementById('modal-protein').value) || 0;
        const salt = parseFloat(document.getElementById('modal-salt').value) || 0;
        const isLactoseFree = document.getElementById('modal-lactose-free-checkbox').checked;

        // Beregn PAC baseret på videnskabelige værdier
        let pac;
        if (isLactoseFree) {
            // Laktosefrie produkter: højere PAC pga. alternativ sukkersammensætning
            pac = sugar * 1.9 + (carbs - sugar) * 0.6 + salt * 5.9;
        } else {
            // Standard beregning
            pac = sugar * 1.0 + (carbs - sugar) * 0.5 + salt * 5.9;
        }

        // Beregn MSNF og HF
        const msnf = carbs + protein;
        const hf = fat;

        // Opdater visning
        document.getElementById('modal-calc-pac').textContent = pac.toFixed(1);
        document.getElementById('modal-calc-msnf').textContent = msnf.toFixed(1);
        document.getElementById('modal-calc-hf').textContent = hf.toFixed(1);
    }

    function saveFromModal() {
        const modal = document.getElementById('nutrition-modal');
        const ingredientName = document.getElementById('modal-ingredient-name').textContent;
        const rowIndex = parseInt(modal.dataset.currentRow);
        const row = ingredientsTbody.querySelectorAll('tr')[rowIndex];

        if (!ingredientName.trim()) {
            alert('Ingrediensnavn mangler');
            return;
        }

        // Hent værdier fra modal
        const energy = parseFloat(document.getElementById('modal-energy').value) || 0;
        const fat = parseFloat(document.getElementById('modal-fat').value) || 0;
        const carbs = parseFloat(document.getElementById('modal-carbs').value) || 0;
        const sugar = parseFloat(document.getElementById('modal-sugar').value) || 0;
        const protein = parseFloat(document.getElementById('modal-protein').value) || 0;
        const salt = parseFloat(document.getElementById('modal-salt').value) || 0;
        const isLactoseFree = document.getElementById('modal-lactose-free-checkbox').checked;

        // Beregn værdier
        let pac;
        if (isLactoseFree) {
            pac = sugar * 1.9 + (carbs - sugar) * 0.6 + salt * 5.9;
        } else {
            pac = sugar * 1.0 + (carbs - sugar) * 0.5 + salt * 5.9;
        }
        const msnf = carbs + protein;
        const hf = fat;

        // Gem i brugerdefinerede ingredienser
        customIngredients[ingredientName] = {
            'Ingrediens': ingredientName,
            'Energi (kcal)': energy,
            'Fedt': fat,
            'Kulhydrater': carbs,
            'Sukker': sugar,
            'Protein': protein,
            'Salt': salt,
            'PAC': pac,
            'MSNF': msnf,
            'HF': hf,
            'Kommentar': `Brugerdefineret${isLactoseFree ? ' (laktosefri)' : ''}`
        };

        // Tilføj til datalist hvis den ikke allerede findes
        if (!Array.from(datalist.options).some(option => option.value === ingredientName)) {
            const option = document.createElement('option');
            option.value = ingredientName;
            datalist.appendChild(option);
        }

        // Skjul udråbstegn-knappen nu hvor ingrediensen er gemt
        row.querySelector('.manual-input-btn').style.display = 'none';

        // Luk modal
        closeModal();

        // Genberegn totaler
        calculateAll();

        // Vis success-besked
        alert(`"${ingredientName}" er blevet gemt som brugerdefineret ingrediens!`);
    }

    function setupInitialRows() {
        for (let i = 0; i < 5; i++) {
            createRow();
        }
    }

    function setupAutoResize() {
        // Auto-resize functionality for textareas
        const textareas = document.querySelectorAll('textarea');
        textareas.forEach(textarea => {
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + 'px';
            });
        });
    }

    function updateCalculatorState() {
        const calculatorSections = document.querySelector('.calculator-sections');
        const hasSelection = document.querySelector('input[name="container-size"]:checked');
        
        if (hasSelection) {
            calculatorSections.classList.remove('disabled');
        } else {
            calculatorSections.classList.add('disabled');
        }
    }

    function setupEventListeners() {
        document.getElementById('add-row-btn').addEventListener('click', createRow);
        ingredientsTbody.addEventListener('input', calculateAll);
        document.getElementById('download-btn').addEventListener('click', downloadMarkdown);
        setupAutoResize(); // Tilføj denne linje
        
        // Event listener for container størrelse toggle
        const sizeInputs = document.querySelectorAll('input[name="container-size"]');
        sizeInputs.forEach(input => {
            input.addEventListener('change', () => {
                updateContainerSize();
                updateCalculatorState(); // Add this line
            });
        });
        
        // Initial setup
        updateContainerSize();
        updateCalculatorState(); // Add this line
    }

    function updateContainerSize() {
        const selectedSize = document.querySelector('input[name="container-size"]:checked')?.value || 'regular';
        const maxVolumeSpan = document.getElementById('max-volume');
        
        if (selectedSize === 'deluxe') {
            maxVolumeSpan.textContent = '710ml';
        } else {
            maxVolumeSpan.textContent = '473ml';
        }
        
        // Genberegn alt for at opdatere volume counter
        calculateAll();
    }

    function calculateAll() {
        const totals = {
            weight: 0, kcal: 0, fat: 0, carbs: 0, sugar: 0, 
            protein: 0, salt: 0, pac: 0, msnf: 0, hf: 0, volume: 0
        };

        const rows = ingredientsTbody.querySelectorAll('tr');
        rows.forEach(row => {
            const nameInput = row.querySelector('.ingredient-input').value;
            const quantity = parseFloat(row.querySelector('.quantity-input').value) || 0;

            if (nameInput && quantity > 0) {
                // Tjek først database, derefter brugerdefinerede ingredienser
                let ingredient = ingredientsData.find(ing => ing.Ingrediens === nameInput);
                if (!ingredient && customIngredients[nameInput]) {
                    ingredient = customIngredients[nameInput];
                }

                if (ingredient) {
                    totals.weight += quantity;
                    totals.volume += quantity; // Antager 1g = 1ml for de fleste ingredienser
                    totals.kcal += (ingredient['Energi (kcal)'] / 100) * quantity;
                    totals.fat += (ingredient.Fedt / 100) * quantity;
                    totals.carbs += (ingredient.Kulhydrater / 100) * quantity;
                    totals.sugar += (ingredient.Sukker / 100) * quantity;
                    totals.protein += (ingredient.Protein / 100) * quantity;
                    totals.salt += (ingredient.Salt / 100) * quantity;
                    totals.pac += (ingredient.PAC / 100) * quantity;
                    totals.msnf += (ingredient.MSNF / 100) * quantity;
                    totals.hf += (ingredient.HF / 100) * quantity;
                }
            }
        });
        
        const fpdf = totals.weight > 0 ? ((totals.pac - totals.hf) / totals.weight) * 100 : 0;
        const msnfPerc = totals.weight > 0 ? (totals.msnf / totals.weight) * 100 : 0;

        // Opdater total værdier
        document.getElementById('total-kcal').textContent = totals.kcal.toFixed(1) + ' kcal';
        document.getElementById('total-fat').textContent = totals.fat.toFixed(1) + 'g';
        document.getElementById('total-carbs').textContent = totals.carbs.toFixed(1) + 'g';
        document.getElementById('total-sugar').textContent = totals.sugar.toFixed(1) + 'g';
        document.getElementById('total-protein').textContent = totals.protein.toFixed(1) + 'g';
        document.getElementById('total-salt').textContent = totals.salt.toFixed(1) + 'g';
        
        // Beregn per 100g/ml værdier
        const per100Factor = totals.weight > 0 ? 100 / totals.weight : 0;
        document.getElementById('per100-kcal').textContent = (totals.kcal * per100Factor).toFixed(1) + ' kcal';
        document.getElementById('per100-fat').textContent = (totals.fat * per100Factor).toFixed(1) + 'g';
        document.getElementById('per100-carbs').textContent = (totals.carbs * per100Factor).toFixed(1) + 'g';
        document.getElementById('per100-sugar').textContent = (totals.sugar * per100Factor).toFixed(1) + 'g';
        document.getElementById('per100-protein').textContent = (totals.protein * per100Factor).toFixed(1) + 'g';
        document.getElementById('per100-salt').textContent = (totals.salt * per100Factor).toFixed(1) + 'g';
        
        // Tekniske værdier
        document.getElementById('total-fpdf').textContent = fpdf.toFixed(1);
        document.getElementById('total-msnf-perc').textContent = `${msnfPerc.toFixed(1)}%`;
        
        // Opdater volume counter
        updateVolumeCounter(totals.volume);
    }
    
    function updateVolumeCounter(currentVolume) {
        const selectedSize = document.querySelector('input[name="container-size"]:checked')?.value || 'regular';
        const maxVolume = selectedSize === 'deluxe' ? 710 : 473;
        const volumeSpan = document.getElementById('total-volume');
        const volumeCounter = document.querySelector('.volume-counter');
        
        volumeSpan.textContent = `${Math.round(currentVolume)}ml`;
        
        // Fjern eksisterende klasser
        volumeCounter.classList.remove('volume-warning', 'volume-danger');
        
        // Tilføj advarsel/fare klasser baseret på procent fyldt
        if (volumeCounter) {
            // Fjern eksisterende klasser
            volumeCounter.classList.remove('volume-warning', 'volume-danger', 'volume-perfect');
            
            // Tilføj klasser baseret på volumen
            if (currentVolume === maxVolume) {
                volumeCounter.classList.add('volume-perfect');
            } else if (currentVolume > maxVolume) {
                volumeCounter.classList.add('volume-danger');
            } else if (currentVolume > maxVolume * 0.9) {
                volumeCounter.classList.add('volume-warning');
            }
        }
    }
    
    // Hjælpefunktion til formatering af instruktioner som nummereret liste
    function formatInstructions(instructionsText) {
        if (!instructionsText.trim()) return '';
        
        const lines = instructionsText.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
        
        if (lines.length === 0) return '';
        
        return lines.map((line, index) => `${index + 1}. ${line}`).join('\n');
    }
    
    // Hjælpefunktion til formatering af noter som punktliste
    function formatNotes(notesText) {
        if (!notesText.trim()) return '';
        
        const lines = notesText.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
        
        if (lines.length === 0) return '';
        
        return lines.map(line => `- ${line}`).join('\n');
    }
    
    function downloadMarkdown() {
        // Check if container size is selected
        const selectedSize = document.querySelector('input[name="container-size"]:checked');
        if (!selectedSize) {
            alert('Vælg venligst en container størrelse først.');
            return;
        }

        // Check for volume overflow
        const currentVolume = parseInt(document.getElementById('total-volume').textContent.replace('ml', ''));
        const maxVolume = selectedSize.value === 'deluxe' ? 710 : 473;
        const sizeText = selectedSize.value === 'deluxe' ? 'Deluxe' : 'Regular';

        if (currentVolume > maxVolume) {
            showOverflowWarning(currentVolume, maxVolume, sizeText, () => {
                proceedWithDownload(selectedSize, sizeText);
            });
            return;
        }

        // Proceed normally if no overflow
        proceedWithDownload(selectedSize, sizeText);
    }

    function showOverflowWarning(currentVolume, maxVolume, sizeText, onContinue) {
        const warningHTML = `
            <div class="warning-overlay" id="overflow-warning">
                <div class="warning-content">
                    <div class="warning-header">
                        <h3>Opskrift Overstiger Container Kapacitet</h3>
                    </div>
                    <div class="warning-body">
                        <p><strong>Din opskrift er for stor til den valgte container:</strong></p>
                        <ul>
                            <li>Opskriftens volumen: <strong>${currentVolume}ml</strong></li>
                            <li>Container kapacitet (${sizeText}): <strong>${maxVolume}ml</strong></li>
                            <li>Overskydende: <strong>${currentVolume - maxVolume}ml</strong></li>
                        </ul>
                        <p>Du kan enten justere opskriften eller fortsætte med at downloade den som den er.</p>
                    </div>
                    <div class="warning-footer">
                        <button class="warning-btn warning-continue" id="warning-continue">
                            Download Alligevel
                        </button>
                        <button class="warning-btn warning-cancel" id="warning-cancel">
                            Annuller
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', warningHTML);

        const warningElement = document.getElementById('overflow-warning');
        const continueBtn = document.getElementById('warning-continue');
        const cancelBtn = document.getElementById('warning-cancel');

        // Event listeners
        continueBtn.addEventListener('click', () => {
            warningElement.remove();
            onContinue();
        });

        cancelBtn.addEventListener('click', () => {
            warningElement.remove();
        });

        // Close on escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                warningElement.remove();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);

        // Close on overlay click
        warningElement.addEventListener('click', (e) => {
            if (e.target === warningElement) {
                warningElement.remove();
            }
        });
    }

    function proceedWithDownload(selectedSize, sizeText) {
        // Get recipe name and add size suffix
        const baseName = document.getElementById('recipe-name-input').value.trim() || 'Unavngivet Opskrift';
        const recipeName = `${baseName} (${sizeText})`;
        
        let markdown = `# ${recipeName}\n\n`;
        
        // Check if there's any description content
        const description = document.getElementById('recipe-description-input')?.value.trim();
        markdown += `## Beskrivelse\n`;
        if (description) {
            markdown += `${description}\n\n`;
        } else {
            markdown += `*Ingen beskrivelse tilføjet.*\n\n`;
        }
        
        // Check for ingredients
        const rows = ingredientsTbody.querySelectorAll('tr');
        let hasIngredients = false;
        let ingredientsTable = '';
        
        rows.forEach(row => {
            const name = row.querySelector('.ingredient-input').value;
            const quantity = row.querySelector('.quantity-input').value;
            if (name && quantity) {
                if (!hasIngredients) {
                    hasIngredients = true;
                    ingredientsTable = `| Ingrediens | Mængde (g) |\n|:---|---:|\n`;
                }
                ingredientsTable += `| ${name} | ${quantity}g |\n`;
            }
        });

        markdown += `## Ingredienser\n`;
        if (hasIngredients) {
            markdown += ingredientsTable;
        } else {
            markdown += `*Ingen ingredienser tilføjet.*\n`;
        }

        // Instructions
        const instructions = document.getElementById('instructions-box').value;
        markdown += `\n## Fremgangsmåde\n`;
        if (instructions.trim()) {
            const formattedInstructions = formatInstructions(instructions);
            markdown += `${formattedInstructions}\n`;
        } else {
            markdown += `*Ingen fremgangsmåde beskrevet.*\n`;
        }

        // Nutrition info
        markdown += `\n## Næringsindhold\n`;
        if (hasIngredients) {
            // Total nutrition
            markdown += `### Per Total Opskrift (${document.getElementById('total-volume').textContent})\n`;
            markdown += `| Næringsemne | Værdi |\n`;
            markdown += `|:---|---:|\n`;
            markdown += `| Energi | ${document.getElementById('total-kcal').textContent} |\n`;
            markdown += `| Fedt | ${document.getElementById('total-fat').textContent} |\n`;
            markdown += `| Kulhydrater | ${document.getElementById('total-carbs').textContent} |\n`;
            markdown += `| Sukker | ${document.getElementById('total-sugar').textContent} |\n`;
            markdown += `| Protein | ${document.getElementById('total-protein').textContent} |\n`;
            markdown += `| Salt | ${document.getElementById('total-salt').textContent} |\n`;

            // Per 100g/ml nutrition
            markdown += `\n### Per 100g/ml\n`;
            markdown += `| Næringsemne | Værdi |\n`;
            markdown += `|:---|---:|\n`;
            markdown += `| Energi | ${document.getElementById('per100-kcal').textContent} |\n`;
            markdown += `| Fedt | ${document.getElementById('per100-fat').textContent} |\n`;
            markdown += `| Kulhydrater | ${document.getElementById('per100-carbs').textContent} |\n`;
            markdown += `| Sukker | ${document.getElementById('per100-sugar').textContent} |\n`;
            markdown += `| Protein | ${document.getElementById('per100-protein').textContent} |\n`;
            markdown += `| Salt | ${document.getElementById('per100-salt').textContent} |\n`;

            // Technical values
            markdown += `\n### Tekniske Værdier\n`;
            markdown += `| Parameter | Værdi |\n`;
            markdown += `|:---|---:|\n`;
            markdown += `| **FPDF** | **${document.getElementById('total-fpdf').textContent}** |\n`;
            markdown += `| **MSNF %** | **${document.getElementById('total-msnf-perc').textContent}** |\n`;
        } else {
            markdown += `*Ingen næringsindhold at beregne - tilføj ingredienser først.*\n`;
        }

        // Notes
        const notes = document.getElementById('notes-box').value;
        markdown += `\n## Noter\n`;
        if (notes.trim()) {
            const formattedNotes = formatNotes(notes);
            markdown += `${formattedNotes}\n`;
        } else {
            markdown += `*Ingen noter tilføjet.*\n`;
        }
        
        // Download with size in filename
        const filename = baseName.toLowerCase().replace(/[^a-z0-9æøåäöü]/g, '_') + `_${sizeText.toLowerCase()}.md`;
        const blob = new Blob([markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    // Start applikationen
    init();
});