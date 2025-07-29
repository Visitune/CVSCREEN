# Analyse de CV - GFSI (multi-CV avec comparaison et graphiques enrichis)

import streamlit as st
import PyPDF2
import json
import re
from datetime import datetime
from pathlib import Path
import groq
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

st.set_page_config(page_title="Analyse de CV GFSI", layout="wide")
st.title("📄 Analyse comparative de CV - Auditeurs GFSI")

# Configuration de la sidebar pour les paramètres
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
        st.error("Aucun référentiel trouvé dans le dossier 'referentiels'.")
        st.stop()

    ref_name = st.selectbox("📚 Référentiel GFSI :", list(referentials.keys()))
    selected_ref = referentials[ref_name]

    model = st.selectbox("🧠 Modèle IA :", [
        "llama3-8b-8192",
        "llama-3.3-70b-versatile", 
        "llama-3.1-8b-instant",
        "kmi-k2-70b",
        "qwen3-72b"
    ])

def create_comparison_charts(results_all):
    """Crée des graphiques de comparaison entre les CVs"""
    
    # Préparer les données
    df_results = pd.DataFrame(results_all)
    
    # 1. Graphique en barres empilées - Vue d'ensemble
    fig_stacked = go.Figure()
    
    cv_names = [r["nom"].replace('.pdf', '') for r in results_all]
    
    fig_stacked.add_trace(go.Bar(
        name='✅ Conformes',
        x=cv_names,
        y=[r["conformes"] for r in results_all],
        marker_color='#28a745',
        text=[r["conformes"] for r in results_all],
        textposition='auto',
    ))
    
    fig_stacked.add_trace(go.Bar(
        name='⚠️ À challenger',
        x=cv_names,
        y=[r["challengers"] for r in results_all],
        marker_color='#ffc107',
        text=[r["challengers"] for r in results_all],
        textposition='auto',
    ))
    
    fig_stacked.add_trace(go.Bar(
        name='❌ Non conformes',
        x=cv_names,
        y=[r["non_conformes"] for r in results_all],
        marker_color='#dc3545',
        text=[r["non_conformes"] for r in results_all],
        textposition='auto',
    ))
    
    fig_stacked.update_layout(
        title="📊 Comparaison des statuts de conformité par CV",
        xaxis_title="Candidats",
        yaxis_title="Nombre d'exigences",
        barmode='stack',
        height=500,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # 2. Graphique en radar - Scores de confiance
    fig_radar = go.Figure()
    
    for i, result in enumerate(results_all):
        categories = []
        scores = []
        
        # Grouper par catégories d'exigences (première partie avant le premier espace)
        category_scores = {}
        for detail in result["details"]:
            category = detail["exigence"].split(" ")[0] if detail["exigence"] else "Autre"
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(detail.get("confiance", 0))
        
        # Calculer les moyennes par catégorie
        for cat, scores_list in category_scores.items():
            categories.append(cat)
            scores.append(np.mean(scores_list) * 100)
        
        # Fermer le polygone
        categories.append(categories[0])
        scores.append(scores[0])
        
        fig_radar.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            name=result["nom"].replace('.pdf', ''),
            line=dict(width=2),
            opacity=0.7
        ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        title="🎯 Scores de confiance par catégorie d'exigences",
        height=500,
        showlegend=True
    )
    
    # 3. Graphique en secteurs pour chaque CV
    fig_pie_subplots = make_subplots(
        rows=1, cols=len(results_all),
        specs=[[{'type': 'domain'}] * len(results_all)],
        subplot_titles=[r["nom"].replace('.pdf', '') for r in results_all]
    )
    
    colors = ['#28a745', '#ffc107', '#dc3545']
    labels = ['Conformes', 'À challenger', 'Non conformes']
    
    for i, result in enumerate(results_all):
        values = [result["conformes"], result["challengers"], result["non_conformes"]]
        
        fig_pie_subplots.add_trace(
            go.Pie(
                values=values,
                labels=labels,
                marker_colors=colors,
                textinfo='label+percent',
                showlegend=(i == 0)  # Afficher la légende seulement pour le premier graphique
            ),
            row=1, col=i+1
        )
    
    fig_pie_subplots.update_layout(
        title="🥧 Répartition détaillée par candidat",
        height=400
    )
    
    # 4. Graphique de performance globale
    fig_performance = go.Figure()
    
    # Calculer un score de performance global
    performance_scores = []
    for result in results_all:
        total = result["conformes"] + result["challengers"] + result["non_conformes"]
        if total > 0:
            score = (result["conformes"] * 100 + result["challengers"] * 50) / total
        else:
            score = 0
        performance_scores.append(score)
    
    # Créer le graphique en barres avec gradient de couleur
    colors_gradient = ['#dc3545' if score < 40 else '#ffc107' if score < 70 else '#28a745' 
                      for score in performance_scores]
    
    fig_performance.add_trace(go.Bar(
        x=cv_names,
        y=performance_scores,
        marker_color=colors_gradient,
        text=[f"{score:.1f}%" for score in performance_scores],
        textposition='auto',
        name='Score de performance'
    ))
    
    # Ajouter des lignes de seuil
    fig_performance.add_hline(y=70, line_dash="dash", line_color="orange", 
                             annotation_text="Seuil recommandé (70%)")
    fig_performance.add_hline(y=40, line_dash="dash", line_color="red", 
                             annotation_text="Seuil minimum (40%)")
    
    fig_performance.update_layout(
        title="📈 Score de performance global par candidat",
        xaxis_title="Candidats",
        yaxis_title="Score de performance (%)",
        yaxis=dict(range=[0, 100]),
        height=400
    )
    
    return fig_stacked, fig_radar, fig_pie_subplots, fig_performance

