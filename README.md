# 8. FinOps Engine — Optimisation des Coûts Cloud Data

**Stack :** Terraform, Python, BigQuery/Snowflake, Kubernetes, Argo Workflows, Streamlit, ClickHouse  
**Niveau :** Avancé | **Budget :** $500K/mois d'infra data à optimiser

## Contexte Métier
Entreprise dépensant $500K/mois en infrastructure data. Besoin d'un moteur d'optimisation des coûts automatisé.

## Ce que tu dois construire

### Cost Collector
- APIs multi-cloud (AWS Cost Explorer, GCP Billing, Azure Cost Management)
- Enrichissement : owner, projet, environnement
- Stockage ClickHouse pour analytics temps réel

### Analytics Engine
- Tagging compliance : % ressources non taggées, suggestions
- Anomaly detection : spikes, tendances
- Idle resources : clusters inactifs, volumes orphelins
- Right-sizing recommendations
- Reserved Instance / Savings Plan optimization

### Data Cost Attribution
- Cost par requête (BigQuery slots, Snowflake credits)
- Showback/Chargeback par team, projet, pipeline

### Automation Engine (Argo Workflows)
- Auto-stop des clusters idle à 19h
- Downsize des resources over-provisionned
- Budget enforcement (alerte → auto-stop)
- Policy-as-code

### Prédiction
- Time series forecasting
- Budget tracking temps réel
- What-if scenarios

### Difficultés Techniques
- API rate limits et pagination
- Cost attribution précise ressources partagées
- False positives dans les anomalies
- Safeguards automation (pas toucher à la prod)

## Structure attendue
```
src/
├── collector/          # Multi-cloud cost APIs
├── analytics/          # Anomaly detection + recommendations
├── automation/         # Argo workflows de remediation
├── dashboard/          # Streamlit FinOps dashboard
├── forecasting/        # Time series prediction
└── policies/           # Policy-as-code rules
```
