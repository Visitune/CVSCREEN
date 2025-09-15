# Analyse de CV GFSI avec référentiels structurés et exemples
import streamlit as st
import PyPDF2
import json
from datetime import datetime
from pathlib import Path
import groq
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Analyse de CV GFSI", layout="wide")
st.title("📄 Analyse comparative de CV - Auditeurs GFSI")

def afficher_jauge(titre, valeur):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valeur * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': titre},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "green" if valeur >= 0.75 else "orange" if valeur >= 0.5 else "red"},
            'steps': [
                {'range': [0, 50], 'color': "#f8d7da"},
                {'range': [50, 75], 'color': "#fff3cd"},
                {'range': [75, 100], 'color': "#d4edda"}
            ]
        }
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

def extract_valid_json(text):
    decoder = json.JSONDecoder()
    text = text.strip()
    for i in range(len(text)):
        try:
            obj, _ = decoder.raw_decode(text[i:])
            return obj
        except json.JSONDecodeError:
            continue
    return None

def create_example_referential():
    """Crée un exemple de référentiel structuré"""
    example = {
        "metadata": {
            "name": "GFSI - Auditeur Senior",
            "version": "1.0",
            "description": "Référentiel pour auditeurs seniors GFSI",
            "date_creation": "2024-01-01"
        },
        "categories": {
            "formation": {
                "name": "Formation et Certification",
                "weight": 0.3,
                "description": "Formations académiques et certifications professionnelles"
            },
            "experience": {
                "name": "Expérience Professionnelle", 
                "weight": 0.4,
                "description": "Expérience pratique en audit et sécurité alimentaire"
            },
            "competences": {
                "name": "Compétences Techniques",
                "weight": 0.2,
                "description": "Maîtrise des standards et outils d'audit"
            },
            "langues": {
                "name": "Compétences Linguistiques",
                "weight": 0.1,
                "description": "Capacités de communication internationale"
            }
        },
        "exigences": {
            "FORM_001": {
                "id": "FORM_001",
                "category": "formation",
                "title": "Formation supérieure en sécurité alimentaire",
                "description": "Diplôme Bac+5 minimum en sciences alimentaires, microbiologie, ou équivalent",
                "criteres": [
                    "Diplôme universitaire niveau Master (Bac+5) minimum",
                    "Spécialisation en sécurité alimentaire, microbiologie, ou domaine connexe",
                    "Formation continue en normes GFSI"
                ],
                "exemples_conformes": [
                    "Master en Sciences Alimentaires - Université de Lyon",
                    "Ingénieur Agronome spécialité Sécurité Alimentaire - AgroParisTech",
                    "PhD en Microbiologie Alimentaire + formations GFSI"
                ],
                "exemples_non_conformes": [
                    "BTS Agroalimentaire uniquement",
                    "Licence en biologie sans spécialisation",
                    "Formation courte en audit sans diplôme supérieur"
                ],
                "niveau_requis": "obligatoire",
                "ponderation": 1.0
            },
            "EXP_001": {
                "id": "EXP_001", 
                "category": "experience",
                "title": "Expérience minimum en audit GFSI",
                "description": "Au moins 5 ans d'expérience en audit de systèmes de management sécurité alimentaire",
                "criteres": [
                    "Minimum 5 années d'expérience en audit",
                    "Expérience dans au moins 2 standards GFSI différents",
                    "Participation à minimum 50 audits documentés"
                ],
                "exemples_conformes": [
                    "7 ans d'expérience - Lead Auditor BRC et IFS",
                    "Auditeur senior FSSC 22000 - 120 audits réalisés",
                    "10 ans audit SQF + formations continues"
                ],
                "exemples_non_conformes": [
                    "3 ans d'expérience uniquement en qualité",
                    "Expérience audit ISO 9001 sans sécurité alimentaire",
                    "Formation théorique sans pratique terrain"
                ],
                "niveau_requis": "obligatoire",
                "ponderation": 1.0
            },
            "COMP_001": {
                "id": "COMP_001",
                "category": "competences", 
                "title": "Maîtrise des standards GFSI",
                "description": "Connaissance approfondie d'au moins 2 standards GFSI reconnus",
                "criteres": [
                    "Certification dans au moins 2 standards GFSI",
                    "Connaissance des évolutions réglementaires",
                    "Capacité à interpréter les non-conformités"
                ],
                "exemples_conformes": [
                    "Certifié Lead Auditor BRC + IFS",
                    "Expert FSSC 22000 + SQF Level 2",
                    "Formateur agréé standards GFSI"
                ],
                "exemples_non_conformes": [
                    "Connaissance théorique uniquement",
                    "Certification dans un seul standard",
                    "Pas de mise à jour des certifications"
                ],
                "niveau_requis": "recommande",
                "ponderation": 0.8
            },
            "LANG_001": {
                "id": "LANG_001",
                "category": "langues",
                "title": "Compétences linguistiques internationales", 
                "description": "Maîtrise de l'anglais professionnel + une langue additionnelle",
                "criteres": [
                    "Anglais professionnel niveau C1 minimum",
                    "Capacité à rédiger des rapports d'audit en anglais",
                    "Une langue européenne additionnelle appréciée"
                ],
                "exemples_conformes": [
                    "Anglais courant + Allemand intermédiaire",
                    "Bilingue français/anglais + notions espagnol",
                    "Certifications TOEIC 900+ ou équivalent"
                ],
                "exemples_non_conformes": [
                    "Anglais scolaire uniquement",
                    "Pas de pratique professionnelle de l'anglais",
                    "Monolingue français"
                ],
                "niveau_requis": "souhaitable",
                "ponderation": 0.6
            }
        }
    }
    return example

