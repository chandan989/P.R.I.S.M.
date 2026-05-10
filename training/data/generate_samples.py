import json
import random
import os

random.seed(42)

ages = list(range(35, 90))
genders = ["male", "female"]

interactions = [
    {
        "drug_a_class": ["Warfarin", "Rivaroxaban", "Apixaban", "Dabigatran"],
        "ind_a": ["AFib", "DVT", "PE", "VTE prophylaxis"],
        "drug_b_class": ["Ibuprofen", "Naproxen", "Diclofenac", "Celecoxib", "Meloxicam"],
        "ind_b": ["osteoarthritis", "acute back pain", "gout flare", "rheumatoid arthritis"],
        "mechanism": "NSAIDs inhibit COX-1/COX-2 leading to platelet dysfunction and direct gastric mucosal injury. Combined with an anticoagulant, this creates a profound synergistic risk for gastrointestinal hemorrhage without necessarily altering the PT/INR (for DOACs) or with only minor changes.",
        "consequence": "Severe gastrointestinal bleeding",
        "support_a": "Multiple large observational studies confirm a 2- to 3-fold increased risk of major GI bleeding when NSAIDs are added to anticoagulants.",
        "weaken_a": "Short-term use (e.g., 1-2 days) might not precipitate an immediate bleed in patients with healthy mucosa.",
        "support_b": "If the patient uses a PPI, the gastric mucosal risk might be partially mitigated.",
        "weaken_b": "PPIs do not prevent lower GI bleeds or reverse the platelet inhibition synergy.",
        "discarded": "NSAIDs induce the metabolism of the anticoagulant. (Incorrect; the interaction is primarily pharmacodynamic, not pharmacokinetic via CYP enzymes).",
        "claim": "Combining NSAIDs with anticoagulants significantly increases the risk of major gastrointestinal bleeding through additive pharmacodynamic effects",
        "emoji": "🔴",
        "confidence": "✅ HIGH",
        "recommendation": "Avoid this combination. Discontinue the NSAID and recommend Acetaminophen for analgesia. If NSAID therapy is absolutely mandatory, use the lowest effective dose for the shortest duration and add a PPI, while monitoring closely for signs of bleeding."
    },
    {
        "drug_a_class": ["Atorvastatin", "Simvastatin", "Lovastatin"],
        "ind_a": ["hyperlipidemia", "dyslipidemia", "post-MI secondary prevention"],
        "drug_b_class": ["Clarithromycin", "Erythromycin", "Itraconazole", "Ketoconazole"],
        "ind_b": ["respiratory tract infection", "systemic fungal infection", "skin infection"],
        "mechanism": "The prescribed anti-infective is a potent inhibitor of CYP3A4. The statin is extensively metabolized by CYP3A4. Inhibition leads to a massive (often 4- to 10-fold) increase in statin systemic exposure (AUC).",
        "consequence": "Rhabdomyolysis and acute renal failure",
        "support_a": "Strongly supported by pharmacokinetic data and numerous FDA black-box warnings and case reports of fatal rhabdomyolysis.",
        "weaken_a": "Some patients with high baseline muscle mass or robust alternative metabolic pathways may tolerate short courses without overt rhabdo.",
        "support_b": "The antibiotic course is short (e.g., 7 days).",
        "weaken_b": "Even a 7-day course of a potent CYP3A4 inhibitor is sufficient to cause toxic accumulation of the statin and trigger muscle breakdown.",
        "discarded": "The statin inhibits the clearance of the antibiotic. (Incorrect; the interaction direction is the antibiotic inhibiting statin clearance).",
        "claim": "Potent CYP3A4 inhibitors cause a dangerous increase in the systemic exposure of CYP3A4-metabolized statins, leading to rhabdomyolysis",
        "emoji": "🔴",
        "confidence": "✅ HIGH",
        "recommendation": "Mandatory hold of the statin for the duration of the anti-infective therapy. Restart the statin 3 days after the last dose of the antibiotic/antifungal."
    },
    {
        "drug_a_class": ["Lisinopril", "Enalapril", "Ramipril", "Valsartan", "Losartan"],
        "ind_a": ["hypertension", "heart failure", "diabetic nephropathy"],
        "drug_b_class": ["Spironolactone", "Eplerenone"],
        "ind_b": ["heart failure with reduced ejection fraction", "resistant hypertension"],
        "mechanism": "Both agents independently promote potassium retention. ACEi/ARBs decrease aldosterone production, and MRAs directly block the mineralocorticoid receptor in the distal tubule.",
        "consequence": "Severe hyperkalemia leading to cardiac arrhythmias",
        "support_a": "Well-documented additive pharmacodynamic effect on renal potassium handling. Guidelines mandate close monitoring when this combination is initiated.",
        "weaken_a": "In patients with robust baseline eGFR and concurrent use of loop diuretics, the potassium rise may be offset.",
        "support_b": "The combination is standard-of-care and mortality-reducing in HFrEF.",
        "weaken_b": "While mortality-reducing, the absolute risk of hyperkalemia remains very high and requires strict protocolized monitoring.",
        "discarded": "MRAs induce the metabolism of ACE inhibitors. (Incorrect; the interaction is purely a pharmacodynamic synergy at the renal level).",
        "claim": "Combining RAAS inhibitors with MRAs causes additive potassium retention and significant risk of hyperkalemia",
        "emoji": "🟡",
        "confidence": "✅ HIGH",
        "recommendation": "Monitor serum potassium and creatinine within 3-7 days of initiation or dose titration. Advise the patient to adhere to a low-potassium diet and avoid potassium-containing salt substitutes."
    },
    {
        "drug_a_class": ["Sertraline", "Fluoxetine", "Citalopram", "Escitalopram", "Paroxetine"],
        "ind_a": ["major depressive disorder", "generalized anxiety disorder", "OCD"],
        "drug_b_class": ["Linezolid", "Tranylcypromine", "Phenelzine", "Methylene Blue"],
        "ind_b": ["VRE pneumonia", "treatment-resistant depression", "severe infection"],
        "mechanism": "The second drug possesses non-selective Monoamine Oxidase Inhibitor (MAOI) activity. Combining an MAOI with a Selective Serotonin Reuptake Inhibitor (SSRI) blocks both serotonin reuptake and degradation, leading to massive synaptic serotonin accumulation.",
        "consequence": "Life-threatening Serotonin Syndrome",
        "support_a": "Class contraindication. Numerous fatal case reports exist when linezolid or traditional MAOIs are mixed with SSRIs. Symptoms include hyperthermia, clonus, and altered mental status.",
        "weaken_a": "None. This is an absolute contraindication.",
        "support_b": "The SSRI dose is extremely low.",
        "weaken_b": "Even low doses of SSRIs can trigger fatal Serotonin Syndrome when paired with an MAOI due to the complete blockade of serotonin clearance.",
        "discarded": "The MAOI induces CYP450 enzymes leading to SSRI withdrawal. (Incorrect; the interaction is a pharmacodynamic crisis, not a pharmacokinetic reduction).",
        "claim": "Combining SSRIs with MAOIs (or drugs with MAOI activity like Linezolid) precipitates life-threatening Serotonin Syndrome",
        "emoji": "🔴",
        "confidence": "✅ HIGH",
        "recommendation": "ABSOLUTE CONTRAINDICATION. Immediately discontinue the SSRI if the MAOI/Linezolid is required. A washout period of 14 days (5 weeks for Fluoxetine) is required before starting an MAOI. Consider alternative non-serotonergic therapies."
    },
    {
        "drug_a_class": ["Sildenafil", "Tadalafil", "Vardenafil"],
        "ind_a": ["erectile dysfunction", "pulmonary arterial hypertension"],
        "drug_b_class": ["Nitroglycerin", "Isosorbide Mononitrate", "Isosorbide Dinitrate"],
        "ind_b": ["stable angina", "acute coronary syndrome"],
        "mechanism": "Nitrates act as exogenous nitric oxide (NO) donors, stimulating guanylate cyclase to produce cGMP. PDE5 inhibitors prevent the breakdown of cGMP. The combination causes an unregulated, massive accumulation of cGMP in vascular smooth muscle.",
        "consequence": "Profound, refractory hypotension and cardiovascular collapse",
        "support_a": "Universally recognized fatal interaction. The profound vasodilation cannot be easily reversed with standard pressors or fluids.",
        "weaken_a": "None.",
        "support_b": "The nitrate is formulated as a topical patch, which might have slower absorption.",
        "weaken_b": "All formulations of nitrates (sublingual, oral, topical) carry the exact same contraindication due to systemic NO delivery.",
        "discarded": "Nitrates inhibit the hepatic clearance of PDE5 inhibitors. (Incorrect; this is a purely pharmacodynamic, synergistic pathway interaction).",
        "claim": "Concurrent use of PDE5 inhibitors and organic nitrates causes massive cGMP accumulation and fatal hypotension",
        "emoji": "🔴",
        "confidence": "✅ HIGH",
        "recommendation": "ABSOLUTE CONTRAINDICATION. Do not administer nitrates within 24 hours of Sildenafil/Vardenafil or 48 hours of Tadalafil. If the patient presents with acute chest pain, alternative anti-anginals (e.g., non-DHP CCBs, beta-blockers) must be utilized."
    },
    {
        "drug_a_class": ["Methotrexate"],
        "ind_a": ["rheumatoid arthritis", "psoriasis", "severe Crohn's"],
        "drug_b_class": ["Trimethoprim/Sulfamethoxazole", "Trimethoprim"],
        "ind_b": ["urinary tract infection", "Pneumocystis jirovecii prophylaxis"],
        "mechanism": "Both methotrexate and trimethoprim are dihydrofolate reductase (DHFR) inhibitors. Their concurrent use creates a synergistic blockade of folate metabolism, severely disrupting DNA synthesis in rapidly dividing cells.",
        "consequence": "Severe bone marrow suppression (pancytopenia) and mucositis",
        "support_a": "Extensive clinical literature shows rapid onset of severe megaloblastic anemia and pancytopenia when low-dose MTX is combined with TMP/SMX.",
        "weaken_a": "Folic acid supplementation might offer a minor protective buffer.",
        "support_b": "The TMP/SMX is only prescribed for a 3-day UTI course.",
        "weaken_b": "Even short courses of dual DHFR inhibition have resulted in fatal bone marrow aplasia.",
        "discarded": "TMP/SMX induces the metabolism of methotrexate. (Incorrect; MTX is eliminated renally, and the interaction is pharmacodynamic synergy at the DHFR enzyme).",
        "claim": "Synergistic inhibition of dihydrofolate reductase by Methotrexate and Trimethoprim causes profound bone marrow suppression",
        "emoji": "🔴",
        "confidence": "✅ HIGH",
        "recommendation": "Avoid this combination. Utilize alternative antibiotics for the UTI (e.g., Nitrofurantoin, Fosfomycin, or a Cephalosporin). If concurrent use is unavoidable (e.g., PJP prophylaxis), intensive monitoring of CBC and rescue with Leucovorin may be necessary."
    },
    {
        "drug_a_class": ["Amiodarone", "Dofetilide", "Sotalol"],
        "ind_a": ["atrial fibrillation", "ventricular tachycardia"],
        "drug_b_class": ["Ondansetron", "Haloperidol", "Methadone", "Moxifloxacin"],
        "ind_b": ["severe nausea", "acute psychosis", "opioid use disorder", "community-acquired pneumonia"],
        "mechanism": "Both agents block the delayed rectifier potassium current (IKr) in cardiac myocytes, which is responsible for ventricular repolarization. This leads to additive prolongation of the QT interval on the ECG.",
        "consequence": "Torsades de Pointes (TdP) and sudden cardiac death",
        "support_a": "Additive QTc prolongation is highly predictable and dose-dependent. Both agents are on the CredibleMeds list of drugs with a known risk of TdP.",
        "weaken_a": "Patient may have a normal baseline QTc and normal electrolytes (K+, Mg++), reducing the immediate risk of arrhythmia.",
        "support_b": "The secondary agent is only given as a single PRN dose.",
        "weaken_b": "Amiodarone has an extremely long half-life, so its background QTc effect is constant; a single dose of another QT-prolonging drug can still trigger TdP if the threshold is crossed.",
        "discarded": "The antiarrhythmic induces the clearance of the secondary drug. (Incorrect; the primary danger is pharmacodynamic synergy on the cardiac potassium channels).",
        "claim": "Combining multiple drugs that block IKr leads to additive QTc prolongation and high risk of Torsades de Pointes",
        "emoji": "🔴",
        "confidence": "✅ HIGH",
        "recommendation": "Avoid combination if possible. Obtain a baseline ECG. If the QTc is >450ms (males) or >470ms (females), alternative therapies must be used. Correct any hypokalemia or hypomagnesemia prior to administration."
    },
    {
        "drug_a_class": ["Tacrolimus", "Cyclosporine"],
        "ind_a": ["renal transplant prophylaxis", "hepatic transplant prophylaxis"],
        "drug_b_class": ["Diltiazem", "Verapamil"],
        "ind_b": ["hypertension", "rate control in AFib"],
        "mechanism": "Non-DHP calcium channel blockers (Diltiazem/Verapamil) are moderate inhibitors of both CYP3A4 and P-glycoprotein (P-gp). Calcineurin inhibitors (Tacrolimus/Cyclosporine) are highly sensitive substrates of both pathways. Inhibition reduces their clearance significantly.",
        "consequence": "Calcineurin inhibitor toxicity (nephrotoxicity, neurotoxicity)",
        "support_a": "Well-characterized pharmacokinetic interaction. Exposure of tacrolimus/cyclosporine can increase by 50-100%, rapidly crossing the narrow therapeutic window.",
        "weaken_a": "This interaction is sometimes utilized intentionally by transplant centers to reduce the required dose (and cost) of the calcineurin inhibitor.",
        "support_b": "The interaction is stable and predictable.",
        "weaken_b": "It is only stable if the doses are tightly managed; initiating the CCB without a preemptive dose reduction of the CNI almost guarantees acute toxicity.",
        "discarded": "Diltiazem directly damages the kidneys synergistically with Tacrolimus. (Incorrect; while nephrotoxicity occurs, it is secondary to the PK-driven accumulation of Tacrolimus, not direct CCB toxicity).",
        "claim": "Non-DHP CCBs inhibit CYP3A4 and P-gp, significantly increasing calcineurin inhibitor systemic exposure and toxicity",
        "emoji": "🟡",
        "confidence": "✅ HIGH",
        "recommendation": "Preemptive dose reduction of the calcineurin inhibitor (often by 30-50%) is required upon initiating Diltiazem or Verapamil. Monitor CNI trough levels and serum creatinine within 3-5 days."
    },
    {
        "drug_a_class": ["Carbamazepine", "Phenytoin", "Phenobarbital"],
        "ind_a": ["focal seizures", "epilepsy", "trigeminal neuralgia"],
        "drug_b_class": ["Ethinyl Estradiol/Levonorgestrel", "Ethinyl Estradiol/Norethindrone"],
        "ind_b": ["oral contraception", "polycystic ovary syndrome"],
        "mechanism": "The antiepileptic drug is a broad-spectrum, potent inducer of hepatic CYP3A4 and UGT enzymes. This greatly accelerates the metabolism and clearance of both the estrogen and progestin components of the oral contraceptive.",
        "consequence": "Contraceptive failure and unintended pregnancy",
        "support_a": "Highly reliable PK induction. Clinical evidence shows a drastic reduction in hormone AUC, leading to breakthrough bleeding and loss of ovulation suppression.",
        "weaken_a": "Very high-dose estrogen formulations (e.g., 50mcg) might retain some efficacy, though rarely used today.",
        "support_b": "The patient has been on the OCP for years and has stable cycles.",
        "weaken_b": "Past stability on the OCP alone is irrelevant once a potent enzyme inducer is introduced; hepatic induction occurs within 1-2 weeks.",
        "discarded": "The OCP reduces the seizure threshold directly. (Incorrect; while estrogens can have minor proconvulsant effects, the primary clinical danger is the PK-driven failure of the contraceptive).",
        "claim": "Broad-spectrum CYP3A4 inducers accelerate the metabolism of oral contraceptives, leading to loss of efficacy",
        "emoji": "🔴",
        "confidence": "✅ HIGH",
        "recommendation": "Standard oral contraceptives are unreliable with this antiepileptic. The patient must transition to a highly effective non-hormonal method (e.g., Copper IUD) or a progestin-releasing IUD/depot injection, as their systemic levels are less critical for local efficacy."
    },
    {
        "drug_a_class": ["Lithium"],
        "ind_a": ["bipolar I disorder", "bipolar maintenance", "acute mania"],
        "drug_b_class": ["Hydrochlorothiazide", "Chlorthalidone"],
        "ind_b": ["hypertension", "peripheral edema"],
        "mechanism": "Thiazide diuretics induce sodium depletion and volume contraction. The kidneys compensate by increasing sodium reabsorption in the proximal tubule. Because lithium is handled similarly to sodium, lithium reabsorption is also drastically increased, reducing its clearance.",
        "consequence": "Acute lithium toxicity (neurotoxicity, ataxia, arrhythmias)",
        "support_a": "Textbook pharmacokinetic interaction. Thiazides predictably reduce lithium clearance by 25% to 40%, easily pushing serum levels into the toxic range (>1.5 mEq/L).",
        "weaken_a": "Loop diuretics have a less pronounced and more variable effect on lithium clearance compared to thiazides.",
        "support_b": "The patient is on a very low dose of HCTZ (12.5mg).",
        "weaken_b": "Even low doses of thiazides reliably induce enough proximal tubule compensation to significantly elevate lithium levels.",
        "discarded": "Thiazides inhibit the hepatic metabolism of lithium. (Incorrect; lithium is not metabolized by the liver, it is 100% renally excreted).",
        "claim": "Thiazide diuretics reduce renal clearance of lithium by promoting proximal tubule reabsorption, causing severe toxicity",
        "emoji": "🔴",
        "confidence": "✅ HIGH",
        "recommendation": "Avoid thiazide diuretics in patients on lithium if possible (use amlodipine or a beta-blocker for hypertension). If HCTZ is strictly necessary, preemptively reduce the lithium dose by 25-50% and monitor serum lithium levels twice weekly until stable."
    }
]

