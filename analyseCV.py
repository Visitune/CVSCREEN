# Analyse de CV - GFSI (version avec vérification JSON et affichage brut)
# Nom du fichier : analyse_cv_gfsi.py

import streamlit as st
import PyPDF2
import json
from datetime import datetime
from pathlib import Path
import groq
import pandas as pd

# Configuration Streamlit
st.set_page_config(page_title="Analyse de CV GFSI", layout="wide")
st.title("📄 Analyse automatisée de CV - Auditeurs GFSI")

# Clé API GROQ
api_key = st.text_input("🔑 Clé API Groq :", type="password")
if not api_key:
    st.warning("Veuillez saisir une clé API valide.")
    st.stop()

client = groq.Client(api_key=api_key)

# Chargement des référentiels
@st.cache_data
def load_referentials():
    referentials = {}
    ref_dir = Path("referentiels")
    for file in ref_dir.glob("*.json"):
        with open(file, encoding="utf-8") as f:
            referentials[file.stem] = json.load(f)
    return referentials

referentials = load_referentials()
if not referentials:
    st.error("Aucun référentiel trouvé dans le dossier 'referentiels'.")
    st.stop()

# Sélection du référentiel
ref_name = st.selectbox("📚 Sélectionnez un référentiel GFSI :", list(referentials.keys()))
selected_ref = referentials[ref_name]

# Modèle IA
model = st.selectbox("🧠 Choisissez le modèle IA :", [
    "llama3-8b-8192",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "kmi-k2-70b",
    "qwen3-72b"
])

# Téléversement du CV
uploaded_file = st.file_uploader("📄 Chargez un CV (PDF uniquement)", type=["pdf"])

if uploaded_file:
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        cv_text = " ".join([page.extract_text() or "" for page in reader.pages])
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")
        st.stop()

    # Construction du prompt avec instruction stricte
    prompt = f"""
Tu es un expert en conformité IFS.
Analyse le CV ci-dessous en comparant CHAQUE EXIGENCE du référentiel IFS une par une.
Pour chaque exigence :
- indique si elle est ✅ CONFORME, ⚠️ À CHALLENGER, ou ❌ NON CONFORME
- fournis une justification brève (données du CV)
- indique un score de confiance (0 à 1)

RÉFÉRENTIEL IFS :
{json.dumps(selected_ref, indent=2)}

CV DU CANDIDAT :
{cv_text}

Tu dois répondre UNIQUEMENT avec un objet JSON strictement valide, sans texte avant ou après, au format suivant :
{{
  "analysis": [
    {{
      "exigence": "...",
      "statut": "CONFORME / À CHALLENGER / NON CONFORME",
      "justification": "...",
      "confiance": 0.85
    }}
  ],
  "synthese": "résumé clair à communiquer au candidat"
}}
"""

    if st.button("🔍 Lancer l'analyse IA"):
        with st.spinner("Analyse du CV en cours..."):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.choices[0].message.content.strip()
                st.success("✅ Analyse terminée")

                st.markdown("### 🧾 Aperçu brut du résultat IA")
                st.code(result, language="text")

                try:
                    result_data = json.loads(result)
                    analysis = result_data.get("analysis", [])

                    # Compter les statuts
                    conformes = sum(1 for i in analysis if i.get("statut", "").upper() == "CONFORME")
                    challengers = sum(1 for i in analysis if i.get("statut", "").upper() == "À CHALLENGER")
                    non_conformes = sum(1 for i in analysis if i.get("statut", "").upper() == "NON CONFORME")

                    st.markdown("## 📊 Répartition des statuts")
                    st.bar_chart({
                        "Statut": ["✅ Conformes", "⚠️ À challenger", "❌ Non conformes"],
                        "Nombre": [conformes, challengers, non_conformes]
                    })

                    st.markdown("## 📋 Détail par exigence")
                    for item in analysis:
                        statut = item.get("statut", "")
                        couleur = {
                            "CONFORME": "#d4edda",
                            "À CHALLENGER": "#fff3cd",
                            "NON CONFORME": "#f8d7da"
                        }.get(statut.upper(), "#e2e3e5")
                        st.markdown(
                            f"""
                            <div style='background-color:{couleur}; padding:15px; border-radius:8px; margin-bottom:10px;'>
                            <strong>Exigence :</strong> {item['exigence']}<br>
                            <strong>Statut :</strong> {item['statut']}<br>
                            <strong>Confiance :</strong> {item['confiance']}<br>
                            <strong>Justification :</strong> {item['justification']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    st.markdown("## 📝 Synthèse pour le candidat")
                    st.success(result_data.get("synthese", "Aucune synthèse disponible."))

                except json.JSONDecodeError:
                    st.error("❌ Erreur : la réponse n'est pas un JSON valide. Copie brute ci-dessus.")

            except Exception as e:
                st.error(f"Erreur pendant l'analyse IA : {e}")

# Administration (mode développeur)
with st.expander("🔐 Mode administration - Création de référentiels IA"):
    admin_pwd = st.text_input("Mot de passe admin :", type="password")
    if admin_pwd == "admin123":
        texte = st.text_area("📋 Collez ici les exigences du nouveau référentiel :")
        if st.button("🤖 Générer référentiel JSON"):
            prompt_ref = f"Crée un JSON structuré pour ce référentiel GFSI :\n{texte}"
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt_ref}]
                )
                json_ref = response.choices[0].message.content.strip()
                st.code(json_ref, language="json")
            except Exception as e:
                st.error(f"Erreur IA : {e}")
    else:
        st.info("Mot de passe requis pour accéder à ce module.")
