document.addEventListener('DOMContentLoaded', () => {
    // --- STATE & DOM REFERENCES ---
    let ingredientsData = [];
    let customIngredients = {};
    const ingredientsTbody = document.getElementById('ingredients-tbody');
    const mixinsTbody = document.getElementById('mixins-tbody');
    const showMixinsBtn = document.getElementById('show-mixins-btn');
    const mixinsTableWrapper = document.getElementById('mixins-table-wrapper');
    let currentFocus = -1;

    // --- INITIALIZATION ---
    async function init() {
        try {
            const response = await fetch(siteBaseURL + 'ingredients.json');
            ingredientsData = await response.json();
            setupInitialRows();
            setupEventListeners();
            createModal();
        } catch (error) {
            console.error('Kunne ikke indlæse ingrediens-database:', error);
        }
    }

    function setupInitialRows() {
        for (let i = 0; i < 5; i++) createRow(ingredientsTbody);
    }

    // --- UI & EVENT HANDLING ---
    function createRow(tbody) {
        const tr = document.createElement('tr');
        const placeholder = tbody === ingredientsTbody ? "Søg efter ingrediens..." : "Søg efter mix-in...";
        tr.innerHTML = `
            <td>
                <div class="ingredient-input-container">
                    <input type="text" class="ingredient-input" placeholder="${placeholder}" autocomplete="off">
                    <button type="button" class="manual-input-btn hidden" title="Indtast næringsværdier manuelt">!</button>
                </div>
            </td>
            <td><input type="number" class="quantity-input" placeholder="0" min="0"></td>
        `;
        tbody.appendChild(tr);
        setupRowEventListeners(tr);
    }

    // Updated setupRowEventListeners function with proper container-based autocomplete
    function setupRowEventListeners(row) {
        const ingredientInput = row.querySelector('.ingredient-input');
        const manualBtn = row.querySelector('.manual-input-btn');
        const container = row.querySelector('.ingredient-input-container');
        let currentAutocomplete = null;

        // --- AUTOCOMPLETE LOGIC ---
        ingredientInput.addEventListener('input', function() {
            const searchTerm = this.value;
            closeAutocomplete();
            
            if (!searchTerm) {
                manualBtn.style.display = 'none';
                manualBtn.classList.add('hidden');
                return;
            }

            currentFocus = -1;
            
            // Create autocomplete dropdown for this specific input
            currentAutocomplete = createAutocompleteDropdown(container);
            
            // Filter ingredients based on the search term, including custom ones.
            const allIngredients = [...ingredientsData, ...Object.values(customIngredients)];
            const uniqueSuggestions = new Map();

            allIngredients.filter(ing => 
                ing.Ingrediens.toLowerCase().includes(searchTerm.toLowerCase())
            ).forEach(ing => {
                if (!uniqueSuggestions.has(ing.Ingrediens)) {
                    uniqueSuggestions.set(ing.Ingrediens, ing);
                }
            });

            uniqueSuggestions.forEach(ing => {
                const item = document.createElement('div');
                item.classList.add('autocomplete-item');
                item.innerHTML = ing.Ingrediens.replace(new RegExp(searchTerm, 'gi'), (match) => `<strong>${match}</strong>`);
                
                item.addEventListener('click', () => {
                    ingredientInput.value = ing.Ingrediens;
                    closeAutocomplete();
                    calculateAll();
                    // Hide manual button when valid ingredient is selected
                    manualBtn.style.display = 'none';
                    manualBtn.classList.add('hidden');
                });
                currentAutocomplete.appendChild(item);
            });

            // Show manual button check - Reset styles first, then check
            const value = searchTerm.trim();
            const exists = ingredientsData.some(ing => ing.Ingrediens === value) || customIngredients[value];
            
            if (value && !exists) {
                // Reset any previous hiding and show the button
                manualBtn.style.visibility = '';
                manualBtn.style.display = 'flex';
                manualBtn.classList.remove('hidden');
            } else {
                manualBtn.style.display = 'none';
                manualBtn.classList.add('hidden');
            }
        });

        // --- KEYBOARD NAVIGATION ---
        ingredientInput.addEventListener('keydown', function(e) {
            if (!currentAutocomplete) return;
            
            let items = currentAutocomplete.getElementsByTagName('div');
            if (e.key === 'ArrowDown') {
                currentFocus++;
                addActive(items);
            } else if (e.key === 'ArrowUp') {
                currentFocus--;
                addActive(items);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (currentFocus > -1 && items) {
                    items[currentFocus].click();
                }
            } else if (e.key === 'Escape') {
                closeAutocomplete();
            }
        });

        // Close autocomplete when input loses focus (with small delay for clicks)
        ingredientInput.addEventListener('blur', function() {
            setTimeout(() => {
                if (currentAutocomplete && !currentAutocomplete.contains(document.activeElement)) {
                    closeAutocomplete();
                }
            }, 150);
        });

        function closeAutocomplete() {
            if (currentAutocomplete) {
                currentAutocomplete.remove();
                currentAutocomplete = null;
            }
            currentFocus = -1;
        }

        manualBtn.addEventListener('click', () => openModal(row));
    }

    // Create autocomplete dropdown within the specific container
    function createAutocompleteDropdown(container) {
        const dropdown = document.createElement('div');
        dropdown.classList.add('autocomplete-items');
        container.appendChild(dropdown);
        
        // Position based on screen size
        const isMobile = window.innerWidth <= 768;
        if (isMobile) {
            dropdown.style.left = '0';
            dropdown.style.right = '0';
            dropdown.style.width = 'auto';
            dropdown.style.maxWidth = 'none';
        }
        
        return dropdown;
    }

    // Updated helper functions for the new approach
    function addActive(items) {
        if (!items || items.length === 0) return;
        removeActive(items);
        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (items.length - 1);
        items[currentFocus].classList.add("autocomplete-active");
        items[currentFocus].scrollIntoView({ block: 'nearest' });
    }

    function removeActive(items) {
        for (let i = 0; i < items.length; i++) {
            items[i].classList.remove("autocomplete-active");
        }
    }

    // Close all autocomplete dropdowns (global function)
    function closeAllLists() {
        document.querySelectorAll('.autocomplete-items').forEach(dropdown => {
            dropdown.remove();
        });
        currentFocus = -1;
    }

    // setupEventListeners function to handle global clicks
    function setupEventListeners() {
        document.getElementById('add-row-btn').addEventListener('click', () => createRow(ingredientsTbody));
        document.getElementById('add-mixin-btn').addEventListener('click', () => createRow(mixinsTbody));
        
        showMixinsBtn.addEventListener('click', () => {
            showMixinsBtn.parentElement.style.display = 'none';
            mixinsTableWrapper.style.display = 'flex';

            if (mixinsTbody.children.length === 0) {
                createRow(mixinsTbody);
            }
        });
        
        ingredientsTbody.addEventListener('input', calculateAll);
        mixinsTbody.addEventListener('input', calculateAll);

        document.getElementById('download-btn').addEventListener('click', downloadMarkdown);
        setupAutoResize();
        
        const sizeInputs = document.querySelectorAll('input[name="container-size"]');
        sizeInputs.forEach(input => {
            input.addEventListener('change', () => {
                updateContainerSize();
                updateCalculatorState();
            });
        });
        
        // Close autocomplete lists if user clicks elsewhere
        document.addEventListener("click", function (e) {
            if (!e.target.closest('.ingredient-input-container')) {
                closeAllLists();
            }
        });
        
        updateContainerSize();
        updateCalculatorState();
    }

    // --- CORE CALCULATION LOGIC ---
    function calculateAll() {
        const baseTotals = calculateTableTotals(ingredientsTbody, true);
        const mixinTotals = calculateTableTotals(mixinsTbody, false);

        const combinedTotals = {
            weight: baseTotals.weight + mixinTotals.weight,
            kcal: baseTotals.kcal + mixinTotals.kcal,
            fat: baseTotals.fat + mixinTotals.fat,
            carbs: baseTotals.carbs + mixinTotals.carbs,
            sugar: baseTotals.sugar + mixinTotals.sugar,
            protein: baseTotals.protein + mixinTotals.protein,
            salt: baseTotals.salt + mixinTotals.salt,
            volume: baseTotals.volume
        };

        const fpdf = baseTotals.weight > 0 ? ((baseTotals.pac - baseTotals.hf) / baseTotals.weight) * 100 : 0;
        const msnfPerc = baseTotals.weight > 0 ? (baseTotals.msnf / baseTotals.weight) * 100 : 0;

        updateNutritionUI(combinedTotals);
        updateTechnicalUI(fpdf, msnfPerc);
        updateVolumeCounter(combinedTotals.volume);
    }

    function calculateTableTotals(tbody, isBase) {
        const totals = { weight: 0, kcal: 0, fat: 0, carbs: 0, sugar: 0, protein: 0, salt: 0, pac: 0, msnf: 0, hf: 0, volume: 0 };
        const rows = tbody.querySelectorAll('tr');

        rows.forEach(row => {
            const nameInput = row.querySelector('.ingredient-input').value;
            const quantity = parseFloat(row.querySelector('.quantity-input').value) || 0;

            if (nameInput && quantity > 0) {
                const ingredient = ingredientsData.find(ing => ing.Ingrediens === nameInput) || customIngredients[nameInput];
                if (ingredient) {
                    totals.weight += quantity;
                    totals.volume += quantity;
                    totals.kcal += (ingredient['Energi (kcal)'] / 100) * quantity;
                    totals.fat += (ingredient.Fedt / 100) * quantity;
                    totals.carbs += (ingredient.Kulhydrater / 100) * quantity;
                    totals.sugar += (ingredient.Sukker / 100) * quantity;
                    totals.protein += (ingredient.Protein / 100) * quantity;
                    totals.salt += (ingredient.Salt / 100) * quantity;

                    if (isBase) {
                        totals.msnf += (ingredient.MSNF / 100) * quantity;
                        if (ingredient.PAC > 0) {
                            totals.pac += (ingredient.PAC / 100) * quantity;
                        } else {
                            const calculatedPac = (ingredient.Sukker * 1.0) + ((ingredient.Kulhydrater - ingredient.Sukker) * 0.5) + (ingredient.Salt * 5.9);
                            totals.pac += (calculatedPac / 100) * quantity;
                        }
                        if (ingredient.HF > 0) {
                            totals.hf += (ingredient.HF / 100) * quantity;
                        } else {
                            totals.hf += (ingredient.Fedt / 100) * quantity;
                        }
                    }
                }
            }
        });
        return totals;
    }

    function updateNutritionUI(totals) {
        document.getElementById('total-kcal').textContent = totals.kcal.toFixed(1) + ' kcal';
        document.getElementById('total-fat').textContent = totals.fat.toFixed(1) + 'g';
        document.getElementById('total-carbs').textContent = totals.carbs.toFixed(1) + 'g';
        document.getElementById('total-sugar').textContent = totals.sugar.toFixed(1) + 'g';
        document.getElementById('total-protein').textContent = totals.protein.toFixed(1) + 'g';
        document.getElementById('total-salt').textContent = totals.salt.toFixed(1) + 'g';

        const per100Factor = totals.weight > 0 ? 100 / totals.weight : 0;
        document.getElementById('per100-kcal').textContent = (totals.kcal * per100Factor).toFixed(1) + ' kcal';
        document.getElementById('per100-fat').textContent = (totals.fat * per100Factor).toFixed(1) + 'g';
        document.getElementById('per100-carbs').textContent = (totals.carbs * per100Factor).toFixed(1) + 'g';
        document.getElementById('per100-sugar').textContent = (totals.sugar * per100Factor).toFixed(1) + 'g';
        document.getElementById('per100-protein').textContent = (totals.protein * per100Factor).toFixed(1) + 'g';
        document.getElementById('per100-salt').textContent = (totals.salt * per100Factor).toFixed(1) + 'g';
    }

    function updateTechnicalUI(fpdf, msnfPerc) {
        document.getElementById('total-fpdf').textContent = fpdf.toFixed(1);
        document.getElementById('total-msnf-perc').textContent = `${msnfPerc.toFixed(1)}%`;
    }

    // --- MODAL LOGIC ---
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
                            <div class="nutrition-row"><label>Energi (kcal):</label><input type="number" id="modal-energy" min="0" placeholder="0"></div>
                            <div class="nutrition-row"><label>Fedt (g):</label><input type="number" id="modal-fat" min="0" step="0.1" placeholder="0"></div>
                            <div class="nutrition-row"><label>Kulhydrater (g):</label><input type="number" id="modal-carbs" min="0" step="0.1" placeholder="0"></div>
                            <div class="nutrition-row"><label>Sukker (g):</label><input type="number" id="modal-sugar" min="0" step="0.1" placeholder="0"></div>
                            <div class="nutrition-row"><label>Protein (g):</label><input type="number" id="modal-protein" min="0" step="0.1" placeholder="0"></div>
                            <div class="nutrition-row"><label>Salt (g):</label><input type="number" id="modal-salt" min="0" step="0.1" placeholder="0"></div>
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
        const inputs = modal.querySelectorAll('input[type="number"], #modal-lactose-free-checkbox');

        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
        document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && modal.style.display !== 'none') closeModal(); });

        inputs.forEach(input => input.addEventListener('input', updateModalCalculations));
        saveBtn.addEventListener('click', saveFromModal);
    }

    function openModal(row) {
        const modal = document.getElementById('nutrition-modal');
        const ingredientName = row.querySelector('.ingredient-input').value.trim();
        
        document.getElementById('modal-ingredient-name').textContent = ingredientName;
        modal.querySelectorAll('input[type="number"]').forEach(input => input.value = '');
        document.getElementById('modal-lactose-free-checkbox').checked = false;
        
        updateModalCalculations();
        
        modal.dataset.currentRow = Array.from(row.parentElement.children).indexOf(row);
        modal.dataset.currentTbody = row.parentElement.id;
        
        modal.style.display = 'flex';
        document.getElementById('modal-energy').focus();
    }

    function closeModal() {
        document.getElementById('nutrition-modal').style.display = 'none';
    }

    function updateModalCalculations() {
        const fat = parseFloat(document.getElementById('modal-fat').value) || 0;
        const carbs = parseFloat(document.getElementById('modal-carbs').value) || 0;
        const sugar = parseFloat(document.getElementById('modal-sugar').value) || 0;
        const protein = parseFloat(document.getElementById('modal-protein').value) || 0;
        const salt = parseFloat(document.getElementById('modal-salt').value) || 0;
        const isLactoseFree = document.getElementById('modal-lactose-free-checkbox').checked;

        let pac = isLactoseFree
            ? sugar * 1.9 + (carbs - sugar) * 0.6 + salt * 5.9
            : sugar * 1.0 + (carbs - sugar) * 0.5 + salt * 5.9;

        document.getElementById('modal-calc-pac').textContent = pac.toFixed(1);
        document.getElementById('modal-calc-msnf').textContent = (carbs + protein).toFixed(1);
        document.getElementById('modal-calc-hf').textContent = fat.toFixed(1);
    }

    function saveFromModal() {
        const modal = document.getElementById('nutrition-modal');
        const ingredientName = document.getElementById('modal-ingredient-name').textContent;
        const rowIndex = parseInt(modal.dataset.currentRow);
        const tbodyId = modal.dataset.currentTbody;
        const tbody = document.getElementById(tbodyId);
        const row = tbody.querySelectorAll('tr')[rowIndex];

        if (!ingredientName.trim()) {
            alert('Ingrediensnavn mangler');
            return;
        }

        const energy = parseFloat(document.getElementById('modal-energy').value) || 0;
        const fat = parseFloat(document.getElementById('modal-fat').value) || 0;
        const carbs = parseFloat(document.getElementById('modal-carbs').value) || 0;
        const sugar = parseFloat(document.getElementById('modal-sugar').value) || 0;
        const protein = parseFloat(document.getElementById('modal-protein').value) || 0;
        const salt = parseFloat(document.getElementById('modal-salt').value) || 0;
        const isLactoseFree = document.getElementById('modal-lactose-free-checkbox').checked;

        let pac = isLactoseFree
            ? sugar * 1.9 + (carbs - sugar) * 0.6 + salt * 5.9
            : sugar * 1.0 + (carbs - sugar) * 0.5 + salt * 5.9;

        customIngredients[ingredientName] = {
            'Ingrediens': ingredientName,
            'Energi (kcal)': energy, 'Fedt': fat, 'Kulhydrater': carbs,
            'Sukker': sugar, 'Protein': protein, 'Salt': salt,
            'PAC': pac, 'MSNF': carbs + protein, 'HF': fat,
            'Kommentar': `Brugerdefineret${isLactoseFree ? ' (laktosefri)' : ''}`
        };

        row.querySelector('.manual-input-btn').style.display = 'none';
        closeModal();
        calculateAll();
        alert(`"${ingredientName}" er blevet gemt som brugerdefineret ingrediens!`);
    }

    // --- HELPER FUNCTIONS ---
    function setupAutoResize() {
        document.querySelectorAll('textarea').forEach(textarea => {
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + 'px';
            });
        });
    }

    function updateCalculatorState() {
        const calculatorSections = document.querySelector('.calculator-sections');
        const hasSelection = document.querySelector('input[name="container-size"]:checked');
        calculatorSections.classList.toggle('disabled', !hasSelection);
    }

    function updateContainerSize() {
        const selectedSize = document.querySelector('input[name="container-size"]:checked')?.value || 'regular';
        document.getElementById('max-volume').textContent = selectedSize === 'deluxe' ? '710ml' : '473ml';
        calculateAll();
    }
    
    function updateVolumeCounter(currentVolume) {
        const selectedSize = document.querySelector('input[name="container-size"]:checked')?.value || 'regular';
        const maxVolume = selectedSize === 'deluxe' ? 710 : 473;
        const volumeSpan = document.getElementById('total-volume');
        const volumeCounter = document.querySelector('.volume-counter');
        
        volumeSpan.textContent = `${Math.round(currentVolume)}ml`;
        
        volumeCounter.classList.remove('volume-warning', 'volume-danger', 'volume-perfect');
        if (currentVolume === maxVolume) {
            volumeCounter.classList.add('volume-perfect');
        } else if (currentVolume > maxVolume) {
            volumeCounter.classList.add('volume-danger');
        } else if (currentVolume > maxVolume * 0.9) {
            volumeCounter.classList.add('volume-warning');
        }
    }
    
    function formatInstructions(text) {
        return text.split('\n').map(line => line.trim()).filter(line => line).map((line, index) => `${index + 1}. ${line}`).join('\n');
    }
    
    function formatNotes(text) {
        return text.split('\n').map(line => line.trim()).filter(line => line).map(line => `- ${line}`).join('\n');
    }
    
    // --- MARKDOWN EXPORT ---
    function downloadMarkdown() {
        const selectedSize = document.querySelector('input[name="container-size"]:checked');
        if (!selectedSize) {
            alert('Vælg venligst en container størrelse først.');
            return;
        }

        const { volume } = calculateTableTotals(ingredientsTbody, true);
        const maxVolume = selectedSize.value === 'deluxe' ? 710 : 473;
        const sizeText = selectedSize.value === 'deluxe' ? 'Deluxe' : 'Regular';

        if (volume > maxVolume) {
            showOverflowWarning(volume, maxVolume, sizeText, () => proceedWithDownload(selectedSize, sizeText));
        } else {
            proceedWithDownload(selectedSize, sizeText);
        }
    }

    function showOverflowWarning(currentVolume, maxVolume, sizeText, onContinue) {
        const warningHTML = `
            <div class="warning-overlay" id="overflow-warning">
                <div class="warning-content">
                    <div class="warning-header"><h3>Opskrift Overstiger Container Kapacitet</h3></div>
                    <div class="warning-body">
                        <p><strong>Din opskrift er for stor til den valgte container:</strong></p>
                        <ul>
                            <li>Opskriftens volumen: <strong>${Math.round(currentVolume)}ml</strong></li>
                            <li>Container kapacitet (${sizeText}): <strong>${maxVolume}ml</strong></li>
                            <li>Overskydende: <strong>${Math.round(currentVolume - maxVolume)}ml</strong></li>
                        </ul>
                        <p>Du kan enten justere opskriften eller fortsætte med at downloade den som den er.</p>
                    </div>
                    <div class="warning-footer">
                        <button class="warning-btn warning-continue">Download Alligevel</button>
                        <button class="warning-btn warning-cancel">Annuller</button>
                    </div>
                </div>
            </div>`;
        document.body.insertAdjacentHTML('beforeend', warningHTML);

        const warningElement = document.getElementById('overflow-warning');
        const continueBtn = warningElement.querySelector('.warning-continue');
        const cancelBtn = warningElement.querySelector('.warning-cancel');

        const closeWarning = () => warningElement.remove();
        continueBtn.addEventListener('click', () => { closeWarning(); onContinue(); });
        cancelBtn.addEventListener('click', closeWarning);
        warningElement.addEventListener('click', (e) => { if (e.target === warningElement) closeWarning(); });
        document.addEventListener('keydown', function escapeHandler(e) {
            if (e.key === 'Escape') {
                closeWarning();
                document.removeEventListener('keydown', escapeHandler);
            }
        });
    }

    function proceedWithDownload(selectedSize, sizeText) {
        const baseName = document.getElementById('recipe-name-input').value.trim() || 'Unavngivet Opskrift';
        const recipeName = `${baseName} (${sizeText})`;
        let markdown = `# ${recipeName}\n\n`;

        const description = document.getElementById('recipe-description-input')?.value.trim();
        markdown += `## Beskrivelse\n${description || '*Ingen beskrivelse tilføjet.*'}\n\n`;

        const buildTable = (tbody, header) => {
            let tableMd = '';
            let hasRows = false;
            tbody.querySelectorAll('tr').forEach(row => {
                const name = row.querySelector('.ingredient-input').value;
                const quantity = row.querySelector('.quantity-input').value;
                if (name && quantity) {
                    if (!hasRows) {
                        hasRows = true;
                        tableMd += `| ${header} | Mængde (g) |\n|:---|---:|\n`;
                    }
                    tableMd += `| ${name} | ${quantity}g |\n`;
                }
            });
            return hasRows ? tableMd : '*Ingen tilføjet.*\n';
        };

        markdown += `## Ingredienser (Is-base)\n`;
        markdown += buildTable(ingredientsTbody, 'Ingrediens');

        markdown += `\n## Mix-Ins\n`;
        markdown += buildTable(mixinsTbody, 'Mix-In');

        const instructions = document.getElementById('instructions-box').value;
        markdown += `\n## Fremgangsmåde\n${instructions.trim() ? formatInstructions(instructions) : '*Ingen fremgangsmåde beskrevet.*'}\n`;

        markdown += `\n## Næringsindhold\n`;
        markdown += `### Per Total Opskrift (${document.getElementById('total-volume').textContent})\n`;
        markdown += `| Næringsemne | Værdi |\n|:---|---:|\n`;
        markdown += `| Energi | ${document.getElementById('total-kcal').textContent} |\n`;
        markdown += `| Fedt | ${document.getElementById('total-fat').textContent} |\n`;
        markdown += `| Kulhydrater | ${document.getElementById('total-carbs').textContent} |\n`;
        markdown += `| Sukker | ${document.getElementById('total-sugar').textContent} |\n`;
        markdown += `| Protein | ${document.getElementById('total-protein').textContent} |\n`;
        markdown += `| Salt | ${document.getElementById('total-salt').textContent} |\n`;

        markdown += `\n### Per 100g/ml\n`;
        markdown += `| Næringsemne | Værdi |\n|:---|---:|\n`;
        markdown += `| Energi | ${document.getElementById('per100-kcal').textContent} |\n`;
        markdown += `| Fedt | ${document.getElementById('per100-fat').textContent} |\n`;
        markdown += `| Kulhydrater | ${document.getElementById('per100-carbs').textContent} |\n`;
        markdown += `| Sukker | ${document.getElementById('per100-sugar').textContent} |\n`;
        markdown += `| Protein | ${document.getElementById('per100-protein').textContent} |\n`;
        markdown += `| Salt | ${document.getElementById('per100-salt').textContent} |\n`;

        markdown += `\n### Tekniske Værdier (Kun Is-base)\n`;
        markdown += `| Parameter | Værdi |\n|:---|---:|\n`;
        markdown += `| **FPDF** | **${document.getElementById('total-fpdf').textContent}** |\n`;
        markdown += `| **MSNF %** | **${document.getElementById('total-msnf-perc').textContent}** |\n`;

        const notes = document.getElementById('notes-box').value;
        markdown += `\n## Noter\n${notes.trim() ? formatNotes(notes) : '*Ingen noter tilføjet.*'}\n`;
        
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

    // --- APPLICATION START ---
    init();
});