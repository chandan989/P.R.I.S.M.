/**
 * Pre-filled demo query strings for the Demo page scenarios.
 * These are NOT mock data — they are sent to the live backend.
 */
export const demoQueries = {
  polypharmacy: `Patient: 78F, eGFR 52
Regimen:
- Warfarin 5mg daily
- Clarithromycin 500mg BID (new, 7-day course)
- Atorvastatin 40mg daily
- Metformin 1000mg BID
- Omeprazole 20mg daily
- Lisinopril 10mg daily
- Amlodipine 5mg daily
- Metoprolol 50mg BID
- Furosemide 40mg daily
- Levothyroxine 75mcg daily
- Sertraline 50mg daily
- Tramadol 50mg PRN
- Aspirin 81mg daily
- Vitamin D3 2000 IU daily
- Calcium carbonate 500mg BID

Audit for clinically significant interactions.`,
  cyp450: `Patient on:
- Warfarin 5mg
- Fluconazole 200mg
- Amiodarone 200mg

Analyze CYP450 metabolic competition and predicted INR impact.`,
  glp1: `Patient on Warfarin 5mg daily, considering initiation of Semaglutide 0.5mg weekly for T2DM.
What does emerging evidence suggest about pharmacokinetic interaction?`,
};