def create_detailed_analysis_chart(result):
    """Crée un graphique détaillé pour un CV spécifique"""
    
    details = result["details"]
    
    # Graphique en barres horizontales pour les scores de confiance
    exigences = [d["exigence"][:50] + "..." if len(d["exigence"]) > 50 else d["exigence"] 
                for d in details]
    confidences = [d.get("confiance", 0) * 100 for d in details]
    statuts = [d.get("statut", "") for d in details]
    
    # Couleurs selon le statut
    colors = []
    for statut in statuts:
        if "CONFORME" in statut.upper():
            colors.append('#28a745')
        elif "CHALLENGER" in statut.upper():
            colors.append('#ffc107')
        else:
            colors.append('#dc3545')
    
    fig_detail = go.Figure()
    
    fig_detail.add_trace(go.Bar(
        y=exigences,
        x=confidences,
        orientation='h',
        marker_color=colors,
        text=[f"{conf:.0f}%" for conf in confidences],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Confiance: %{x:.1f}%<br>Statut: %{customdata}<extra></extra>',
        customdata=statuts
    ))
    
    fig_detail.update_layout(
        title=f"📊 Analyse détaillée - {result['nom']}",
        xaxis_title="Score de confiance (%)",
        yaxis_title="Exigences",
        height=max(400, len(details) * 25),  # Hauteur dynamique
        margin=dict(l=300)  # Marge gauche pour les textes longs
    )
    
    return fig_detail

