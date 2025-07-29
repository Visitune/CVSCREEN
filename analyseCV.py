# Configuration avancée de la page - DOIT ÊTRE LA PREMIÈRE COMMANDE STREAMLIT
import streamlit as st
st.set_page_config(
    layout="wide", 
    page_title="Analyse de CV - GFSI (Version 25.12)", 
    page_icon="📄",
    initial_sidebar_state="expanded"
)

from PyPDF2 import PdfReader
import pandas as pd
from groq import Groq
from referentials import REFERENTIALS, load_referentials_from_json, create_referential_with_ai, save_referential_to_json, is_admin_authenticated, TEMPLATE_NOUVEAU_REFERENTIEL
import json
import re
import os

# Dictionnaire de traduction
TRANSLATIONS = {
    "fr": {
        # Textes principaux
        "app_title": "Analyse de CV selon les Référentiels GFSI",
        "app_description": "Outil d'analyse de CV - GFSI",
        "language": "Langue",
        "french": "Français",
        "english": "Anglais",
        
        # Configuration
        "configuration": "Configuration",
        "api_key": "Clé API Groq :",
        "api_key_help": "La clé API commence par 'gsk_'",
        "model": "Modèle d'IA:",
        "model_help": "Balance entre précision d'analyse et vitesse",
        "models": {
            "llama-3.3-70b-versatile": "Llama 3.3 70B (Haute précision)",
            "llama-3.2-11b-versatile": "Llama 3.2 11B (Équilibré)",
            "llama-3.1-8b-instant": "Llama 3.1 8B (Rapide)",
            "kmi-k2-70b": "KMI K2 70B (Spécialisé)",
            "qwen3-72b": "QWEN 3 72B (Alibaba Cloud)"
        },
        
        # Options d'analyse
        "analysis_options": "Options d'analyse",
        "debug_mode": "Afficher les données brutes (Debug)",
        
        # Administration
        "administration": "Administration",
        "admin_password": "Mot de passe admin :",
        "access_admin": "Accéder au mode admin",
        "exit_admin": "Quitter le mode admin",
        "admin_activated": "Mode admin activé ✅",
        "admin_password_incorrect": "Mot de passe incorrect",
        "create_referential": "Créer un nouveau référentiel",
        "ai_assistant": "Assistant IA de création de référentiel",
        "paste_requirements": "Collez ici les exigences du nouveau standard :",
        "generate_json": "Générer le JSON",
        "generated_referential": "Référentiel généré (à copier/coller dans referentials.py) :",
        "save_referential": "Sauvegarder le référentiel",
        "filename": "Nom du fichier (sans extension) :",
        "referential_saved": "Référentiel sauvegardé dans referentiels/{}.json",
        "error_saving": "Erreur lors de la sauvegarde",
        "referential_generated": "Référentiel généré avec succès !",
        "error_generating": "Erreur lors de la génération du référentiel",
        "please_enter_requirements": "Veuillez saisir les exigences et configurer votre clé API",
        
        # À propos
        "about": "À propos",
        "app_info": """
        **Outil d'analyse CV - GFSI**
        Version 25.12
        
        Référentiels supportés : BRCGS, FSSC 22000, IFS
        """,
        
        # Guide d'utilisation
        "usage_guide": "Guide d'utilisation",
        "usage_instructions": """
        ### Comment utiliser cet outil?
        
        1. **Configuration**:
           - Saisissez votre clé API Groq dans le panneau latéral
           - Sélectionnez le modèle d'IA à utiliser
        
        2. **Analyse**:
           - Téléchargez un CV au format PDF
           - Sélectionnez le référentiel GFSI applicable
           - Lancez l'analyse
        
        3. **Résultats**:
           - Consultez le rapport détaillé avec références aux exigences
           - Explorez les détails par section (Général, Qualifications, etc.)
           - Exportez les résultats au format HTML
        
        **Astuce**: Plus le document est clairement formaté, meilleure sera l'analyse.
        """,
        
        # Analyse de CV
        "cv_analysis": "Analyse de CV",
        "configure_api": "⚠️ Veuillez configurer votre clé API Groq dans le panneau latéral pour continuer.",
        "upload_cv": "📄 Téléchargez un fichier PDF (CV)",
        "upload_help": "Formats supportés : PDF. Taille maximale: 10MB",
        "please_upload_cv": "Veuillez télécharger un fichier PDF pour commencer l'analyse.",
        "referential_preview": "Aperçu des référentiels supportés",
        "select_referential": "📋 Sélectionnez un référentiel",
        "referential_help": "Choisissez le standard GFSI applicable pour ce candidat",
        "analyze_cv": "🔍 Analyser le CV",
        "extracting_text": "Extraction du texte en cours...",
        "no_pages": "Le PDF ne contient aucune page.",
        "no_text_extracted": "Aucun texte n'a pu être extrait du PDF. Vérifiez qu'il ne s'agit pas d'un PDF scanné.",
        "pdf_protected": "Conseils: Vérifiez que le PDF n'est pas protégé ou qu'il ne s'agit pas d'un document scanné sans OCR.",
        "analyzing_cv": "Analyse approfondie du CV en cours...",
        "analysis_failed": "L'analyse n'a pas pu être structurée correctement. Affichage des résultats bruts.",
        "connection_error": "Erreur de connexion à l'API Groq : {}",
        "api_key_invalid": "La clé API semble invalide. Les clés Groq commencent généralement par 'gsk_'.",
        "text_preview": "Aperçu du texte extrait",
        "raw_analysis_data": "Données brutes de l'analyse (Debug)",
        "download_report": "📥 Télécharger le rapport complet",
        
        # Résultats d'analyse
        "analysis_summary": "📊 Résumé de l'analyse selon le référentiel {}",
        "total_requirements": "📊 Total",
        "conformant": "✅ Conformes",
        "partially_conformant": "🟡 Partiel",
        "non_conformant": "❌ Non conformes",
        "compliance_rate": "📈 Taux de conformité",
        "final_recommendation": "Recommandation finale :",
        "major_strengths": "💪 Forces principales",
        "critical_gaps": "⚠️ Lacunes critiques",
        "development_opportunities": "📈 Opportunités",
        "detailed_justification": "📝 Justification",
        "no_justification": "Aucune justification disponible.",
        "detailed_analysis": "📋 Analyse détaillée des exigences",
        "category": "📁 {}",
        "requirement": "📋 Exigence",
        "evaluation": "Évaluation",
        "status": "Statut:",
        "confidence_score": "Score de confiance:",
        "elements_found": "🔍 Éléments trouvés",
        "no_elements": "Aucun élément trouvé",
        "justification": "🧠 Justification",
        "no_justification_detail": "Aucune justification fournie",
        "recommendations": "💡 Recommandations",
        "no_recommendations": "Aucune recommandation",
        "requirement_not_specified": "Exigence non spécifiée",
        "not_evaluated": "Non évalué",
        "reference_not_specified": "Non spécifiée",
        "no_data_available": "Aucune donnée disponible pour la section {}",
        "conclusion": "Conclusion",
        "overall_assessment": "Évaluation générale :",
        "key_strengths": "Forces principales",
        "improvement_points": "Points d'amélioration",
        "no_conclusion": "Aucune conclusion disponible.",
        "general_requirements": "Exigences générales",
        "qualifications": "Qualifications",
        "audit_experience": "Expérience en audit",
        "advanced_requirements": "Exigences avancées",
    },
    "en": {
        # Main texts
        "app_title": "CV Analysis according to GFSI Standards",
        "app_description": "GFSI CV Analysis Tool",
        "language": "Language",
        "french": "French",
        "english": "English",
        
        # Configuration
        "configuration": "Configuration",
        "api_key": "Groq API Key:",
        "api_key_help": "API key starts with 'gsk_'",
        "model": "AI Model:",
        "model_help": "Balance between analysis precision and speed",
        "models": {
            "llama-3.3-70b-versatile": "Llama 3.3 70B (High precision)",
            "llama-3.2-11b-versatile": "Llama 3.2 11B (Balanced)",
            "llama-3.1-8b-instant": "Llama 3.1 8B (Fast)",
            "kmi-k2-70b": "KMI K2 70B (Specialized)",
            "qwen3-72b": "QWEN 3 72B (Alibaba Cloud)"
        },
        
        # Analysis options
        "analysis_options": "Analysis Options",
        "debug_mode": "Show raw data (Debug)",
        
        # Administration
        "administration": "Administration",
        "admin_password": "Admin password:",
        "access_admin": "Access admin mode",
        "exit_admin": "Exit admin mode",
        "admin_activated": "Admin mode activated ✅",
        "admin_password_incorrect": "Incorrect password",
        "create_referential": "Create new referential",
        "ai_assistant": "AI Assistant for referential creation",
        "paste_requirements": "Paste the requirements of the new standard here:",
        "generate_json": "Generate JSON",
        "generated_referential": "Generated referential (copy/paste to referentials.py):",
        "save_referential": "Save referential",
        "filename": "File name (without extension):",
        "referential_saved": "Referential saved in referentiels/{}.json",
        "error_saving": "Error saving",
        "referential_generated": "Referential generated successfully!",
        "error_generating": "Error generating referential",
        "please_enter_requirements": "Please enter requirements and configure your API key",
        
        # About
        "about": "About",
        "app_info": """
        **GFSI CV Analysis Tool**
        Version 25.12
        
        Supported standards: BRCGS, FSSC 22000, IFS
        """,
        
        # Usage guide
        "usage_guide": "Usage Guide",
        "usage_instructions": """
        ### How to use this tool?
        
        1. **Configuration**:
           - Enter your Groq API key in the sidebar
           - Select the AI model to use
        
        2. **Analysis**:
           - Upload a CV in PDF format
           - Select the applicable GFSI standard
           - Launch the analysis
        
        3. **Results**:
           - View the detailed report with references to requirements
           - Explore details by section (General, Qualifications, etc.)
           - Export results in HTML format
        
        **Tip**: The clearer the document is formatted, the better the analysis will be.
        """,
        
        # CV Analysis
        "cv_analysis": "CV Analysis",
        "configure_api": "⚠️ Please configure your Groq API key in the sidebar to continue.",
        "upload_cv": "📄 Upload a PDF file (CV)",
        "upload_help": "Supported formats: PDF. Maximum size: 10MB",
        "please_upload_cv": "Please upload a PDF file to start the analysis.",
        "referential_preview": "Preview of supported standards",
        "select_referential": "📋 Select a standard",
        "referential_help": "Choose the applicable GFSI standard for this candidate",
        "analyze_cv": "🔍 Analyze CV",
        "extracting_text": "Extracting text...",
        "no_pages": "The PDF contains no pages.",
        "no_text_extracted": "No text could be extracted from the PDF. Check if it's a scanned PDF.",
        "pdf_protected": "Tips: Check that the PDF is not protected or that it is not a scanned document without OCR.",
        "analyzing_cv": "In-depth CV analysis in progress...",
        "analysis_failed": "The analysis could not be properly structured. Displaying raw results.",
        "connection_error": "Error connecting to Groq API: {}",
        "api_key_invalid": "The API key seems invalid. Groq keys usually start with 'gsk_'.",
        "text_preview": "Text preview",
        "raw_analysis_data": "Raw analysis data (Debug)",
        "download_report": "📥 Download complete report",
        
        # Analysis results
        "analysis_summary": "📊 Analysis summary according to standard {}",
        "total_requirements": "📊 Total",
        "conformant": "✅ Conformant",
        "partially_conformant": "🟡 Partial",
        "non_conformant": "❌ Non-conformant",
        "compliance_rate": "📈 Compliance rate",
        "final_recommendation": "Final recommendation:",
        "major_strengths": "💪 Major strengths",
        "critical_gaps": "⚠️ Critical gaps",
        "development_opportunities": "📈 Development opportunities",
        "detailed_justification": "📝 Detailed justification",
        "no_justification": "No justification available.",
        "detailed_analysis": "📋 Detailed analysis of requirements",
        "category": "📁 {}",
        "requirement": "📋 Requirement",
        "evaluation": "Evaluation",
        "status": "Status:",
        "confidence_score": "Confidence score:",
        "elements_found": "🔍 Elements found",
        "no_elements": "No elements found",
        "justification": "🧠 Justification",
        "no_justification_detail": "No justification provided",
        "recommendations": "💡 Recommendations",
        "no_recommendations": "No recommendations",
        "requirement_not_specified": "Requirement not specified",
        "not_evaluated": "Not evaluated",
        "reference_not_specified": "Not specified",
        "no_data_available": "No data available for section {}",
        "conclusion": "Conclusion",
        "overall_assessment": "Overall assessment:",
        "key_strengths": "Key strengths",
        "improvement_points": "Improvement points",
        "no_conclusion": "No conclusion available.",
        "general_requirements": "General requirements",
        "qualifications": "Qualifications",
        "audit_experience": "Audit experience",
        "advanced_requirements": "Advanced requirements",
    }
}

