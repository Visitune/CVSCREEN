import streamlit as st
import PyPDF2
import json
from datetime import datetime
from pathlib import Path
import groq
import pandas as pd
import plotly.graph_objects as go
import hashlib
import io
import os
import re

# ============== Sécurité / Admin ==============
def is_admin_authenticated(password: str) -> bool:
    expected = st.secrets.get("ADMIN_PASSWORD", os.environ.get("ADMIN_PASSWORD", ""))
    return bool(expected) and password == expected

def save_referential_to_json(referential_data: dict, filename: str) -> bool:
    try:
        ref_dir = Path("referentiels")
        ref_dir.mkdir(exist_ok=True)
        safe = filename.strip().replace(" ", "_").replace("/", "_")
        if not safe.endswith(".json"):
            safe += ".json"
        with open(ref_dir / safe, "w", encoding="utf-8") as f:
            json.dump(referential_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")
        st.info("ℹ️ Sur certaines plateformes (Spaces), les fichiers peuvent ne pas persister après reboot.")
        return False

def validate_referential_structure(data: dict) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Le référentiel doit être un objet JSON"
    if "exigences" not in data and "categories" not in data:
        return False, "Clé manquante: 'exigences' ou 'categories'"
    if "exigences" in data and not isinstance(data["exigences"], dict):
        return False, "'exigences' doit être un objet"
    if "categories" in data and not isinstance(data["categories"], dict):
        return False, "'categories' doit être un objet"
    return True, "OK"

# ============== Config Streamlit ==============
st.set_page_config(page_title="Analyse de CV GFSI", layout="wide")
st.title("📄 Analyse comparative de CV - Auditeurs GFSI")

# ============== Utils ==============
def jauge(titre, valeur):
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

def extract_json_strict(text: str):
    s = (text or "").strip()
    a, b = s.find("{"), s.rfind("}")
    if a == -1 or b == -1 or b <= a:
        return None
    try:
        return json.loads(s[a:b+1])
    except Exception:
        pass
    stack, start = 0, None
    for i, ch in enumerate(s):
        if ch == "{":
            if stack == 0:
                start = i
            stack += 1
        elif ch == "}":
            stack -= 1
            if stack == 0 and start is not None:
                try:
                    return json.loads(s[start:i+1])
                except Exception:
                    continue
    return None

def validate_analysis(obj):
    if not isinstance(obj, dict):
        return False, "Objet racine non valide"
    if "analysis" not in obj or not isinstance(obj["analysis"], list):
        return False, "Champ 'analysis' manquant"
    ok_items = []
    for it in obj["analysis"]:
        if not isinstance(it, dict):
            continue
        need = ["exigence_id", "exigence_titre", "statut", "justification", "confiance", "ponderation", "niveau_requis"]
        if not all(k in it for k in need):
            continue
        it["statut"] = str(it["statut"]).upper().replace("À", "A")
        if "category_id" not in it:
            it["category_id"] = ""
        ok_items.append(it)
    obj["analysis"] = ok_items
    if "score_global" not in obj:
        obj["score_global"] = 0
    if "synthese" not in obj:
        obj["synthese"] = ""
    return True, obj

@st.cache_data
def pdf_to_text(file_bytes: bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    return " ".join([(page.extract_text() or "") for page in reader.pages])

def file_digest(uploaded_file):
    uploaded_file.seek(0)
    data = uploaded_file.read()
    uploaded_file.seek(0)
    return hashlib.sha256(data).hexdigest(), data

# ============== Sidebar ==============
with st.sidebar:
    st.header("🔧 Configuration")
    api_key = st.text_input("🔑 Clé API Groq :", type="password")

    st.divider()
    st.subheader("🔒 Administration")
    admin_pass = st.text_input("Mot de passe admin :", type="password")
    admin_ok = is_admin_authenticated(admin_pass)
    if admin_ok:
        st.success("Accès admin validé ✅")
    else:
        st.caption("Entrez le mot de passe admin pour accéder aux fonctions avancées.")

    if not api_key:
        st.warning("Veuillez saisir une clé API valide.")
        st.stop()

    client = groq.Client(api_key=api_key)

    @st.cache_data
    def load_referentials():
        out = {}
        ref_dir = Path("referentiels")
        if ref_dir.exists():
            for file in ref_dir.glob("*.json"):
                try:
                    with open(file, encoding="utf-8") as f:
                        data = json.load(f)
                    if "exigences" in data or "categories" in data:
                        out[file.stem] = data
                except Exception as e:
                    st.error(f"❌ Erreur lecture {file.name}: {e}")
        return out

    referentials = load_referentials()
    if not referentials:
        st.error("Aucun référentiel valide trouvé.")
        st.stop()

    ref_name = st.selectbox("📚 Référentiel GFSI :", list(referentials.keys()))
    selected_ref = referentials[ref_name]

    if "metadata" in selected_ref:
        md = selected_ref["metadata"]
        st.info(f"**{md.get('name', 'Sans nom')}**\n\n{md.get('description', '')}")
        st.caption(f"Version: {md.get('version', 'N/A')} | Date: {md.get('date_creation', md.get('last_updated', 'N/A'))}")

    model = st.selectbox("🧠 Modèle IA :", ["llama3-8b-8192", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"])

# ============== Fonctions IA Admin ==============
def create_referential_with_ai(exigences_text: str, groq_client) -> dict | None:
    prompt = f"""
Structure ces exigences en JSON hiérarchisé avec catégories, sous-catégories, pondérations (somme=1.0), références et seuils:
TEXTES:
{exigences_text}

FORMAT:
{{
  "metadata": {{
    "name": "Nom à déterminer",
    "version": "1.0",
    "description": "Description du référentiel",
    "last_updated": "{datetime.now().date()}",
    "source": "Source des exigences"
  }},
  "categories": {{
    "Category_Name": {{
      "weight": 0.3,
      "description": "Description",
      "subcategories": {{
        "Subcategory_Name": {{
          "weight": 0.5,
          "requirements": [
            {{
              "id": "REF-001",
              "text": "Texte de l'exigence",
              "critical": true,
              "minimum_acceptable": "Critère minimum acceptable",
              "references": ["Section du standard"]
            }}
          ]
        }}
      }}
    }}
  }}
}}
Répond uniquement avec du JSON strictement valide.
"""
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Tu es un expert en structuration de référentiels de conformité."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=4000,
            temperature=0.1
        )
        content = response.choices[0].message.content or ""
        m = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        raw_json = m.group(1) if m else content
        return extract_json_strict(raw_json)
    except Exception as e:
        st.error(f"Erreur IA: {e}")
        return None

# ============== Prompt builder ==============
def build_prompt(selected_ref, cv_text):
    if "exigences" in selected_ref and isinstance(selected_ref["exigences"], dict) and selected_ref["exigences"]:
        lines = []
        for req_id, req in selected_ref["exigences"].items():
            lines.append(
                f"EXIGENCE {req_id}: {req.get('title','')}\n"
                f"Description: {req.get('description','')}\n"
                f"Niveau: {req.get('niveau_requis','')}\n"
                f"Pondération: {req.get('ponderation',1.0)}\n"
                "Critères:\n" + "\n".join(["• "+c for c in req.get("criteres", [])])
            )
            lines.append("Exemples conformes:\n" + "\n".join(["• "+e for e in req.get("exemples_conformes", [])]))
            lines.append("Exemples non conformes:\n" + "\n".join(["• "+e for e in req.get("exemples_non_conformes", [])]) + "\n---")
        exigences_detail = "\n".join(lines)
    else:
        lines = []
        for cat, cat_data in selected_ref.get("categories", {}).items():
            lines.append(f"== CATEGORIE {cat} (poids {cat_data.get('weight',0)}) ==")
            lines.append(cat_data.get("description",""))
            for sub, sub_data in cat_data.get("subcategories", {}).items():
                lines.append(f"-- Sous-catégorie {sub} (poids {sub_data.get('weight',0)}) --")
                for req in sub_data.get("requirements", []):
                    lines.append(
                        f"EXIGENCE {req.get('id','N/A')}\n"
                        f"Texte: {req.get('text','')}\n"
                        f"Minimum acceptable: {req.get('minimum_acceptable','')}\n"
                        f"Références: {', '.join(req.get('references', []))}\n---"
                    )
        exigences_detail = "\n".join(lines)

    schema = {
        "analysis": [{
            "exigence_id": "ID exact",
            "exigence_titre": "Titre",
            "category_id": "Catégorie/Sous-catégorie",
            "statut": "CONFORME | A CHALLENGER | NON CONFORME",
            "justification": "Preuves et raisonnement",
            "elements_cv": "Citations du CV",
            "confiance": 0.0,
            "niveau_requis": "obligatoire|recommande|souhaitable",
            "ponderation": 1.0
        }],
        "score_global": 0.0,
        "synthese": "Résumé et recommandations"
    }
    return f"""
Tu es un expert conformité GFSI.
Analyse le CV ci-dessous selon les exigences listées.
Répond uniquement avec un JSON strictement valide qui respecte ce schéma:
{json.dumps(schema, ensure_ascii=False, indent=2)}

RÉFÉRENTIEL:
{exigences_detail}

CV:
{cv_text}
"""

# ============== Main: Upload & Analyse ==============
uploaded_files = st.file_uploader("📄 Chargez un ou plusieurs CV (PDF uniquement)", type=["pdf"], accept_multiple_files=True)

if uploaded_files and st.button("🔍 Lancer l'analyse IA"):
    results_all, details_export = [], []
    with st.spinner("Analyse des CV en cours..."):
        for up in uploaded_files:
            try:
                digest, data = file_digest(up)
                cv_text = pdf_to_text(data)
                prompt = build_prompt(selected_ref, cv_text)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=4000
                )
                raw = response.choices[0].message.content or ""
                parsed = extract_json_strict(raw)
                if not parsed:
                    st.error(f"JSON invalide pour {up.name}")
                    continue
                ok, res = validate_analysis(parsed)
                if not ok:
                    st.error(f"{res} pour {up.name}")
                    continue
                analysis = res["analysis"]
                for a in analysis:
                    a["cv"] = up.name
                    details_export.append(a)
                score_pondere, poids_total = 0.0, 0.0
                conformes = challengers = non_conformes = 0
                for item in analysis:
                    statut = item.get("statut", "")
                    ponderation = float(item.get("ponderation", 1.0) or 1.0)
                    confiance = float(item.get("confiance", 0) or 0)
                    if statut == "CONFORME":
                        conformes += 1
                        score_pondere += confiance * ponderation
                    elif statut == "A CHALLENGER":
                        challengers += 1
                        score_pondere += (confiance * 0.5) * ponderation
                    else:
                        non_conformes += 1
                    poids_total += ponderation
                score_final = (score_pondere / poids_total) if poids_total > 0 else 0.0
                results_all.append({
                    "nom": up.name,
                    "conformes": conformes,
                    "challengers": challengers,
                    "non_conformes": non_conformes,
                    "score": round(score_final, 2),
                    "score_global": res.get("score_global", score_final),
                    "details": analysis,
                    "synthese": res.get("synthese", "")
                })
            except Exception as e:
                st.error(f"❌ Erreur pour {up.name} : {e}")

    if results_all:
        st.subheader("📊 Comparaison des candidats")
        comparison_df = pd.DataFrame([{
            "Candidat": r["nom"],
            "Score Global": f"{r['score']:.0%}",
            "✅ Conformes": r["conformes"],
            "⚠️ À challenger": r["challengers"],
            "❌ Non conformes": r["non_conformes"]
        } for r in results_all])
        st.dataframe(comparison_df, use_container_width=True)

        for result in results_all:
            st.subheader(f"📄 Analyse détaillée : {result['nom']}")
            col1, col2 = st.columns([1, 2])
            with col1:
                jauge("Score Global", result["score"])
            with col2:
                st.markdown("### 🧠 Synthèse IA")
                st.info(result["synthese"])
            df = pd.DataFrame(result["details"])
            for _, row in df.iterrows():
                status_emoji = {"CONFORME": "✅", "A CHALLENGER": "⚠️", "NON CONFORME": "❌"}
                emoji = status_emoji.get(row["statut"], "❓")
                st.write(f"{emoji} **{row['exigence_titre']}**")
                st.write(f"*Justification:* {row['justification']}")
                if row.get('elements_cv'):
                    st.write(f"*Éléments du CV:* {row['elements_cv']}")
                st.write(f"*Confiance:* {float(row['confiance']):.0%}")
                st.divider()

        export_df = pd.DataFrame(details_export)
        csv = export_df.to_csv(index=False, encoding="utf-8")
        st.download_button(
            label="💾 Télécharger CSV",
            data=csv,
            file_name=f"analyse_cv_gfsi_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

# ============== Admin: CRUD Référentiels ==============
st.divider()
st.header("🛠️ Administration des référentiels")

if not admin_ok:
    st.info("🔐 Saisissez le mot de passe admin dans la sidebar pour gérer les référentiels.")
else:
    tab_creer, tab_import, tab_editer, tab_dupliquer = st.tabs(
        ["✨ Créer via IA", "📥 Importer JSON", "✏️ Éditer existant", "📄 Dupliquer"]
    )

    with tab_creer:
        st.subheader("Créer un référentiel à partir d'un texte brut")
        exigences_text = st.text_area("Collez ici les exigences (texte libre)...", height=220, placeholder="Ex: The auditor shall ...")
        colA, colB = st.columns(2)
        with colA:
            ref_filename = st.text_input("Nom de fichier (sans .json)", value="nouveau_referentiel")
        with colB:
            ref_preview = st.checkbox("Prévisualiser seulement", value=True)
        if st.button("🧠 Générer avec l'IA"):
            with st.spinner("Génération du référentiel via IA..."):
                gen = create_referential_with_ai(exigences_text, client)
            if not gen:
                st.error("Impossible de générer un JSON valide.")
            else:
                ok, msg = validate_referential_structure(gen)
                if not ok:
                    st.error(f"Structure invalide: {msg}")
                    st.json(gen)
                else:
                    st.success("Référentiel généré ✅")
                    st.json(gen)
                    if not ref_preview:
                        if save_referential_to_json(gen, ref_filename):
                            st.success(f"Enregistré sous referentiels/{ref_filename}.json")
                            st.caption("Recharge des référentiels...")
                            load_referentials.clear()
                            st.rerun()

    with tab_import:
        st.subheader("Importer un fichier JSON")
        uploaded_json = st.file_uploader("Sélectionnez un fichier .json", type=["json"], accept_multiple_files=False, key="imp_json")
        if uploaded_json is not None:
            try:
                data = json.loads(uploaded_json.read().decode("utf-8"))
                ok, msg = validate_referential_structure(data)
                if not ok:
                    st.error(f"Structure invalide: {msg}")
                    st.json(data)
                else:
                    st.success("JSON valide ✅")
                    st.json(data)
                    filename = st.text_input("Nom de fichier (sans .json)", value=Path(uploaded_json.name).stem)
                    if st.button("💾 Sauvegarder l'import"):
                        if save_referential_to_json(data, filename):
                            st.success(f"Enregistré sous referentiels/{filename}.json")
                            load_referentials.clear()
                            st.rerun()
            except Exception as e:
                st.error(f"Erreur de parsing JSON: {e}")

    with tab_editer:
        st.subheader("Éditer un référentiel existant")
        edit_key = st.selectbox("Référentiel à éditer", list(referentials.keys()))
        current = referentials[edit_key]
        raw = st.text_area("Éditez le JSON ci-dessous :", value=json.dumps(current, ensure_ascii=False, indent=2), height=400)
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Nom de fichier (sans .json)", value=edit_key)
        with col2:
            keep_backup = st.checkbox("Créer une sauvegarde .bak", value=True)
        if st.button("💾 Sauvegarder les modifications"):
            try:
                data = json.loads(raw)
                ok, msg = validate_referential_structure(data)
                if not ok:
                    st.error(f"Structure invalide: {msg}")
                else:
                    if keep_backup:
                        save_referential_to_json(current, f"{edit_key}.bak_{datetime.now().strftime('%Y%m%d_%H%M')}")
                    if save_referential_to_json(data, new_name):
                        st.success(f"Enregistré sous referentiels/{new_name}.json")
                        load_referentials.clear()
                        st.rerun()
            except Exception as e:
                st.error(f"JSON invalide: {e}")

    with tab_dupliquer:
        st.subheader("Dupliquer un référentiel")
        src = st.selectbox("Source", list(referentials.keys()), key="dup_src")
        target = st.text_input("Nom de fichier cible (sans .json)", value=f"{src}_copy")
        if st.button("📄 Dupliquer"):
            if save_referential_to_json(referentials[src], target):
                st.success(f"Copie enregistrée: referentiels/{target}.json")
                load_referentials.clear()
                st.rerun()