generated_samples = []

for i in range(500):
    age = random.choice(ages)
    gender = random.choice(genders)
    template = random.choice(interactions)
    
    drug_a = random.choice(template["drug_a_class"])
    ind_a = random.choice(template["ind_a"])
    drug_b = random.choice(template["drug_b_class"])
    ind_b = random.choice(template["ind_b"])
    
    instruction = f"Patient is a {age}yo {gender} taking {drug_a} for {ind_a}. A new prescription for {drug_b} is being considered for {ind_b}. Evaluate the interaction risk."
    
    comp_a_pct = round(random.uniform(90.0, 99.0), 1)
    comp_b_pct = round(100.0 - comp_a_pct, 1)
    
    thought_process = f"""[Logical Chain]
1. Target drugs: {drug_a} and {drug_b}.
2. Clinical Indication: {ind_a} and {ind_b}.
3. Pharmacological Mechanism: {template['mechanism']}
4. Resulting Complication: {template['consequence']}
5. Severity Analysis: {template['emoji']} implies high clinical impact.

[Competing Hypotheses]
Interpretation A: Severe risk of {template['consequence']} [{comp_a_pct}%]
├── Supporting: {template['support_a']}
└── Weakening: {template['weaken_a']}

Interpretation B: Manageable or minor clinical impact [{comp_b_pct}%]
├── Supporting: {template['support_b']}
└── Weakening: {template['weaken_b']}

[Discarded Paths]
✗ Discarded: {template['discarded']}

▶ Selected: Interpretation A
<|tool_call>verify_claim<|"{template['claim']}"|>"""

    output = f"{template['emoji']} {template['consequence']}.\n\nConfidence: {template['confidence']}\n\nRecommendation: {template['recommendation']}"

    sample = {
        "instruction": instruction,
        "thought_process": thought_process,
        "output": output
    }
    
    generated_samples.append(sample)

with open("training/data/deliberation_dataset_clean.json", "r") as f:
    existing_data = json.load(f)

existing_data.extend(generated_samples)

with open("training/data/deliberation_dataset.json", "w") as f:
    json.dump(existing_data, f, indent=2)

print(f"Successfully appended 500 samples. Total samples: {len(existing_data)}")