def get_text(key, lang="fr"):
    """Get translated text for a given key and language"""
    return TRANSLATIONS.get(lang, TRANSLATIONS["fr"]).get(key, key)

# Fonction pour configurer le client Groq avec validation
def get_groq_client(api_key):
    """
    Initialise et valide un client Groq avec la clé API fournie.
    
    Args:
        api_key (str): Clé API Groq
        
    Returns:
        Groq: Instance de client Groq ou None en cas d'erreur
    """
    if not api_key or not api_key.startswith("gsk_"):
        st.error("La clé API semble invalide. Les clés Groq commencent généralement par 'gsk_'.")
        return None
    
    try:
        client = Groq(api_key=api_key)
        # Test de la connexion avec une requête minimale
        test_response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Test de connexion"}],
            model="llama-3.1-8b-instant",
            max_tokens=10
        )
        if test_response:
            return client
    except Exception as e:
        st.error(f"Erreur de connexion à l'API Groq : {str(e)}")
        return None

# Extraction améliorée de texte depuis un PDF
def extract_text_from_pdf(file):
    """
    Extrait le texte d'un fichier PDF avec gestion optimisée des erreurs.
    
    Args:
        file (UploadedFile): Fichier PDF téléchargé
        
    Returns:
        str: Texte extrait du PDF ou None en cas d'erreur
    """
    try:
        with st.spinner("Extraction du texte en cours..."):
            reader = PdfReader(file)
            
            # Vérification des pages vides
            if len(reader.pages) == 0:
                st.warning("Le PDF ne contient aucune page.")
                return None
            
            # Extraction avec nettoyage des caractères spéciaux
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    # Nettoyage des caractères problématiques
                    page_text = re.sub(r'\s+', ' ', page_text)
                    text_parts.append(page_text)
            
            if not text_parts:
                st.warning("Aucun texte n'a pu être extrait du PDF. Vérifiez qu'il ne s'agit pas d'un PDF scanné.")
                return None
                
            return " ".join(text_parts)
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du texte : {str(e)}")
        st.info("Conseils: Vérifiez que le PDF n'est pas protégé ou qu'il ne s'agit pas d'un document scanné sans OCR.")
        return None