def generate_executive_summary(results_all):
    """Génère un résumé exécutif avec recommandations"""
    
    total_cvs = len(results_all)
    
    # Calculer les statistiques globales
    avg_conformes = np.mean([r["conformes"] for r in results_all])
    avg_challengers = np.mean([r["challengers"] for r in results_all])
    avg_non_conformes = np.mean([r["non_conformes"] for r in results_all])
    avg_confiance = np.mean([r["score"] for r in results_all])
    
    # Identifier le meilleur et le moins bon candidat
    best_candidate = max(results_all, key=lambda x: x["conformes"] - x["non_conformes"])
    worst_candidate = min(results_all, key=lambda x: x["conformes"] - x["non_conformes"])
    
    # Générer le résumé
    summary = f"""
    ## 📋 Résumé Exécutif
    
    **Analyse de {total_cvs} candidat(s) auditeur GFSI**
    
    ### 🎯 Performance Globale
    - **Moyenne conformité :** {avg_conformes:.1f} exigences conformes par CV
    - **Moyenne à challenger :** {avg_challengers:.1f} points à éclaircir par CV  
    - **Moyenne non-conformité :** {avg_non_conformes:.1f} lacunes par CV
    - **Confiance moyenne :** {avg_confiance*100:.1f}%
    
    ### 🏆 Candidat le plus qualifié
    **{best_candidate['nom']}** - {best_candidate['conformes']} conformités, {best_candidate['non_conformes']} non-conformités
    
    ### ⚠️ Candidat nécessitant le plus d'attention
    **{worst_candidate['nom']}** - {worst_candidate['conformes']} conformités, {worst_candidate['non_conformes']} non-conformités
    
    ### 💡 Recommandations
    """
    
    # Recommandations personnalisées
    if avg_confiance > 0.8:
        summary += "- ✅ **Excellent niveau général** des candidats analysés\n"
    elif avg_confiance > 0.6:
        summary += "- 🔍 **Niveau correct** mais validation complémentaire recommandée\n"
    else:
        summary += "- ⚠️ **Attention requise** - Plusieurs lacunes identifiées\n"
    
    if avg_non_conformes > avg_conformes:
        summary += "- 🚨 **Action prioritaire** - Plus de non-conformités que de conformités\n"
    
    if total_cvs > 1:
        summary += f"- 📊 **Comparaison disponible** entre {total_cvs} profils\n"
    
    return summary

