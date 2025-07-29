# Analyse de CV - GFSI (version complète avec présentation simplifiée)
# Nom du fichier : analyse_cv_gfsi.py

import streamlit as st
import PyPDF2
import json
from datetime import datetime
from pathlib import Path
import groq

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

    # Construction du prompt
    prompt = f"""
Tu es un expert GFSI. Analyse le CV ci-dessous selon ce référentiel :

{json.dumps(selected_ref, indent=2)}

Contenu du CV :
{cv_text}

Donne une réponse SIMPLIFIÉE, CLAIRE pour un non-spécialiste, en français. Organise par catégorie avec :
- ✅ Points forts (conformes),
- ⚠️ Points à challenger,
- ❌ Points non conformes
Ajoute des couleurs et un résumé final pour échanger avec le candidat.
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

                # Présentation simplifiée pour utilisateurs non experts
                st.markdown("## ✨ Résultat de l'analyse simplifiée")
                st.markdown(result, unsafe_allow_html=True)

                filename = f"analyse_{ref_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                st.download_button("💾 Télécharger le rapport simplifié", result, file_name=filename, mime="text/plain")

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