# Analyse granulaire du CV avec l'API Groq et référentiel
def analyze_cv_with_groq(cv_text, referential_name, groq_client, model="llama-3.3-70b-versatile"):
    """
    Analyse approfondie du CV en fonction des référentiels GFSI avec analyse granulaire et pondération.
    
    Args:
        cv_text (str): Texte du CV à analyser
        referential_name (str): Nom du référentiel GFSI sélectionné
        groq_client (Groq): Instance de client Groq
        model (str): Modèle LLM à utiliser
        
    Returns:
        dict: Résultats structurés de l'analyse ou None en cas d'erreur
    """
    referential_data = REFERENTIALS.get(referential_name, {})
    
    # Vérifier si c'est un référentiel au nouveau format (avec catégories pondérées)
    if "categories" in referential_data:
        # Nouveau format avec analyse granulaire
        return analyze_cv_granular(cv_text, referential_name, referential_data, groq_client, model)
    else:
        # Ancien format - utiliser l'analyse existante
        return analyze_cv_traditional(cv_text, referential_name, referential_data, groq_client, model)

def analyze_cv_granular(cv_text, referential_name, referential_data, groq_client, model):
    """
    Analyse granulaire avec pondération et référencement précis.
    """
    # Construction d'un prompt structuré optimisé
    prompt = create_enhanced_analysis_prompt(cv_text, referential_data, referential_name)
    
    try:
        with st.spinner("Analyse approfondie du CV en cours..."):
            messages = [
                {"role": "system", "content": "Vous êtes un expert en conformité GFSI qui fournit des analyses structurées avec références systématiques aux exigences."},
                {"role": "user", "content": prompt}
            ]
            
            response = groq_client.chat.completions.create(
                messages=messages,
                model=model,
                max_tokens=4000,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parsing de la réponse en JSON
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                # Si le parsing JSON échoue, tenter de récupérer le contenu brut
                content = response.choices[0].message.content
                st.warning("L'analyse n'a pas pu être structurée correctement. Affichage des résultats bruts.")
                return {"raw_content": content}
    except Exception as e:
        st.error(f"Erreur lors de l'analyse du CV : {str(e)}")
        return None

def analyze_cv_traditional(cv_text, referential_name, referential_data, groq_client, model):
    """
    Analyse traditionnelle pour les anciens référentiels.
    """
    # Structuration des exigences pour analyse systématique
    requirements_categories = {
        "General_Requirements": referential_data.get("General_Requirements", {}),
        "Qualifications": referential_data.get("Qualifications", {}),
        "Audit_Experience": referential_data.get("Audit_Experience", {}),
        "Advanced_Requirements": referential_data.get("Advanced_Requirements", {})
    }
    
    # Construction d'un prompt structuré pour obtenir une réponse analysable
    prompt = f"""
    Vous êtes un expert en évaluation des compétences selon les référentiels GFSI.
    
    TÂCHE: Analysez ce CV pour vérifier sa conformité avec le référentiel {referential_name} de manière systématique.
    
    INSTRUCTIONS:
    1. Ne jamais mentionner le nom du candidat - utilisez toujours "le candidat"
    2. Pour chaque exigence, fournissez:
       - La référence exacte de l'exigence (code/numéro)
       - Votre évaluation avec STATUT: CONFORME, NON CONFORME, ou PARTIELLEMENT CONFORME
       - Les éléments du CV justifiant votre évaluation
       - Des recommandations spécifiques si nécessaire
    3. Structurez votre réponse exactement selon le format JSON demandé à la fin
    
    RÉFÉRENTIEL {referential_name} - EXIGENCES:
    
    SECTION 1: EXIGENCES GÉNÉRALES
    {json.dumps(requirements_categories["General_Requirements"], ensure_ascii=False, indent=2)}
    
    SECTION 2: QUALIFICATIONS
    {json.dumps(requirements_categories["Qualifications"], ensure_ascii=False, indent=2)}
    
    SECTION 3: EXPÉRIENCE EN AUDIT
    {json.dumps(requirements_categories["Audit_Experience"], ensure_ascii=False, indent=2)}
    
    SECTION 4: EXIGENCES AVANCÉES
    {json.dumps(requirements_categories["Advanced_Requirements"], ensure_ascii=False, indent=2)}
    
    CV DU CANDIDAT:
    {cv_text}
    
    INSTRUCTIONS SUPPLÉMENTAIRES:
    - Vérifiez chaque formation et expérience plusieurs fois, car les terminologies peuvent varier
    - Évaluez si l'équivalence des formations est acceptable selon le référentiel
    - Identifiez précisément chaque lacune avec référence à l'exigence spécifique
    
    FORMAT DE RÉPONSE: Fournissez votre analyse au format JSON avec la structure suivante:
    {{
      "analysis": {{
        "general_requirements": [
          {{
            "reference": "REF-CODE-1",
            "requirement": "Description de l'exigence",
            "status": "CONFORME/NON CONFORME/PARTIELLEMENT CONFORME",
            "evidence": "Éléments du CV justifiant l'évaluation",
            "recommendations": "Recommandations si nécessaire"
          }}
        ],
        "qualifications": [...],
        "audit_experience": [...],
        "advanced_requirements": [...]
      }},
      "summary": {{
        "conformant_count": 12,  
        "non_conformant_count": 3,
        "partially_conformant_count": 2,
        "overall_assessment": "CONFORME/NON CONFORME/PARTIELLEMENT CONFORME",
        "key_strengths": ["Force 1", "Force 2"],
        "key_gaps": ["Lacune 1", "Lacune 2"],
        "conclusion": "Conclusion générale sur l'adéquation du candidat"
      }}
    }}
    
    IMPORTANT: Assurez-vous que votre réponse soit un JSON valide et bien structuré.
    """
    
    try:
        with st.spinner("Analyse approfondie du CV en cours..."):
            messages = [
                {"role": "system", "content": "Vous êtes un expert en conformité GFSI qui fournit des analyses structurées avec références systématiques aux exigences."},
                {"role": "user", "content": prompt}
            ]
            
            response = groq_client.chat.completions.create(
                messages=messages,
                model=model,
                max_tokens=4000,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parsing de la réponse en JSON
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                # Si le parsing JSON échoue, tenter de récupérer le contenu brut
                content = response.choices[0].message.content
                st.warning("L'analyse n'a pas pu être structurée correctement. Affichage des résultats bruts.")
                return {"raw_content": content}
    except Exception as e:
        st.error(f"Erreur lors de l'analyse du CV : {str(e)}")
        return None

def create_enhanced_analysis_prompt(cv_text, referential_data, referential_name):
    """
    Crée un prompt optimisé pour l'analyse granulaire avec pondération.
    """
    
    # Construction progressive du prompt
    prompt_parts = []
    
    # 1. En-tête et contexte
    prompt_parts.append(f"""
    EXPERT EN ÉVALUATION DE CONFORMITÉ GFSI - ANALYSE STRUCTURÉE
    
    TÂCHE : Analyser ce CV selon le référentiel {referential_name}
    FORMAT DE RÉPONSE : JSON strict (obligatoire)
    CONFIDENTIALITÉ : Ne jamais mentionner le nom du candidat
    
    MÉTHODOLOGIE D'ANALYSE REQUISE :
    1. LECTURE APPROFONDIE du CV et du référentiel
    2. ANALYSE EXIGENCE PAR EXIGENCE avec référencement systématique
    3. JUSTIFICATION précise avec citations du CV
    4. ÉVALUATION OBJECTIVE selon critères définis
    """)
    
    # 2. Structure détaillée du référentiel
    prompt_parts.append("STRUCTURE DU RÉFÉRENTIEL À ANALYSER :")
    
    for category_name, category_data in referential_data.get("categories", {}).items():
        prompt_parts.append(f"\nCATÉGORIE : {category_name} (Poids: {category_data.get('weight', 0)})")
        prompt_parts.append(f"Description: {category_data.get('description', '')}")
        prompt_parts.append("EXIGENCES À VÉRIFIER :")
        
        for subcategory_name, subcategory_data in category_data.get("subcategories", {}).items():
            prompt_parts.append(f"  SOUS-CATÉGORIE : {subcategory_name} (Poids: {subcategory_data.get('weight', 0)})")
            for i, req in enumerate(subcategory_data.get("requirements", []), 1):
                prompt_parts.append(f"    [{req.get('id', f'{category_name[:3].upper()}-{subcategory_name[:3].upper()}-{i:02d}')}]" + 
                                  f" {req.get('text', 'Exigence non définie')}")
                if req.get('critical', False):
                    prompt_parts.append("    ⚠️ EXIGENCE CRITIQUE")
                prompt_parts.append(f"    Acceptable minimum: {req.get('minimum_acceptable', 'Non spécifié')}")
    
    # 3. CV du candidat
    prompt_parts.append(f"\nCV DU CANDIDAT À ANALYSER :\n{cv_text[:8000]}...")  # Limite pour éviter dépassement tokens
    
    # 4. Instructions détaillées d'analyse
    prompt_parts.append("""
    INSTRUCTIONS D'ANALYSE DÉTAILLÉES :
    
    POUR CHAQUE EXIGENCE, FOURNIR :
    1. RÉFÉRENCE EXACTE de l'exigence analysée
    2. TEXTE EXACT de l'exigence du référentiel
    3. ÉLÉMENTS TROUVÉS dans le CV (citations précises avec dates si disponibles)
    4. ANALYSE CRITIQUE avec justification objective
    5. STATUT : CONFORME | PARTIELLEMENT CONFORME | NON CONFORME
    6. SCORE DE CONFIANCE : 0.0 à 1.0 (précision de l'analyse)
    7. RECOMMANDATIONS concrètes si non-conforme
    
    CRITÈRES D'ÉVALUATION :
    🟢 CONFORME : Exigence clairement satisfaite avec preuves concrètes
    🟡 PARTIELLEMENT CONFORME : Équivalence acceptable ou expérience partielle
    🔴 NON CONFORME : Exigence clairement absente ou insuffisamment démontrée
    
    FORMAT JSON OBLIGATOIRE :
    {
      "analysis_metadata": {
        "referential": "nom_du_referentiel",
        "analysis_timestamp": "date_ISO8601",
        "total_requirements_analyzed": 0,
        "confidence_level": 0.0
      },
      "detailed_evaluation": [
        {
          "requirement_reference": "REF-CODE-01",
          "requirement_category": "Nom de la catégorie",
          "requirement_text": "Texte exact de l'exigence",
          "candidate_evidence": "Citations précises du CV avec dates",
          "analysis_justification": "Explication détaillée de l'évaluation",
          "compliance_status": "CONFORME/PARTIELLEMENT CONFORME/NON CONFORME",
          "confidence_score": 0.95,
          "recommendations": "Actions spécifiques pour amélioration"
        }
      ],
      "summary_analysis": {
        "compliance_statistics": {
          "total_requirements": 0,
          "conformant": 0,
          "partially_conformant": 0,
          "non_conformant": 0,
          "compliance_rate_percentage": 0.0
        },
        "key_findings": {
          "major_strengths": ["Force principale 1"],
          "critical_gaps": ["Lacune critique 1"],
          "development_opportunities": ["Opportunité de développement 1"]
        },
        "final_recommendation": "RECOMMANDÉ/À AMÉLIORER/À REJETER",
        "detailed_justification": "Justification globale de la recommandation"
      }
    }
    
    IMPORTANT :
    - Respecter ABSOLUMENT le format JSON spécifié
    - Fournir des citations précises du CV
    - Être objectif et factuel dans les évaluations
    - Ne pas faire d'assomptions non fondées
    - Inclure des scores de confiance réalistes
    """)
    
    return "\n".join(prompt_parts)

# Affichage amélioré des résultats d'analyse
def display_analysis_results(analysis_result, referential):
    """
    Affiche les résultats de l'analyse de manière structurée et visuelle.
    
    Args:
        analysis_result (dict): Résultats de l'analyse
        referential (str): Référentiel GFSI utilisé pour l'analyse
    """
    if not analysis_result:
        return
    
    # Cas où le résultat est brut (non JSON)
    if "raw_content" in analysis_result:
        st.markdown(
            f"""
            <div style='font-size:18px;line-height:1.6;margin-top:20px;'>
                {analysis_result["raw_content"]}
            </div>
            """,
            unsafe_allow_html=True
        )
        return
    
    # Vérifier si c'est le nouveau format granulaire
    if "detailed_evaluation" in analysis_result:
        display_granular_analysis_results(analysis_result, referential)
    else:
        display_traditional_analysis_results(analysis_result, referential)

def display_granular_analysis_results(analysis_result, referential):
    """
    Affiche les résultats de l'analyse granulaire avec pondération.
    """
    # Affichage du résumé global
    st.markdown(f"## 📊 Résumé de l'analyse selon le référentiel {referential}")
    
    summary_analysis = analysis_result.get("summary_analysis", {})
    compliance_stats = summary_analysis.get("compliance_statistics", {})
    
    conformant = compliance_stats.get("conformant", 0)
    non_conformant = compliance_stats.get("non_conformant", 0)
    partially_conformant = compliance_stats.get("partially_conformant", 0)
    total = compliance_stats.get("total_requirements", 0)
    
    # Affichage des statistiques avec indicateurs visuels
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📊 Total", total)
    with col2:
        st.metric("✅ Conformes", conformant, f"{int(conformant/total*100 if total else 0)}%")
    with col3:
        st.metric("🟡 Partiel", partially_conformant, f"{int(partially_conformant/total*100 if total else 0)}%")
    with col4:
        st.metric("❌ Non conformes", non_conformant, f"{int(non_conformant/total*100 if total else 0)}%")
    with col5:
        compliance_rate = compliance_stats.get("compliance_rate_percentage", 0)
        st.metric("📈 Taux de conformité", f"{compliance_rate:.1f}%")
    
    # Conclusion globale avec couleur selon le niveau
    final_recommendation = summary_analysis.get("final_recommendation", "Non déterminée")
    recommendation_color = {
        "RECOMMANDÉ": "#28a745",
        "À AMÉLIORER": "#ffc107",
        "À REJETER": "#dc3545"
    }.get(final_recommendation, "#6c757d")
    
    st.markdown(
        f"""
        <div style="background-color:{recommendation_color};color:white;padding:20px;border-radius:10px;margin-top:20px;font-size:22px;line-height:1.8;text-align:center;">
            <strong>Recommandation finale :</strong> {final_recommendation}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Forces et lacunes
    key_findings = summary_analysis.get("key_findings", {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 💪 Forces principales")
        for strength in key_findings.get("major_strengths", []):
            st.markdown(f"✅ {strength}")
    
    with col2:
        st.markdown("### ⚠️ Lacunes critiques")
        for gap in key_findings.get("critical_gaps", []):
            st.markdown(f"❌ {gap}")
    
    with col3:
        st.markdown("### 📈 Opportunités")
        for opportunity in key_findings.get("development_opportunities", []):
            st.markdown(f"📈 {opportunity}")
    
    # Justification détaillée
    st.markdown("### 📝 Justification")
    st.markdown(summary_analysis.get("detailed_justification", "Aucune justification disponible."))
    
    # Affichage détaillé des exigences analysées
    st.markdown("## 📋 Analyse détaillée des exigences")
    
    detailed_evaluation = analysis_result.get("detailed_evaluation", [])
    
    # Regrouper par catégorie pour affichage organisé
    categories = {}
    for item in detailed_evaluation:
        category = item.get("requirement_category", "Non catégorisé")
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    
    # Création d'onglets pour chaque catégorie
    if categories:
        tabs = st.tabs(list(categories.keys()))
        
        for i, (category_name, category_items) in enumerate(categories.items()):
            with tabs[i]:
                st.markdown(f"### 📁 {category_name}")
                
                # Tri par statut (conforme d'abord, puis partiel, puis non conforme)
                sorted_items = sorted(category_items, key=lambda x: (
                    0 if x.get("compliance_status") == "CONFORME" else
                    1 if x.get("compliance_status") == "PARTIELLEMENT CONFORME" else
                    2
                ))
                
                for item in sorted_items:
                    # Couleur en fonction du statut
                    status = item.get("compliance_status", "")
                    status_color = {
                        "CONFORME": "#28a745",
                        "PARTIELLEMENT CONFORME": "#ffc107",
                        "NON CONFORME": "#dc3545"
                    }.get(status, "#6c757d")
                    
                    status_emoji = {
                        "CONFORME": "✅",
                        "PARTIELLEMENT CONFORME": "🟡",
                        "NON CONFORME": "❌"
                    }.get(status, "❓")
                    
                    # Création d'un expander pour chaque exigence
                    expander_title = f"{status_emoji} {item.get('requirement_reference', 'REF')} - {status} ({item.get('confidence_score', 0):.2f})"
                    with st.expander(expander_title):
                        st.markdown(f"**📋 Exigence**")
                        st.write(item.get('requirement_text', 'Exigence non spécifiée'))
                        
                        st.markdown(f"**{status_emoji} Évaluation**")
                        st.markdown(f"**Statut:** {status}")
                        st.markdown(f"**Score de confiance:** {item.get('confidence_score', 0):.2f}/1.00")
                        
                        st.markdown(f"**🔍 Éléments trouvés**")
                        st.info(item.get('candidate_evidence', 'Aucun élément trouvé'))
                        
                        st.markdown(f"**🧠 Justification**")
                        st.write(item.get('analysis_justification', 'Aucune justification fournie'))
                        
                        st.markdown(f"**💡 Recommandations**")
                        st.success(item.get('recommendations', 'Aucune recommandation'))

def display_traditional_analysis_results(analysis_result, referential):
    """
    Affiche les résultats de l'analyse traditionnelle (pour compatibilité).
    """
    # Affichage du résumé global
    st.markdown(f"## Résumé de l'analyse selon le référentiel {referential}")
    
    summary = analysis_result.get("summary", {})
    conformant = summary.get("conformant_count", 0)
    non_conformant = summary.get("non_conformant_count", 0)
    partially = summary.get("partially_conformant_count", 0)
    total = conformant + non_conformant + partially
    
    # Affichage des statistiques
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total des exigences", total)
    with col2:
        st.metric("Conformes", conformant, f"{int(conformant/total*100 if total else 0)}%")
    with col3:
        st.metric("Non conformes", non_conformant, f"{int(non_conformant/total*100 if total else 0)}%")
    with col4:
        st.metric("Partiellement conformes", partially, f"{int(partially/total*100 if total else 0)}%")
    
    # Conclusion globale
    conclusion_color = {
        "CONFORME": "#28a745",
        "NON CONFORME": "#dc3545",
        "PARTIELLEMENT CONFORME": "#ffc107"
    }.get(summary.get("overall_assessment", ""), "#6c757d")
    
    st.markdown(
        f"""
        <div style="background-color:{conclusion_color};color:white;padding:20px;border-radius:10px;margin-top:20px;font-size:22px;line-height:1.8;">
            <strong>Évaluation générale :</strong> {summary.get("overall_assessment", "Non déterminée")}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Forces et lacunes
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Forces principales")
        for strength in summary.get("key_strengths", []):
            st.markdown(f"✅ {strength}")
    
    with col2:
        st.markdown("### Points d'amélioration")
        for gap in summary.get("key_gaps", []):
            st.markdown(f"❌ {gap}")
    
    # Conclusion détaillée
    st.markdown("### Conclusion")
    st.markdown(summary.get("conclusion", "Aucune conclusion disponible."))
    
    # Affichage détaillé des sections d'analyse
    analysis = analysis_result.get("analysis", {})
    
    # Liste des sections pour affichage uniforme
    sections = [
        ("Exigences générales", analysis.get("general_requirements", [])),
        ("Qualifications", analysis.get("qualifications", [])),
        ("Expérience en audit", analysis.get("audit_experience", [])),
        ("Exigences avancées", analysis.get("advanced_requirements", []))
    ]
    
    # Création d'onglets pour chaque section
    tabs = st.tabs([section[0] for section in sections])
    
    # Affichage du contenu de chaque section dans son onglet
    for i, (section_name, section_data) in enumerate(sections):
        with tabs[i]:
            if not section_data:
                st.info(f"Aucune donnée disponible pour la section {section_name}")
                continue
                
            for item in section_data:
                # Couleur en fonction du statut
                status_color = {
                    "CONFORME": "#28a745",
                    "NON CONFORME": "#dc3545",
                    "PARTIELLEMENT CONFORME": "#ffc107"
                }.get(item.get("status", ""), "#6c757d")
                
                # Création d'un expander pour chaque exigence
                with st.expander(f"{item.get('reference', 'REF')} - {item.get('requirement', 'Exigence')} ({item.get('status', 'Non évalué')})"):
                    st.markdown(
                        f"""
                        <div style="border-left: 5px solid {status_color}; padding-left: 10px;">
                            <p><strong>Référence:</strong> {item.get('reference', 'Non spécifiée')}</p>
                            <p><strong>Exigence:</strong> {item.get('requirement', 'Non spécifiée')}</p>
                            <p><strong>Statut:</strong> <span style="background-color:{status_color};color:white;padding:3px 6px;border-radius:3px;">{item.get('status', 'Non évalué')}</span></p>
                            <p><strong>Éléments justificatifs:</strong> {item.get('evidence', 'Aucun')}</p>
                            <p><strong>Recommandations:</strong> {item.get('recommendations', 'Aucune')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

# Génération d'un rapport exportable
def generate_exportable_report(analysis_result, referential, cv_text):
    """
    Génère un rapport exportable basé sur l'analyse du CV.
    
    Args:
        analysis_result (dict): Résultats de l'analyse
        referential (str): Référentiel utilisé
        cv_text (str): Texte du CV analysé
        
    Returns:
        str: HTML du rapport
    """
    if not analysis_result or "raw_content" in analysis_result:
        return None
    
    # Vérifier si c'est le nouveau format granulaire
    if "detailed_evaluation" in analysis_result:
        return generate_granular_report(analysis_result, referential, cv_text)
    else:
        return generate_traditional_report(analysis_result, referential, cv_text)

def generate_granular_report(analysis_result, referential, cv_text):
    """
    Génère un rapport pour le format d'analyse granulaire.
    """
    summary_analysis = analysis_result.get("summary_analysis", {})
    compliance_stats = summary_analysis.get("compliance_statistics", {})
    key_findings = summary_analysis.get("key_findings", {})
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Rapport d'analyse CV - {referential}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
            .section {{ margin-bottom: 30px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
            .stat-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
            .item {{ border-left: 5px solid #ccc; padding-left: 15px; margin-bottom: 15px; }}
            .conforme {{ border-color: #28a745; background-color: #f8fff9; }}
            .non-conforme {{ border-color: #dc3545; background-color: #fff8f8; }}
            .partiel {{ border-color: #ffc107; background-color: #fffdf8; }}
            .status-badge {{ padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; font-weight: bold; }}
            .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; }}
            .recommendation {{ 
                padding: 20px; 
                border-radius: 10px; 
                text-align: center; 
                font-size: 1.2em; 
                font-weight: bold;
                margin: 20px 0;
            }}
            .conforme-rec {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .ameliorer-rec {{ background-color: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
            .rejeter-rec {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .category-header {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0 10px 0; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Rapport d'analyse de CV</h1>
            <p><strong>Référentiel:</strong> {referential}</p>
            <p><strong>Date:</strong> {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        <div class="section summary">
            <h2>📊 Résumé de l'analyse</h2>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{compliance_stats.get('total_requirements', 0)}</div>
                    <div>Total des exigences</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #28a745;">{compliance_stats.get('conformant', 0)}</div>
                    <div>Conformes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #ffc107;">{compliance_stats.get('partially_conformant', 0)}</div>
                    <div>Partiellement conformes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #dc3545;">{compliance_stats.get('non_conformant', 0)}</div>
                    <div>Non conformes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #007bff;">{compliance_stats.get('compliance_rate_percentage', 0):.1f}%</div>
                    <div>Taux de conformité</div>
                </div>
            </div>
        </div>
    """
    
    # Recommandation finale
    final_recommendation = summary_analysis.get("final_recommendation", "Non déterminée")
    rec_class = ""
    if "RECOMMANDÉ" in final_recommendation:
        rec_class = "conforme-rec"
    elif "À AMÉLIORER" in final_recommendation:
        rec_class = "ameliorer-rec"
    elif "À REJETER" in final_recommendation:
        rec_class = "rejeter-rec"
    
    html += f"""
        <div class="recommendation {rec_class}">
            Recommandation finale: {final_recommendation}
        </div>
    """
    
    # Forces et lacunes
    html += """
        <div class="section summary">
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                <div>
                    <h3>💪 Forces principales</h3>
                    <ul>
    """
    for strength in key_findings.get("major_strengths", []):
        html += f"<li>{strength}</li>"
    html += """
                    </ul>
                </div>
                <div>
                    <h3>⚠️ Lacunes critiques</h3>
                    <ul>
    """
    for gap in key_findings.get("critical_gaps", []):
        html += f"<li>{gap}</li>"
    html += """
                    </ul>
                </div>
                <div>
                    <h3>📈 Opportunités</h3>
                    <ul>
    """
    for opportunity in key_findings.get("development_opportunities", []):
        html += f"<li>{opportunity}</li>"
    html += """
                    </ul>
                </div>
            </div>
        </div>
    """
    
    # Justification détaillée
    html += f"""
        <div class="section summary">
            <h3>📝 Justification détaillée</h3>
            <p>{summary_analysis.get("detailed_justification", "Aucune justification disponible.")}</p>
        </div>
    """
    
    # Analyse détaillée des exigences
    html += """
        <div class="section">
            <h2>📋 Analyse détaillée des exigences</h2>
    """
    
    detailed_evaluation = analysis_result.get("detailed_evaluation", [])
    
    # Regrouper par catégorie
    categories = {}
    for item in detailed_evaluation:
        category = item.get("requirement_category", "Non catégorisé")
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    
    for category_name, category_items in categories.items():
        html += f'<div class="category-header">📁 {category_name}</div>'
        
        html += """
            <table>
                <thead>
                    <tr>
                        <th>Référence</th>
                        <th>Exigence</th>
                        <th>Statut</th>
                        <th>Confiance</th>
                        <th>Éléments trouvés</th>
                        <th>Recommandations</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in category_items:
            status = item.get("compliance_status", "")
            status_color = {
                "CONFORME": "#28a745",
                "PARTIELLEMENT CONFORME": "#ffc107",
                "NON CONFORME": "#dc3545"
            }.get(status, "#6c757d")
            
            html += f"""
                <tr class="{'conforme' if status == 'CONFORME' else 'partiel' if status == 'PARTIELLEMENT CONFORME' else 'non-conforme'}">
                    <td><strong>{item.get('requirement_reference', 'REF')}</strong></td>
                    <td>{item.get('requirement_text', 'Exigence non spécifiée')}</td>
                    <td><span class="status-badge" style="background-color: {status_color};">{status}</span></td>
                    <td>{item.get('confidence_score', 0):.2f}</td>
                    <td>{item.get('candidate_evidence', 'Aucun élément trouvé')}</td>
                    <td>{item.get('recommendations', 'Aucune recommandation')}</td>
                </tr>
            """
        
        html += """
                </tbody>
            </table>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

def generate_traditional_report(analysis_result, referential, cv_text):
    """
    Génère un rapport pour le format d'analyse traditionnel (pour compatibilité).
    """
    summary = analysis_result.get("summary", {})
    analysis = analysis_result.get("analysis", {})
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Rapport d'analyse CV - {referential}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            .section {{ margin-bottom: 30px; }}
            .item {{ border-left: 5px solid #ccc; padding-left: 15px; margin-bottom: 15px; }}
            .conforme {{ border-color: #28a745; }}
            .non-conforme {{ border-color: #dc3545; }}
            .partiel {{ border-color: #ffc107; }}
            .status-badge {{ padding: 3px 6px; border-radius: 3px; color: white; font-size: 12px; }}
            .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Rapport d'analyse de CV</h1>
            <p>Référentiel: <strong>{referential}</strong></p>
            <p>Date: <strong>{pd.Timestamp.now().strftime('%d/%m/%Y')}</strong></p>
        </div>
        
        <div class="section summary">
            <h2>Résumé de l'analyse</h2>
            <table>
                <tr>
                    <th>Exigences conformes</th>
                    <th>Exigences non conformes</th>
                    <th>Exigences partiellement conformes</th>
                    <th>Évaluation générale</th>
                </tr>
                <tr>
                    <td>{summary.get('conformant_count', 0)}</td>
                    <td>{summary.get('non_conformant_count', 0)}</td>
                    <td>{summary.get('partially_conformant_count', 0)}</td>
                    <td><strong>{summary.get('overall_assessment', 'Non déterminée')}</strong></td>
                </tr>
            </table>
            
            <h3>Forces principales</h3>
            <ul>
                {' '.join(f'<li>{strength}</li>' for strength in summary.get('key_strengths', []))}
            </ul>
            
            <h3>Points d'amélioration</h3>
            <ul>
                {' '.join(f'<li>{gap}</li>' for gap in summary.get('key_gaps', []))}
            </ul>
            
            <h3>Conclusion</h3>
            <p>{summary.get('conclusion', 'Aucune conclusion disponible.')}</p>
        </div>
    """
    
    # Ajout des sections détaillées
    sections = [
        ("Exigences générales", analysis.get("general_requirements", [])),
        ("Qualifications", analysis.get("qualifications", [])),
        ("Expérience en audit", analysis.get("audit_experience", [])),
        ("Exigences avancées", analysis.get("advanced_requirements", []))
    ]
    
    for section_name, section_data in sections:
        html += f"""
        <div class="section">
            <h2>{section_name}</h2>
        """
        
        if not section_data:
            html += "<p>Aucune donnée disponible pour cette section</p>"
        else:
            for item in section_data:
                status = item.get('status', '')
                status_class = ""
                if "CONFORME" in status and "NON" not in status:
                    status_class = "conforme"
                elif "NON CONFORME" in status:
                    status_class = "non-conforme"
                elif "PARTIELLEMENT" in status:
                    status_class = "partiel"
                
                html += f"""
                <div class="item {status_class}">
                    <h3>{item.get('reference', 'REF')} - {item.get('requirement', 'Exigence')}</h3>
                    <p><strong>Statut:</strong> <span class="status-badge" style="background-color: {'#28a745' if status_class == 'conforme' else '#dc3545' if status_class == 'non-conforme' else '#ffc107'};">{status}</span></p>
                    <p><strong>Éléments justificatifs:</strong> {item.get('evidence', 'Aucun')}</p>
                    <p><strong>Recommandations:</strong> {item.get('recommendations', 'Aucune')}</p>
                </div>
                """
        
        html += "</div>"
    
    html += """
    </body>
    </html>
    """
    
    return html

# Fonction principale améliorée
def main():
    """
    Interface principale améliorée avec fonctionnalités d'exportation et statistiques.
    """
    # Barre latérale pour configuration
    with st.sidebar:
        st.image("https://via.placeholder.com/150x60?text=GFSI+Analyzer", width=150)
        st.title("Configuration")
        
        # Gestion de la clé API avec sauvegarde dans session_state
        if "api_key" not in st.session_state:
            st.session_state.api_key = ""
        
        api_key = st.text_input(
            "Clé API Groq :", 
            value=st.session_state.api_key,
            type="password",
            help="La clé API commence par 'gsk_'"
        )
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            st.session_state.groq_client = None if not api_key else get_groq_client(api_key)
        
        if "groq_client" not in st.session_state:
            st.session_state.groq_client = None if not api_key else get_groq_client(api_key)
        
        # Sélection du modèle
        model_options = {
            "llama-3.3-70b-versatile": "Llama 3.3 70B (Haute précision)",
            "meta-llama/llama-4-maverick-17b-128e-instruct": "Llama 4 Maverick",
            "llama-3.1-8b-instant": "Llama 3.1 8B (Rapide)",
            "moonshotai/kimi-k2-instruct": "KMI K2 70B (Spécialisé)",
            "qwen/qwen3-32b": "QWEN 3 72B (Alibaba Cloud)"
        }
        selected_model = st.selectbox(
            "Modèle d'IA:",
            options=list(model_options.keys()),
            format_func=lambda x: model_options[x],
            help="Balance entre précision d'analyse et vitesse"
        )
        
        st.markdown("---")
        st.markdown("### Options d'analyse")
        
        # Options de debug pour développement
        show_debug = st.checkbox("Afficher les données brutes (Debug)", False)
        
        # Interface admin pour création de référentiels
        st.markdown("---")
        st.markdown("### 🔐 Administration")
        
        if "admin_mode" not in st.session_state:
            st.session_state.admin_mode = False
        
        if not st.session_state.admin_mode:
            admin_password = st.text_input("Mot de passe admin :", type="password")
            if st.button("🔐 Accéder au mode admin"):
                if is_admin_authenticated(admin_password):
                    st.session_state.admin_mode = True
                    st.success("Mode admin activé !")
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
        else:
            st.success("Mode admin activé ✅")
            if st.button("🚪 Quitter le mode admin"):
                st.session_state.admin_mode = False
                st.rerun()
            
            # Interface de création de référentiel
            with st.expander("➕ Créer un nouveau référentiel"):
                st.markdown("### Assistant IA de création de référentiel")
                exigences_texte = st.text_area("Collez ici les exigences du nouveau standard :", height=300)
                
                if st.button("🤖 Générer le JSON"):
                    if exigences_texte and st.session_state.groq_client:
                        with st.spinner("Génération du référentiel en cours..."):
                            referential_json = create_referential_with_ai(exigences_texte, st.session_state.groq_client)
                            if referential_json:
                                st.session_state.generated_referential = referential_json
                                st.success("Référentiel généré avec succès !")
                                st.json(referential_json)
                            else:
                                st.error("Erreur lors de la génération du référentiel")
                    else:
                        st.warning("Veuillez saisir les exigences et configurer votre clé API")
                
                # Afficher le référentiel généré s'il existe
                if "generated_referential" in st.session_state:
                    st.markdown("### Référentiel généré (à copier/coller dans referentials.py) :")
                    st.code(json.dumps(st.session_state.generated_referential, indent=2, ensure_ascii=False), language="json")
                    
                    # Option de sauvegarde
                    filename = st.text_input("Nom du fichier (sans extension) :", 
                                           value=st.session_state.generated_referential.get("metadata", {}).get("name", "nouveau_referentiel"))
                    if st.button("💾 Sauvegarder le référentiel"):
                        if save_referential_to_json(st.session_state.generated_referential, filename):
                            st.success(f"Référentiel sauvegardé dans referentiels/{filename}.json")
                            # Recharger les référentiels
                            global REFERENTIALS
                            REFERENTIALS = load_referentials_from_json()
                        else:
                            st.error("Erreur lors de la sauvegarde")
        
        # Informations supplémentaires
        st.markdown("---")
        st.markdown("### À propos")
        st.info("""
        **Outil d'analyse CV - GFSI**
        Version 25.12
        
        Référentiels supportés : BRCGS, FSSC 22000, IFS
        """)

    # Contenu principal
    st.title("Analyse de CV selon les Référentiels GFSI")
    st.markdown("---")

    # Panneau d'information avec des instructions complètes
    with st.expander("ℹ️ Guide d'utilisation", expanded=True):
        st.markdown("""
        ### Comment utiliser cet outil?
        
        1. **Configuration**:
           - Saisissez votre clé API Groq dans le panneau latéral
           - Sélectionnez le modèle d'IA à utiliser
        
        2. **Analyse**:
           - Téléchargez un CV au format PDF
           - Sélectionnez le référentiel GFSI applicable
           - Lancez l'analyse
        
        3. **Résultats**:
           - Consultez le rapport détaillé avec références aux exigences
           - Explorez les détails par section (Général, Qualifications, etc.)
           - Exportez les résultats au format HTML
        
        **Astuce**: Plus le document est clairement formaté, meilleure sera l'analyse.
        """)
    
    # Contenu principal - Interface d'analyse
    st.markdown("## Analyse de CV")
    
    # Vérification de la présence du client Groq
    if not st.session_state.groq_client:
        st.warning("⚠️ Veuillez configurer votre clé API Groq dans le panneau latéral pour continuer.")
        return
    
    # Chargement du fichier PDF
    uploaded_file = st.file_uploader(
        "📄 Téléchargez un fichier PDF (CV)", 
        type="pdf",
        help="Formats supportés : PDF. Taille maximale: 10MB"
    )
    
    if not uploaded_file:
        st.info("Veuillez télécharger un fichier PDF pour commencer l'analyse.")
        # Affichage d'exemples des référentiels
        st.markdown("### Aperçu des référentiels supportés")
        for ref_name, ref_data in REFERENTIALS.items():
            with st.expander(f"Référentiel {ref_name}"):
                st.json(ref_data)
        return
    
    # Sélection du référentiel
    referential = st.selectbox(
        "📋 Sélectionnez un référentiel", 
        list(REFERENTIALS.keys()),
        help="Choisissez le standard GFSI applicable pour ce candidat"
    )
    
    # Vérification que tous les éléments nécessaires sont présents
    if uploaded_file and referential and st.session_state.groq_client:
        # Bouton pour lancer l'analyse
        if st.button("🔍 Analyser le CV", type="primary"):
            # Extraction du texte du CV
            cv_text = extract_text_from_pdf(uploaded_file)
            
            # Afficher un extrait du texte extrait en mode debug
            if show_debug and cv_text:
                with st.expander("Aperçu du texte extrait", expanded=False):
                    st.text(cv_text[:1000] + "..." if len(cv_text) > 1000 else cv_text)
            
            if cv_text:
                # Analyse du CV avec références systématiques
                analysis_result = analyze_cv_with_groq(
                    cv_text, 
                    referential, 
                    st.session_state.groq_client,
                    model=selected_model
                )
                
                # Affichage des données brutes en mode debug
                if show_debug and analysis_result:
                    with st.expander("Données brutes de l'analyse (Debug)", expanded=False):
                        st.json(analysis_result)
                
                # Affichage des résultats
                if analysis_result:
                    # Affichage structuré des résultats
                    display_analysis_results(analysis_result, referential)
                    
                    # Génération et téléchargement du rapport
                    report_html = generate_exportable_report(analysis_result, referential, cv_text)
                    if report_html:
                        st.download_button(
                            label="📥 Télécharger le rapport complet",
                            data=report_html,
                            file_name=f"analyse_cv_{referential}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.html",
                            mime="text/html",
                        )

if __name__ == "__main__":
    main()
