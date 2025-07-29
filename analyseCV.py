# Analyse de CV - GFSI (multi-CV avec comparaison)

import streamlit as st
import PyPDF2
import json
import re
from datetime import datetime
from pathlib import Path
import groq
import pandas as pd

st.set_page_config(page_title="Analyse de CV GFSI", layout="wide")
st.title("📄 Analyse comparative de CV - Auditeurs GFSI")

api_key = st.text_input("🔑 Clé API Groq :", type="password")
if not api_key:
    st.warning("Veuillez saisir une clé API valide.")
    st.stop()

client = groq.Client(api_key=api_key)

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

ref_name = st.selectbox("📚 Sélectionnez un référentiel GFSI :", list(referentials.keys()))
selected_ref = referentials[ref_name]

model = st.selectbox("🧠 Choisissez le modèle IA :", [
    "llama3-8b-8192",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "kmi-k2-70b",
    "qwen3-72b"
])

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
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.choices[0].message.content.strip()
                json_start = result.find('{')
                json_str = result[json_start:]
                json_str = re.sub(r'```json|```', '', json_str).strip()
                result_data = json.loads(json_str)
                analysis = result_data.get("analysis", [])
                for a in analysis:
                    a["cv"] = uploaded_file.name
                    details_export.append(a)
                conformes = sum(1 for i in analysis if i.get("statut", "").upper() == "CONFORME")
                challengers = sum(1 for i in analysis if i.get("statut", "").upper() == "À CHALLENGER")
                non_conformes = sum(1 for i in analysis if i.get("statut", "").upper() == "NON CONFORME")
                score_moyen = round(sum(i.get("confiance", 0) for i in analysis) / len(analysis), 2) if analysis else 0
                results_all.append({
                    "nom": uploaded_file.name,
                    "conformes": conformes,
                    "challengers": challengers,
                    "non_conformes": non_conformes,
                    "score": score_moyen,
                    "details": analysis,
                    "synthese": result_data.get("synthese", "")
                })
            except Exception as e:
                st.error(f"Erreur pour {uploaded_file.name} : {e}")

    if results_all:
        st.markdown("## 📊 Comparaison entre CVs")
        df_compare = pd.DataFrame([{
            "CV": r["nom"],
            "✅ Conformes": r["conformes"],
            "⚠️ À challenger": r["challengers"],
            "❌ Non conformes": r["non_conformes"],
            "🎯 Score confiance": round(r["score"] * 100)
        } for r in results_all])
        st.dataframe(df_compare, hide_index=True)

        csv_data = df_compare.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger le comparatif CSV",
            data=csv_data,
            file_name="comparatif_cv_gfsi.csv",
            mime="text/csv"
        )

        df_details = pd.DataFrame(details_export)
        st.download_button(
            label="📄 Télécharger les analyses détaillées",
            data=df_details.to_csv(index=False).encode('utf-8'),
            file_name="details_analyse_cv_gfsi.csv",
            mime="text/csv"
        )

        for r in results_all:
            st.markdown(f"## 📋 Détail pour {r['nom']}")
            for item in r["details"]:
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
            st.markdown(f"### 🗒️ Synthèse IA pour {r['nom']}")
            st.info(r["synthese"])

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
