# Analyse de CV GFSI avec jauges et JSON tolérant
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

# Sidebar config
with st.sidebar:
    st.header("🔧 Configuration")
    api_key = st.text_input("🔑 Clé API Groq :", type="password")
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
                with open(file, encoding="utf-8") as f:
                    referentials[file.stem] = json.load(f)
        return referentials

    referentials = load_referentials()
    if not referentials:
        st.error("Aucun référentiel trouvé.")
        st.stop()

    ref_name = st.selectbox("📚 Référentiel GFSI :", list(referentials.keys()))
    selected_ref = referentials[ref_name]

    model = st.selectbox("🧠 Modèle IA :", [
        "meta-llama/llama-4-maverick-17b-128e-instruct", "llama-3.3-70b-versatile", "openai/gpt-oss-120b", "moonshotai/kimi-k2-instruct-0905", "qwen3-72b"
    ])

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

                prompt = f"""
Tu es un expert en conformité GFSI.
Analyse le CV ci-dessous en comparant CHAQUE EXIGENCE du référentiel une par une.
Pour chaque exigence :
- indique si elle est ✅ CONFORME, ⚠️ À CHALLENGER, ou ❌ NON CONFORME
- fournis une justification brève basée sur les données du CV
- indique un score de confiance (0 à 1)

RÉFÉRENTIEL GFSI :
{json.dumps(selected_ref, indent=2)}

CV DU CANDIDAT :
{cv_text}

Répond UNIQUEMENT avec un objet JSON strictement valide :
{{
  "analysis": [
    {{
      "exigence": "description de l'exigence",
      "statut": "CONFORME / À CHALLENGER / NON CONFORME",
      "justification": "justification basée sur le CV",
      "confiance": 0.85
    }}
  ],
  "synthese": "résumé clair et actionnable pour le candidat"
}}
"""

                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
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

                conformes = sum(1 for i in analysis if i.get("statut", "").upper() == "CONFORME")
                challengers = sum(1 for i in analysis if "CHALLENGER" in i.get("statut", "").upper())
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
                st.error(f"❌ Erreur pour {uploaded_file.name} : {e}")

    # Affichage des résultats
    for result in results_all:
        st.subheader(f"📄 Résultats pour : {result['nom']}")
        df = pd.DataFrame(result["details"])

        st.markdown("### 🎯 Taux de conformité par exigence")
        grouped = df.groupby("exigence")
        for exigence, group in grouped:
            total = len(group)
            conformes = group["statut"].str.upper().eq("CONFORME").sum()
            taux_conformite = conformes / total if total > 0 else 0
            afficher_jauge(exigence, taux_conformite)

        st.markdown("### 🧠 Synthèse IA")
        st.info(result["synthese"])
