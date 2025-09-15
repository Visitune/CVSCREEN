import streamlit as st
import PyPDF2
import json
from datetime import datetime
from pathlib import Path
import groq
import pandas as pd
import plotly.graph_objects as go
import hashlib

st.set_page_config(page_title="Analyse de CV GFSI", layout="wide")
st.title("📄 Analyse comparative de CV - Auditeurs GFSI")

def jauge(titre, valeur):
    fig = go.Figure(go.Indicator(mode="gauge+number", value=valeur * 100, domain={'x': [0, 1], 'y': [0, 1]}, title={'text': titre}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "green" if valeur >= 0.75 else "orange" if valeur >= 0.5 else "red"}, 'steps': [{'range': [0, 50], 'color': "#f8d7da"}, {'range': [50, 75], 'color': "#fff3cd"}, {'range': [75, 100], 'color': "#d4edda"}]}))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

def extract_json_strict(text):
    s = text.strip()
    a = s.find("{")
    b = s.rfind("}")
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

def create_example_referential():
    return {
        "metadata": {"name": "GFSI - Auditeur Senior", "version": "1.0", "description": "Référentiel pour auditeurs seniors GFSI", "date_creation": "2024-01-01"},
        "categories": {
            "formation": {"name": "Formation et Certification", "weight": 0.3, "description": "Formations académiques et certifications professionnelles"},
            "experience": {"name": "Expérience Professionnelle", "weight": 0.4, "description": "Expérience pratique en audit et sécurité alimentaire"},
            "competences": {"name": "Compétences Techniques", "weight": 0.2, "description": "Maîtrise des standards et outils d'audit"},
            "langues": {"name": "Compétences Linguistiques", "weight": 0.1, "description": "Capacités de communication internationale"}
        },
        "exigences": {
            "FORM_001": {"id": "FORM_001", "category": "formation", "title": "Formation supérieure en sécurité alimentaire", "description": "Diplôme Bac+5 minimum en sciences alimentaires, microbiologie, ou équivalent", "criteres": ["Diplôme universitaire niveau Master (Bac+5) minimum", "Spécialisation en sécurité alimentaire, microbiologie, ou domaine connexe", "Formation continue en normes GFSI"], "exemples_conformes": ["Master en Sciences Alimentaires - Université de Lyon", "Ingénieur Agronome spécialité Sécurité Alimentaire - AgroParisTech", "PhD en Microbiologie Alimentaire + formations GFSI"], "exemples_non_conformes": ["BTS Agroalimentaire uniquement", "Licence en biologie sans spécialisation", "Formation courte en audit sans diplôme supérieur"], "niveau_requis": "obligatoire", "ponderation": 1.0},
            "EXP_001": {"id": "EXP_001", "category": "experience", "title": "Expérience minimum en audit GFSI", "description": "Au moins 5 ans d'expérience en audit de systèmes de management sécurité alimentaire", "criteres": ["Minimum 5 années d'expérience en audit", "Expérience dans au moins 2 standards GFSI différents", "Participation à minimum 50 audits documentés"], "exemples_conformes": ["7 ans d'expérience - Lead Auditor BRC et IFS", "Auditeur senior FSSC 22000 - 120 audits réalisés", "10 ans audit SQF + formations continues"], "exemples_non_conformes": ["3 ans d'expérience uniquement en qualité", "Expérience audit ISO 9001 sans sécurité alimentaire", "Formation théorique sans pratique terrain"], "niveau_requis": "obligatoire", "ponderation": 1.0},
            "COMP_001": {"id": "COMP_001", "category": "competences", "title": "Maîtrise des standards GFSI", "description": "Connaissance approfondie d'au moins 2 standards GFSI reconnus", "criteres": ["Certification dans au moins 2 standards GFSI", "Connaissance des évolutions réglementaires", "Capacité à interpréter les non-conformités"], "exemples_conformes": ["Certifié Lead Auditor BRC + IFS", "Expert FSSC 22000 + SQF Level 2", "Formateur agréé standards GFSI"], "exemples_non_conformes": ["Connaissance théorique uniquement", "Certification dans un seul standard", "Pas de mise à jour des certifications"], "niveau_requis": "recommande", "ponderation": 0.8},
            "LANG_001": {"id": "LANG_001", "category": "langues", "title": "Compétences linguistiques internationales", "description": "Maîtrise de l'anglais professionnel + une langue additionnelle", "criteres": ["Anglais professionnel niveau C1 minimum", "Capacité à rédiger des rapports d'audit en anglais", "Une langue européenne additionnelle appréciée"], "exemples_conformes": ["Anglais courant + Allemand intermédiaire", "Bilingue français/anglais + notions espagnol", "Certifications TOEIC 900+ ou équivalent"], "exemples_non_conformes": ["Anglais scolaire uniquement", "Pas de pratique professionnelle de l'anglais", "Monolingue français"], "niveau_requis": "souhaitable", "ponderation": 0.6}
        }
    }