# Sidebar config
with st.sidebar:
    st.header("🔧 Configuration")
    api_key = st.text_input("🔑 Clé API Groq :", type="password")
    
    # Bouton pour créer un exemple de référentiel
    if st.button("📝 Créer un référentiel d'exemple"):
        ref_dir = Path("referentiels")
        ref_dir.mkdir(exist_ok=True)
        example_ref = create_example_referential()
        with open(ref_dir / "exemple_auditeur_senior.json", "w", encoding="utf-8") as f:
            json.dump(example_ref, f, indent=2, ensure_ascii=False)
        st.success("✅ Référentiel d'exemple créé dans /referentiels/")
    
    if not api_key:
        st.warning("Veuillez saisir une clé API valide.")
        st.stop()

    client = groq.Client(api_key=api_key)

    @st.cache_data
    def load_referentials():
        referentials = {}
        ref_dir = Path("referentiels")
        if ref_dir.exists():
            for file in ref_dir.glob("*.json"):
                try:
                    with open(file, encoding="utf-8") as f:
                        data = json.load(f)
                        # Validation de la structure
                        if "exigences" in data:
                            referentials[file.stem] = data
                        else:
                            st.warning(f"⚠️ Structure invalide pour {file.name}")
                except Exception as e:
                    st.error(f"❌ Erreur lecture {file.name}: {e}")
        return referentials

    referentials = load_referentials()
    if not referentials:
        st.error("Aucun référentiel valide trouvé. Créez d'abord un référentiel d'exemple.")
        st.stop()

    ref_name = st.selectbox("📚 Référentiel GFSI :", list(referentials.keys()))
    selected_ref = referentials[ref_name]
    
    # Affichage des métadonnées du référentiel
    if "metadata" in selected_ref:
        metadata = selected_ref["metadata"]
        st.info(f"**{metadata.get('name', 'Sans nom')}**\n\n{metadata.get('description', '')}")
        st.caption(f"Version: {metadata.get('version', 'N/A')} | Date: {metadata.get('date_creation', 'N/A')}")

    model = st.selectbox("🧠 Modèle IA :", [
        "llama3-8b-8192", "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "kmi-k2-70b", "qwen3-72b"
    ])