# Interface principale
uploaded_files = st.file_uploader(
    "📄 Chargez un ou plusieurs CV (PDF uniquement)", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files and st.button("🔍 Lancer l'analyse IA", type="primary"):
    results_all = []
    details_export = []
    
    # Barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with st.spinner("Analyse des CV en cours..."):
        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Analyse en cours: {uploaded_file.name}")
            progress_bar.progress((idx + 1) / len(uploaded_files))
            
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
                json_start = result.find('{')
                json_str = result[json_start:]
                json_str = re.sub(r'```json|```', '', json_str).strip()
                result_data = json.loads(json_str)
                
                analysis = result_data.get("analysis", [])
                
                # Enrichir les données pour l'export
                for a in analysis:
                    a["cv"] = uploaded_file.name
                    details_export.append(a)
                
                # Calculer les métriques
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
    
    progress_bar.empty()
    status_text.empty()

    if results_all:
        # Affichage du résumé exécutif
        st.markdown(generate_executive_summary(results_all))
        
        # Création des graphiques
        fig_stacked, fig_radar, fig_pie_subplots, fig_performance = create_comparison_charts(results_all)
        
        # Affichage des graphiques de comparaison
        st.markdown("## 📊 Visualisations Comparatives")
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_stacked, use_container_width=True)
        with col2:
            st.plotly_chart(fig_performance, use_container_width=True)
        
        st.plotly_chart(fig_radar, use_container_width=True)
        st.plotly_chart(fig_pie_subplots, use_container_width=True)
        
        # Tableau de comparaison amélioré
        st.markdown("## 📋 Tableau de Comparaison")
        df_compare = pd.DataFrame([{
            "👤 CV": r["nom"].replace('.pdf', ''),
            "✅ Conformes": r["conformes"],
            "⚠️ À challenger": r["challengers"], 
            "❌ Non conformes": r["non_conformes"],
            "🎯 Confiance (%)": f"{round(r['score'] * 100)}%",
            "📊 Performance": f"{((r['conformes'] * 100 + r['challengers'] * 50) / (r['conformes'] + r['challengers'] + r['non_conformes']) if (r['conformes'] + r['challengers'] + r['non_conformes']) > 0 else 0):.1f}%"
        } for r in results_all])
        
        st.dataframe(df_compare, hide_index=True, use_container_width=True)
        
        # Boutons de téléchargement
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv_data = df_compare.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Comparatif CSV",
                data=csv_data,
                file_name=f"comparatif_cv_gfsi_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            df_details = pd.DataFrame(details_export)
            st.download_button(
                label="📄 Analyses détaillées",
                data=df_details.to_csv(index=False).encode('utf-8'),
                file_name=f"details_analyse_cv_gfsi_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col3:
            # Export JSON complet
            export_data = {
                "metadata": {
                    "date_analyse": datetime.now().isoformat(),
                    "referentiel": ref_name,
                    "modele_ia": model,
                    "nombre_cvs": len(results_all)
                },
                "resultats": results_all
            }
            st.download_button(
                label="💾 Export JSON complet",
                data=json.dumps(export_data, indent=2, ensure_ascii=False).encode('utf-8'),
                file_name=f"analyse_complete_gfsi_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        # Analyses détaillées par CV
        st.markdown("## 🔍 Analyses Détaillées par CV")
        
        # Onglets pour chaque CV
        if len(results_all) > 1:
            tabs = st.tabs([r["nom"].replace('.pdf', '') for r in results_all])
            
            for idx, (tab, result) in enumerate(zip(tabs, results_all)):
                with tab:
                    # Graphique détaillé pour ce CV
                    fig_detail = create_detailed_analysis_chart(result)
                    st.plotly_chart(fig_detail, use_container_width=True)
                    
                    # Affichage des détails par exigence
                    st.markdown("### 📋 Détail par exigence")
                    for item in result["details"]:
                        statut = item.get("statut", "")
                        couleur = {
                            "CONFORME": "#d4edda",
                            "À CHALLENGER": "#fff3cd", 
                            "NON CONFORME": "#f8d7da"
                        }.get(statut.upper(), "#e2e3e5")
                        
                        st.markdown(
                            f"""
                            <div style='background-color:{couleur}; padding:15px; border-radius:8px; margin-bottom:10px; border-left: 4px solid {"#28a745" if "CONFORME" in statut.upper() else "#ffc107" if "CHALLENGER" in statut.upper() else "#dc3545"};'>
                            <strong>📝 Exigence :</strong> {item['exigence']}<br>
                            <strong>🏷️ Statut :</strong> <span style='font-weight:bold;'>{statut}</span><br>
                            <strong>🎯 Confiance :</strong> {item['confiance']*100:.0f}%<br>
                            <strong>💭 Justification :</strong> {item['justification']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    # Synthèse IA
                    st.markdown("### 🤖 Synthèse IA")
                    st.info(result["synthese"])
        else:
            # Un seul CV - affichage direct
            result = results_all[0]
            fig_detail = create_detailed_analysis_chart(result)
            st.plotly_chart(fig_detail, use_container_width=True)
            
            st.markdown("### 📋 Détail par exigence")
            for item in result["details"]:
                statut = item.get("statut", "")
                couleur = {
                    "CONFORME": "#d4edda",
                    "À CHALLENGER": "#fff3cd",
                    "NON CONFORME": "#f8d7da"
                }.get(statut.upper(), "#e2e3e5")
                
                st.markdown(
                    f"""
                    <div style='background-color:{couleur}; padding:15px; border-radius:8px; margin-bottom:10px; border-left: 4px solid {"#28a745" if "CONFORME" in statut.upper() else "#ffc107" if "CHALLENGER" in statut.upper() else "#dc3545"};'>
                    <strong>📝 Exigence :</strong> {item['exigence']}<br>
                    <strong>🏷️ Statut :</strong> <span style='font-weight:bold;'>{statut}</span><br>
                    <strong>🎯 Confiance :</strong> {item['confiance']*100:.0f}%<br>
                    <strong>💭 Justification :</strong> {item['justification']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            st.markdown("### 🤖 Synthèse IA")
            st.info(result["synthese"])

# Module d'administration (inchangé)
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
