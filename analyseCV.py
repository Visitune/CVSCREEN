import streamlit as st
import os
import groq
import PyPDF2
import pandas as pd
from pathlib import Path
import json

st.set_page_config(page_title="Analyse CV Auditeurs", layout="wide")

st.title("📄 Analyse automatique de CV – Auditeurs")

# --- Étape 1 : Clé API utilisateur ---
api_key = st.text_input("🔑 Veuillez saisir votre clé API Groq :", type="password")

if not api_key:
    st.warning("Merci d'entrer une clé API valide pour continuer.")
    st.stop()

client = groq.Client(api_key=api_key)

# --- Étape 2 : Chargement des référentiels ---
def load_referentials():
    referentials = {}
    folder = Path("referentiels")
    if folder.exists():
        for file in folder.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                referentials[file.stem] = json.load(f)
    return referentials

referentials = load_referentials()
selected_schema = st.selectbox("📚 Choisissez un référentiel à utiliser :", list(referentials.keys()))

# --- Étape 3 : Upload du CV ---
uploaded_file = st.file_uploader("📤 Uploadez un CV (PDF uniquement)", type=["pdf"])

if uploaded_file and selected_schema:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    prompt = f"""
Tu es un assistant qui vérifie si un CV est conforme aux exigences du référentiel suivant :
{json.dumps(referentials[selected_schema], indent=2)}

Voici le contenu du CV à analyser :
{text}

Retourne un JSON indiquant pour chaque exigence si elle est remplie ou non, avec un score de confiance, et une synthèse globale du profil.
"""

    with st.spinner("Analyse en cours avec Groq..."):
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content
            st.subheader("✅ Résultat de l'analyse")
            st.code(result, language="json")
        except Exception as e:
            st.error(f"Erreur pendant l'appel à l'API : {e}")