# Affichage du référentiel sélectionné
if selected_ref and st.expander("👁️ Aperçu du référentiel sélectionné"):
    if "categories" in selected_ref:
        st.subheader("📋 Catégories d'exigences")
        for cat_id, cat_info in selected_ref["categories"].items():
            st.write(f"**{cat_info['name']}** (poids: {cat_info['weight']}) - {cat_info['description']}")
    
    if "exigences" in selected_ref:
        st.subheader("📝 Exigences détaillées")
        for req_id, req_info in selected_ref["exigences"].items():
            with st.expander(f"{req_id}: {req_info['title']}"):
                st.write(f"**Description:** {req_info['description']}")
                st.write(f"**Niveau:** {req_info['niveau_requis']} | **Pondération:** {req_info['ponderation']}")
                
                st.write("**Critères:**")
                for critere in req_info.get("criteres", []):
                    st.write(f"• {critere}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("✅ **Exemples conformes:**")
                    for ex in req_info.get("exemples_conformes", []):
                        st.write(f"• {ex}")
                
                with col2:
                    st.write("❌ **Exemples non conformes:**")
                    for ex in req_info.get("exemples_non_conformes", []):
                        st.write(f"• {ex}")

# Fichiers PDF
uploaded_files = st.file_uploader("📄 Chargez un ou plusieurs CV (PDF uniquement)", type=["pdf"], accept_multiple_files=True)

if uploaded_files and st.button("🔍 Lancer l'analyse IA"):
    results_all = []
    details_export = []

    with st.spinner("Analyse des CV en cours..."):
        for uploaded_file in uploaded_files:
            try:
                uploaded_file.seek(0)
                reader = PyPDF2.PdfReader(uploaded_file)
                cv_text = " ".join([page.extract_text() or "" for page in reader.pages])

                # Construction du prompt enrichi avec exemples
                exigences_detail = ""
                for req_id, req_info in selected_ref["exigences"].items():
                    exigences_detail += f"""
EXIGENCE {req_id}: {req_info['title']}
Description: {req_info['description']}
Niveau: {req_info['niveau_requis']} | Pondération: {req_info['ponderation']}

Critères d'évaluation:
{chr(10).join(['• ' + c for c in req_info.get('criteres', [])])}

Exemples CONFORMES (à rechercher dans le CV):
{chr(10).join(['• ' + ex for ex in req_info.get('exemples_conformes', [])])}

Exemples NON CONFORMES (éléments insuffisants):
{chr(10).join(['• ' + ex for ex in req_info.get('exemples_non_conformes', [])])}
---"""

                prompt = f"""
Tu es un expert en conformité GFSI avec 15 ans d'expérience.
Analyse le CV ci-dessous en évaluant CHAQUE EXIGENCE du référentiel.

MÉTHODOLOGIE D'ANALYSE:
1. Pour chaque exigence, recherche dans le CV les éléments correspondant aux critères
2. Compare avec les exemples conformes/non conformes fournis
3. Attribue un statut: ✅ CONFORME, ⚠️ À CHALLENGER, ou ❌ NON CONFORME
4. Justifie ta décision en citant les éléments précis du CV
5. Indique un score de confiance (0 à 1) basé sur la clarté des informations

RÉFÉRENTIEL DÉTAILLÉ:
{exigences_detail}

CV DU CANDIDAT À ANALYSER:
{cv_text}

IMPORTANT: Base-toi uniquement sur les informations présentes dans le CV. Si une information n'est pas claire ou absente, marque comme "À CHALLENGER".

Répond UNIQUEMENT avec un objet JSON strictement valide :
{{
  "analysis": [
    {{
      "exigence_id": "FORM_001",
      "exigence_titre": "Formation supérieure en sécurité alimentaire",
      "statut": "CONFORME / À CHALLENGER / NON CONFORME",
      "justification": "justification précise basée sur les éléments du CV",
      "elements_cv": "citation exacte des éléments pertinents du CV",
      "confiance": 0.85,
      "niveau_requis": "obligatoire",
      "ponderation": 1.0
    }}
  ],
  "score_global": 0.75,
  "synthese": "résumé des points forts et points d'attention avec recommandations actionables"
}}
"""

                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=4000
                )

                result = response.choices[0].message.content.strip()
                result_data = extract_valid_json(result)
                if not result_data:
                    st.error(f"⚠️ JSON invalide pour {uploaded_file.name}")
                    continue

                analysis = result_data.get("analysis", [])
                for a in analysis:
                    a["cv"] = uploaded_file.name
                    details_export.append(a)

                # Calculs avec pondération
                score_pondere = 0
                poids_total = 0
                conformes = challengers = non_conformes = 0
                
                for item in analysis:
                    statut = item.get("statut", "").upper()
                    ponderation = item.get("ponderation", 1.0)
                    confiance = item.get("confiance", 0)
                    
                    if statut == "CONFORME":
                        conformes += 1
                        score_pondere += confiance * ponderation
                    elif "CHALLENGER" in statut:
                        challengers += 1
                        score_pondere += (confiance * 0.5) * ponderation
                    else:
                        non_conformes += 1
                    
                    poids_total += ponderation

                score_final = score_pondere / poids_total if poids_total > 0 else 0

                results_all.append({
                    "nom": uploaded_file.name,
                    "conformes": conformes,
                    "challengers": challengers,
                    "non_conformes": non_conformes,
                    "score": round(score_final, 2),
                    "score_global": result_data.get("score_global", score_final),
                    "details": analysis,
                    "synthese": result_data.get("synthese", "")
                })

            except Exception as e:
                st.error(f"❌ Erreur pour {uploaded_file.name} : {e}")

    # Affichage des résultats amélioré
    if results_all:
        # Tableau comparatif
        st.subheader("📊 Comparaison des candidats")
        comparison_df = pd.DataFrame([{
            "Candidat": r["nom"],
            "Score Global": f"{r['score']:.0%}",
            "✅ Conformes": r["conformes"],
            "⚠️ À challenger": r["challengers"], 
            "❌ Non conformes": r["non_conformes"]
        } for r in results_all])
        st.dataframe(comparison_df, use_container_width=True)

        # Détails par candidat
        for result in results_all:
            st.subheader(f"📄 Analyse détaillée : {result['nom']}")
            
            # Score global avec jauge
            col1, col2 = st.columns([1, 2])
            with col1:
                afficher_jauge("Score Global", result["score"])
            with col2:
                st.markdown("### 🧠 Synthèse IA")
                st.info(result["synthese"])

            # Détail par catégorie
            df = pd.DataFrame(result["details"])
            if "categories" in selected_ref:
                st.markdown("### 📋 Analyse par catégorie")
                for cat_id, cat_info in selected_ref["categories"].items():
                    cat_exigences = df[df["exigence_id"].str.startswith(cat_id.upper()[:4])]
                    if not cat_exigences.empty:
                        with st.expander(f"{cat_info['name']} ({len(cat_exigences)} exigences)"):
                            for _, row in cat_exigences.iterrows():
                                status_emoji = {"CONFORME": "✅", "À CHALLENGER": "⚠️", "NON CONFORME": "❌"}
                                emoji = status_emoji.get(row["statut"], "❓")
                                
                                st.write(f"{emoji} **{row['exigence_titre']}**")
                                st.write(f"*Justification:* {row['justification']}")
                                if row.get('elements_cv'):
                                    st.write(f"*Éléments du CV:* {row['elements_cv']}")
                                st.write(f"*Confiance:* {row['confiance']:.0%}")
                                st.divider()

        # Export des résultats
        if st.button("📥 Exporter les résultats détaillés"):
            export_df = pd.DataFrame(details_export)
            csv = export_df.to_csv(index=False, encoding="utf-8")
            st.download_button(
                label="💾 Télécharger CSV", 
                data=csv, 
                file_name=f"analyse_cv_gfsi_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

# Instructions d'utilisation
with st.expander("📚 Structure du référentiel JSON"):
    st.code("""
{
  "metadata": {
    "name": "Nom du référentiel",
    "version": "1.0", 
    "description": "Description du référentiel",
    "date_creation": "2024-01-01"
  },
  "categories": {
    "formation": {
      "name": "Formation et Certification",
      "weight": 0.3,
      "description": "Description de la catégorie"
    }
  },
  "exigences": {
    "FORM_001": {
      "id": "FORM_001",
      "category": "formation",
      "title": "Titre de l'exigence",
      "description": "Description détaillée",
      "criteres": ["Critère 1", "Critère 2"],
      "exemples_conformes": ["Exemple 1", "Exemple 2"],
      "exemples_non_conformes": ["Contre-exemple 1"],
      "niveau_requis": "obligatoire|recommande|souhaitable",
      "ponderation": 1.0
    }
  }
}
    """, language="json")
