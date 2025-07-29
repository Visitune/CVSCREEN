import streamlit as st
import PyPDF2
import pandas as pd
import os
import json
import groq
from pathlib import Path
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Analyse de CV Auditeurs", layout="wide")

# Titre de l'application
st.title("📄 Analyse automatisée de CV - Auditeurs de certification")

# Clé API Groq manuelle
api_key = st.text_input("🔑 Entrez votre clé API Groq :", type="password")
if not api_key:
    st.warning("Merci de renseigner votre clé API Groq pour continuer.")
    st.stop()

client = groq.Client(api_key=api_key)

# Chargement des référentiels depuis le dossier
def load_referentials():
    ref_dir = Path("referentiels")
    referentials = {}
    if ref_dir.exists():
        for ref_file in ref_dir.glob("*.json"):
            with open(ref_file, "r", encoding="utf-8") as f:
                referentials[ref_file.stem] = json.load(f)
    return referentials

referentials = load_referentials()
if not referentials:
    st.error("Aucun référentiel trouvé dans le dossier 'referentiels'.")
    st.stop()

ref_choice = st.selectbox("📚 Choisissez un référentiel à utiliser :", list(referentials.keys()))
selected_ref = referentials[ref_choice]

# Upload du CV
uploaded_file = st.file_uploader("📤 Uploadez un CV (PDF uniquement)", type=["pdf"])

if uploaded_file:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    raw_text = ""
    for page in pdf_reader.pages:
        raw_text += page.extract_text()

    # Construction du prompt pour l'IA
    prompt = f"""
Tu es un assistant de recrutement spécialisé dans les audits de certification.
Analyse le CV suivant à la lumière des exigences du référentiel suivant :

{json.dumps(selected_ref, indent=2)}

Voici le contenu du CV :
"""
{raw_text}
"""

Retourne un JSON structuré contenant :
1. Pour chaque exigence : met / non met, score de confiance, commentaire
2. Une synthèse globale du profil
3. Une suggestion de relance si certaines informations sont manquantes
"""

    with st.spinner("⏳ Analyse du CV en cours..."):
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            result_text = response.choices[0].message.content.strip()
            st.success("✅ Analyse terminée avec succès !")

            # Affichage
            st.subheader("🧾 Résultat JSON")
            st.code(result_text, language="json")

            # Option de téléchargement
            filename = f"rapport_{ref_choice}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            st.download_button("📥 Télécharger le rapport JSON", result_text, file_name=filename, mime="application/json")

        except Exception as e:
            st.error(f"❌ Erreur pendant l'appel à l'API : {e}")