with st.sidebar:
    st.header("🔧 Configuration")
    api_key = st.text_input("🔑 Clé API Groq :", type="password")
    if st.button("📝 Créer un référentiel d'exemple"):
        ref_dir = Path("referentiels")
        ref_dir.mkdir(exist_ok=True)
        with open(ref_dir / "exemple_auditeur_senior.json", "w", encoding="utf-8") as f:
            json.dump(create_example_referential(), f, indent=2, ensure_ascii=False)
        st.success("✅ Référentiel d'exemple créé dans /referentiels/")
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
                    else:
                        st.warning(f"⚠️ Structure invalide pour {file.name}")
                except Exception as e:
                    st.error(f"❌ Erreur lecture {file.name}: {e}")
        return out

    referentials = load_referentials()
    if not referentials:
        st.error("Aucun référentiel valide trouvé.")
        st.info("• Cliquez sur '📝 Créer un référentiel d'exemple' pour commencer")
        st.stop()

    ref_name = st.selectbox("📚 Référentiel GFSI :", list(referentials.keys()))
    selected_ref = referentials[ref_name]

    if "metadata" in selected_ref:
        md = selected_ref["metadata"]
        st.info(f"**{md.get('name', 'Sans nom')}**\n\n{md.get('description', '')}")
        st.caption(f"Version: {md.get('version', 'N/A')} | Date: {md.get('date_creation', md.get('last_updated', 'N/A'))}")

    model = st.selectbox("🧠 Modèle IA :", ["llama3-8b-8192", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"])

def build_prompt(selected_ref, cv_text):
    if "categories" in selected_ref and any(isinstance(v, dict) and "subcategories" in v for v in selected_ref["categories"].values()):
        lines = []
        for cat_name, cat_data in selected_ref["categories"].items():
            lines.append(f"\n=== CATEGORIE: {cat_name} (Poids: {cat_data.get('weight', 0)}) ===")
            lines.append(cat_data.get("description", ""))
            for sub_name, sub in cat_data.get("subcategories", {}).items():
                lines.append(f"\n-- Sous-catégorie: {sub_name} (Poids: {sub.get('weight', 0)}) --")
                for req in sub.get("requirements", []):
                    rid = req.get("id", "N/A")
                    txt = req.get("text", "")
                    minacc = req.get("minimum_acceptable", "")
                    refs = ", ".join(req.get("references", []))
                    exs = req.get("examples", [])
                    ex_block = "\n".join(["• " + e for e in exs]) if exs else ""
                    lines.append(f"EXIGENCE {rid}\nTexte: {txt}\nMinimum acceptable: {minacc}\nRéférences: {refs}\nExemples:\n{ex_block}\n---")
        exigences_detail = "\n".join(lines)
    else:
        lines = []
        for req_id, req in selected_ref.get("exigences", {}).items():
            lines.append(f"EXIGENCE {req_id}: {req.get('title','')}\nDescription: {req.get('description','')}\nNiveau: {req.get('niveau_requis','')}\nPondération: {req.get('ponderation',1.0)}\nCritères:\n" + "\n".join(["• "+c for c in req.get("criteres", [])]))
            lines.append("Exemples conformes:\n" + "\n".join(["• "+e for e in req.get("exemples_conformes", [])]))
            lines.append("Exemples non conformes:\n" + "\n".join(["• "+e for e in req.get("exemples_non_conformes", [])]) + "\n---")
        exigences_detail = "\n".join(lines)
    schema = {
        "analysis": [{
            "exigence_id": "ID requis exact",
            "exigence_titre": "Titre",
            "category_id": "ID catégorie ou sous-catégorie",
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
Analyse le CV par rapport aux exigences listées ci-dessous.
Méthode: détecte les éléments du CV, compare aux critères, statue, justifie, et note la confiance.
Répond UNIQUEMENT avec un JSON strictement valide correspondant EXACTEMENT au schéma suivant:
{json.dumps(schema, ensure_ascii=False, indent=2)}

RÉFÉRENTIEL:
{exigences_detail}

CV:
{cv_text}
"""

@st.cache_data
def pdf_to_text(file_bytes):
    reader = PyPDF2.PdfReader(file_bytes)
    return " ".join([page.extract_text() or "" for page in reader.pages])

def file_digest(uploaded_file):
    uploaded_file.seek(0)
    data = uploaded_file.read()
    uploaded_file.seek(0)
    return hashlib.sha256(data).hexdigest(), data

uploaded_files = st.file_uploader("📄 Chargez un ou plusieurs CV (PDF uniquement)", type=["pdf"], accept_multiple_files=True)

if uploaded_files and st.button("🔍 Lancer l'analyse IA"):
    results_all, details_export = [], []
    with st.spinner("Analyse des CV en cours..."):
        for up in uploaded_files:
            try:
                digest, data = file_digest(up)
                cv_text = pdf_to_text(data)
                prompt = build_prompt(selected_ref, cv_text)
                response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], temperature=0.1, max_tokens=4000)
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
                score_pondere = 0.0
                poids_total = 0.0
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
                results_all.append({"nom": up.name, "conformes": conformes, "challengers": challengers, "non_conformes": non_conformes, "score": round(score_final, 2), "score_global": res.get("score_global", score_final), "details": analysis, "synthese": res.get("synthese", "")})
            except Exception as e:
                st.error(f"❌ Erreur pour {up.name} : {e}")

    if results_all:
        st.subheader("📊 Comparaison des candidats")
        comparison_df = pd.DataFrame([{"Candidat": r["nom"], "Score Global": f"{r['score']:.0%}", "✅ Conformes": r["conformes"], "⚠️ À challenger": r["challengers"], "❌ Non conformes": r["non_conformes"]} for r in results_all])
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
            st.markdown("### 📋 Analyse par catégorie")
            if "category_id" in df.columns and df["category_id"].astype(str).str.len().gt(0).any():
                for cat in sorted(df["category_id"].fillna("").unique()):
                    if cat == "":
                        continue
                    subset = df[df["category_id"] == cat]
                    if subset.empty:
                        continue
                    with st.expander(f"{cat} ({len(subset)})"):
                        for _, row in subset.iterrows():
                            status_emoji = {"CONFORME": "✅", "A CHALLENGER": "⚠️", "NON CONFORME": "❌"}
                            emoji = status_emoji.get(row["statut"], "❓")
                            st.write(f"{emoji} **{row['exigence_titre']}**")
                            st.write(f"*Justification:* {row['justification']}")
                            if row.get('elements_cv'):
                                st.write(f"*Éléments du CV:* {row['elements_cv']}")
                            st.write(f"*Confiance:* {float(row['confiance']):.0%}")
                            st.divider()
            else:
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
        st.download_button(label="💾 Télécharger CSV", data=csv, file_name=f"analyse_cv_gfsi_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")

with st.expander("📚 Structure du référentiel JSON"):
    st.code("""
{
  "metadata": {"name": "Nom du référentiel","version": "1.0","description": "Description","date_creation": "2024-01-01"},
  "categories": {"formation": {"name": "Formation","weight": 0.3,"description": "Texte"}},
  "exigences": {
    "FORM_001": {
      "id": "FORM_001","category": "formation","title": "Titre",
      "description": "Détail","criteres": ["Critère 1"],"exemples_conformes": ["Exemple"],
      "exemples_non_conformes": ["Contre-exemple"],"niveau_requis": "obligatoire|recommande|souhaitable","ponderation": 1.0
    }
  }
}
""", language="json")
