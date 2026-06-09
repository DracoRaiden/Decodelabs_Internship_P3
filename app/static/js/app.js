// TechMatch AI - Application Script
document.addEventListener("DOMContentLoaded", () => {
    
    // Core Application State
    const state = {
        currentStep: 1,
        profile: {
            skills: [],
            interests: [],
            goals: []
        },
        topN: 3,
        allSkillsDb: [] // Fetched dynamically from /api/skills
    };

    // DOM Elements - Navigation
    const onboardingSection = document.getElementById("onboarding-section");
    const dashboardSection = document.getElementById("dashboard-section");
    const currentStepNum = document.getElementById("current-step-num");
    const progressBarFill = document.getElementById("progress-bar-fill");
    
    // DOM Elements - Buttons
    const btnPrevStep = document.getElementById("btn-prev-step");
    const btnNextStep = document.getElementById("btn-next-step");
    const btnSubmitOnboarding = document.getElementById("btn-submit-onboarding");
    const btnResetSurvey = document.getElementById("btn-reset-survey");
    
    // Onboarding Step Divs
    const steps = [
        document.getElementById("step-1"),
        document.getElementById("step-2"),
        document.getElementById("step-3")
    ];

    // Math explainer
    const mathToggle = document.getElementById("math-header-toggle");
    const mathCard = mathToggle.closest(".math-explainer-card");

    // Initialize UI Preset Skills and event handlers
    initApp();

    /* ==========================================
       1. INITIALIZATION & DATA FETCHING
       ========================================== */
    async function initApp() {
        // Fetch unique skills from backend vocabulary to dynamically populate the preset buttons
        try {
            const response = await fetch("/api/skills");
            if (response.ok) {
                const data = await response.json();
                state.allSkillsDb = data.skills;
                renderDynamicPresets(data.skills);
            }
        } catch (error) {
            console.error("Failed to fetch skills from vocabulary:", error);
        }

        // Hook up onboarding navigation
        btnNextStep.addEventListener("click", nextStep);
        btnPrevStep.addEventListener("click", prevStep);
        btnSubmitOnboarding.addEventListener("click", submitOnboarding);
        btnResetSurvey.addEventListener("click", resetToSurvey);

        // Onboarding Step 1: Click Interest Cards
        const interestCards = document.querySelectorAll(".interest-card");
        interestCards.forEach(card => {
            card.addEventListener("click", () => {
                card.classList.toggle("selected");
                const val = card.getAttribute("data-val");
                const text = card.querySelector("h4").innerText;
                
                if (card.classList.contains("selected")) {
                    if (!state.profile.interests.includes(text)) {
                        state.profile.interests.push(text);
                    }
                } else {
                    state.profile.interests = state.profile.interests.filter(i => i !== text);
                }
                updateOnboardingTags();
            });
        });

        // Custom Skill Ingestion in onboarding
        const btnAddCustomSkill = document.getElementById("btn-add-custom-skill");
        const inputCustomSkills = document.getElementById("input-custom-skills");
        
        btnAddCustomSkill.addEventListener("click", () => {
            addCustomSkillsFromInput(inputCustomSkills, "onboarding-skills-tags");
        });
        inputCustomSkills.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                addCustomSkillsFromInput(inputCustomSkills, "onboarding-skills-tags");
            }
        });

        // Math Toggle Accordion
        mathToggle.addEventListener("click", () => {
            mathCard.classList.toggle("expanded");
        });

        // Dashboard Slider
        const slider = document.getElementById("slider-top-n");
        const sliderVal = document.getElementById("top-n-value");
        slider.addEventListener("input", (e) => {
            state.topN = parseInt(e.target.value);
            sliderVal.innerText = state.topN;
            fetchRecommendations();
        });

        // Dashboard Inputs
        setupDashboardInput("dashboard-skills-input", "skills");
        setupDashboardInput("dashboard-interests-input", "interests");
        setupDashboardInput("dashboard-goals-input", "goals");
    }

    // Populates Step 2 with chips containing vocabulary keywords
    function renderDynamicPresets(skills) {
        const grid = document.getElementById("preset-skills-grid");
        grid.innerHTML = ""; // Clear placeholders
        
        // Take up to 15 key skills to show in wizard
        const showcaseSkills = skills.slice(0, 20);
        showcaseSkills.forEach((skill, idx) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "preset-chip";
            btn.id = `preset-${idx}`;
            btn.setAttribute("data-skill", skill);
            btn.innerText = capitalizeWord(skill);
            
            btn.addEventListener("click", () => {
                btn.classList.toggle("active");
                if (btn.classList.contains("active")) {
                    if (!state.profile.skills.includes(skill)) {
                        state.profile.skills.push(skill);
                    }
                } else {
                    state.profile.skills = state.profile.skills.filter(s => s !== skill);
                }
                updateOnboardingTags();
            });
            grid.appendChild(btn);
        });
    }

    /* ==========================================
       2. ONBOARDING WIZARD STEPS NAV
       ========================================== */
    function updateStepUI() {
        // Hide all steps, show current
        steps.forEach((stepDiv, idx) => {
            if (idx === state.currentStep - 1) {
                stepDiv.classList.add("active");
            } else {
                stepDiv.classList.remove("active");
            }
        });

        // Update step text and progress bar
        currentStepNum.innerText = state.currentStep;
        progressBarFill.style.width = `${(state.currentStep / 3) * 100}%`;

        // Update footer buttons
        if (state.currentStep === 1) {
            btnPrevStep.classList.add("hidden");
            btnPrevStep.disabled = true;
            btnNextStep.classList.remove("hidden");
            btnSubmitOnboarding.classList.add("hidden");
        } else if (state.currentStep === 2) {
            btnPrevStep.classList.remove("hidden");
            btnPrevStep.disabled = false;
            btnNextStep.classList.remove("hidden");
            btnSubmitOnboarding.classList.add("hidden");
        } else if (state.currentStep === 3) {
            btnPrevStep.classList.remove("hidden");
            btnPrevStep.disabled = false;
            btnNextStep.classList.add("hidden");
            btnSubmitOnboarding.classList.remove("hidden");
        }
    }

    function nextStep() {
        if (state.currentStep < 3) {
            state.currentStep++;
            updateStepUI();
        }
    }

    function prevStep() {
        if (state.currentStep > 1) {
            state.currentStep--;
            updateStepUI();
        }
    }

    function updateOnboardingTags() {
        const container = document.getElementById("onboarding-skills-tags");
        container.innerHTML = "";
        
        if (state.profile.skills.length === 0) {
            container.innerHTML = '<span class="no-tags-placeholder">No skills selected yet.</span>';
            return;
        }

        state.profile.skills.forEach(skill => {
            const pill = document.createElement("span");
            pill.className = "tag-pill";
            pill.innerHTML = `${capitalizeWord(skill)} <i class="fa-solid fa-xmark remove-tag"></i>`;
            pill.querySelector(".remove-tag").addEventListener("click", () => {
                state.profile.skills = state.profile.skills.filter(s => s !== skill);
                updateOnboardingTags();
                // Sync preset chip states if visible
                const activeChips = document.querySelectorAll(`.preset-chip[data-skill="${skill}"]`);
                activeChips.forEach(c => c.classList.remove("active"));
            });
            container.appendChild(pill);
        });
    }

    function addCustomSkillsFromInput(inputElem, tagContainerId) {
        const text = inputElem.value.trim();
        if (!text) return;

        // Split by comma or spaces
        const parts = text.split(/[\s,]+/);
        parts.forEach(part => {
            const clean = part.toLowerCase().replace(/[^a-z0-9\-]/g, "");
            if (clean && clean.length > 1 && !state.profile.skills.includes(clean)) {
                state.profile.skills.push(clean);
                
                // Toggle active if it matches a preset chip
                const chips = document.querySelectorAll(`.preset-chip[data-skill="${clean}"]`);
                chips.forEach(c => c.classList.add("active"));
            }
        });

        inputElem.value = "";
        updateOnboardingTags();
    }

    /* ==========================================
       3. SUBMITTING ONBOARDING & SURVEY RESETS
       ========================================== */
    function submitOnboarding() {
        // Collect goals selected via checkbox
        const checkedGoals = document.querySelectorAll('input[name="goal-choices"]:checked');
        checkedGoals.forEach(cb => {
            const words = cb.value.split(" ");
            words.forEach(w => {
                if (w && !state.profile.goals.includes(w)) {
                    state.profile.goals.push(w);
                }
            });
        });

        // Collect custom goal statement
        const customGoalText = document.getElementById("input-custom-goals").value.trim();
        if (customGoalText) {
            const words = customGoalText.toLowerCase().replace(/[^a-z0-9\-]/g, " ").split(/\s+/);
            words.forEach(w => {
                if (w && w.length > 2 && !state.profile.goals.includes(w)) {
                    state.profile.goals.push(w);
                }
            });
        }

        // Ensure we have at least 3 active input tokens across profiles to ensure data density
        const totalTokens = state.profile.skills.length + state.profile.interests.length + state.profile.goals.length;
        if (totalTokens < 3) {
            alert("To satisfy recommendation accuracy, please select or enter at least 3 total preferences (skills, fields, or goals).");
            return;
        }

        // Clean onboarding UI
        onboardingSection.classList.remove("active");
        dashboardSection.classList.add("active");

        // Sync local state to Dashboard input chips
        renderDashboardTags();
        
        // Fetch similarity scores from API
        fetchRecommendations();
    }

    function resetToSurvey() {
        // Clear state
        state.currentStep = 1;
        state.profile.skills = [];
        state.profile.interests = [];
        state.profile.goals = [];
        
        // Uncheck boxes and clear inputs
        document.querySelectorAll('input[name="goal-choices"]').forEach(cb => cb.checked = false);
        document.querySelectorAll(".interest-card").forEach(c => c.classList.remove("selected"));
        document.querySelectorAll(".preset-chip").forEach(c => c.classList.remove("active"));
        document.getElementById("input-custom-skills").value = "";
        document.getElementById("input-custom-goals").value = "";

        updateOnboardingTags();
        updateStepUI();

        dashboardSection.classList.remove("active");
        onboardingSection.classList.add("active");
    }

    /* ==========================================
       4. DASHBOARD STATE SYNC & TAG HANDLING
       ========================================== */
    function renderDashboardTags() {
        renderTagsForBlock("dashboard-skills-tags", "skills");
        renderTagsForBlock("dashboard-interests-tags", "interests");
        renderTagsForBlock("dashboard-goals-tags", "goals");
    }

    function renderTagsForBlock(containerId, profileKey) {
        const container = document.getElementById(containerId);
        container.innerHTML = "";
        
        const list = state.profile[profileKey];
        if (list.length === 0) {
            container.innerHTML = '<span class="no-tags-placeholder">No tags.</span>';
            return;
        }

        list.forEach(val => {
            const pill = document.createElement("span");
            pill.className = "tag-pill";
            pill.innerHTML = `${capitalizeWord(val)} <i class="fa-solid fa-xmark remove-tag"></i>`;
            pill.querySelector(".remove-tag").addEventListener("click", () => {
                state.profile[profileKey] = state.profile[profileKey].filter(x => x !== val);
                renderTagsForBlock(containerId, profileKey);
                fetchRecommendations();
            });
            container.appendChild(pill);
        });
    }

    function setupDashboardInput(inputId, profileKey) {
        const input = document.getElementById(inputId);
        const containerId = inputId.replace("-input", "-tags");

        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                const text = input.value.trim().toLowerCase();
                if (!text) return;
                
                // Split by spaces or commas
                const parts = text.split(/[\s,]+/);
                parts.forEach(p => {
                    const clean = p.replace(/[^a-z0-9\-]/g, "");
                    if (clean && clean.length > 1 && !state.profile[profileKey].includes(clean)) {
                        state.profile[profileKey].push(clean);
                    }
                });

                input.value = "";
                renderTagsForBlock(containerId, profileKey);
                fetchRecommendations();
            }
        });
    }

    /* ==========================================
       5. SIMILARITY SCORE & REST FETCH
       ========================================== */
    async function fetchRecommendations() {
        const listContainer = document.getElementById("recommendations-container");
        listContainer.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Recalculating vectors...</p>
            </div>
        `;

        try {
            const response = await fetch("/api/recommend", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    skills: state.profile.skills,
                    interests: state.profile.interests,
                    goals: state.profile.goals,
                    top_n: state.topN
                })
            });

            if (!response.ok) {
                throw new Error("HTTP error " + response.status);
            }

            const results = await response.json();
            
            if (results.cold_start) {
                listContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-triangle-exclamation"></i>
                        <h3>Vector Zero State Detected</h3>
                        <p>No active terms matched our dataset. Your input must contain real matching skills or interests.</p>
                        <button type="button" class="btn-primary" onclick="window.location.reload()"><i class="fa-solid fa-rotate-left"></i> Restart Onboarding</button>
                    </div>
                `;
                return;
            }

            renderRecommendations(results.recommendations, listContainer);

        } catch (error) {
            console.error("API error:", error);
            listContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-circle-xmark" style="color: var(--accent-magenta);"></i>
                    <h3>Service Error</h3>
                    <p>Failed to connect to recommendation server. Details: ${error.message}</p>
                </div>
            `;
        }
    }

    function renderRecommendations(recoms, container) {
        container.innerHTML = "";
        
        if (!recoms || recoms.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-ghost"></i>
                    <h3>No Matches Found</h3>
                    <p>Try expanding your profile tags to include more common tech keywords.</p>
                </div>
            `;
            return;
        }

        recoms.forEach((item, index) => {
            const isTopMatch = index === 0;
            const card = document.createElement("div");
            card.className = `recomm-card ${isTopMatch ? 'top-match' : ''}`;
            
            // Format scores as percentages
            const matchPercentage = Math.round(item.similarity_score * 100);
            
            // Circumference of dashboard score ring is 2 * pi * 32 = 201
            const circleRadius = 32;
            const circumference = 2 * Math.PI * circleRadius; // ~201
            const strokeDashOffset = circumference - (item.similarity_score * circumference);

            // Generate HTML for matches
            let matchesHTML = "";
            if (item.matched_skills && item.matched_skills.length > 0) {
                matchesHTML = `
                    <div class="matched-skills-display">
                        <span class="matched-label">Matched Inputs:</span>
                        ${item.matched_skills.map(s => `<span class="match-pill">${capitalizeWord(s)}</span>`).join("")}
                    </div>
                `;
            } else {
                matchesHTML = `
                    <div class="matched-skills-display">
                        <span class="matched-label">No direct overlap (semantic profile match)</span>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="recomm-info">
                    <div class="card-title-row">
                        <h3>${item.role}</h3>
                        ${isTopMatch ? `<span class="match-tag top-match-tag">Top Recommendation</span>` : `<span class="match-tag">Role Match</span>`}
                    </div>
                    <p class="recomm-desc">${item.description}</p>
                    
                    <div class="tech-stack-display">
                        <strong>Recommended Tech Stack</strong>
                        <span>${item.tech_stack}</span>
                    </div>
                    
                    ${matchesHTML}
                </div>
                <div class="recomm-score">
                    <div class="score-circle">
                        <svg>
                            <circle class="circle-bg" cx="40" cy="40" r="${circleRadius}"></circle>
                            <circle class="circle-val" cx="40" cy="40" r="${circleRadius}" 
                                    style="stroke-dasharray: ${circumference}; stroke-dashoffset: ${strokeDashOffset}; 
                                           stroke: ${isTopMatch ? 'var(--accent-purple)' : 'var(--accent-cyan)'}">
                            </circle>
                        </svg>
                        <div class="score-text">${matchPercentage}%</div>
                    </div>
                    <span class="score-label">Similarity</span>
                </div>
            `;
            container.appendChild(card);
        });
    }

    /* ==========================================
       6. HELPERS
       ========================================== */
    function capitalizeWord(word) {
        if (!word) return "";
        // Handle tags like "ci-cd" or "rest-apis"
        return word.split("-").map(part => {
            if (part === "api" || part === "apis") return "API";
            if (part === "qa") return "QA";
            if (part === "ui" || part === "ux") return "UI/UX";
            if (part === "db") return "DB";
            if (part === "ml" || part === "ai") return part.toUpperCase();
            return part.charAt(0).toUpperCase() + part.slice(1);
        }).join("-");
    }

    function capitalizeSentence(str) {
        return str.split(" ").map(w => capitalizeWord(w)).join(" ");
    }
});
