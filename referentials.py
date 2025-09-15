import os
import json
import streamlit as st

# Configuration du mot de passe admin (à définir dans les secrets de l'application)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "default_admin_password")

def load_referentials_from_json():
    """
    Charge les référentiels depuis les fichiers JSON dans le dossier referentiels/
    avec fallback sur les référentiels intégrés si le dossier n'est pas accessible.
    """
    # Structure améliorée des référentiels (pour compatibilité)
    referentials = {
        "BRCGS_auditeur": {
            "Education_and_Experience": {
                "requirements": [
                    "The auditor shall have a degree in a food-related, bioscience, or science and engineering discipline.",
                    "The auditor shall have a minimum of 5 years post-qualification experience related to the food industry.",
                    "This experience shall include roles such as quality assurance, food safety, technical management, or risk management functions within manufacturing, retailing, or inspection/enforcement."
                ]
            },
            "Qualifications": {
                "Lead_Auditor": [
                    "The auditor shall have completed a recognized lead auditor qualification, including training on quality management systems with a minimum of 40 hours.",
                    "Examples of recognized courses include IRCA registered courses, ASQ Certified Quality Auditor, or BRCGS Lead Auditor courses."
                ],
                "HACCP": [
                    "The auditor shall have completed a HACCP training course of at least 2 days (16 hours) based on Codex Alimentarius principles."
                ],
                "Global_Standard_Food_Safety": [
                    "Auditors shall have successfully completed a Global Standard Food Safety (Issue 9) training course with corresponding examinations."
                ]
            },
            "Auditor_Training": {
                "Training_Program": [
                    "Certification bodies must develop tailored training programs for each auditor depending on their background.",
                    "Training shall include product safety, HACCP, prerequisite programs, and relevant laws and regulations.",
                    "Assessment of knowledge and skills for each category is required before certification."
                ],
                "Exceptions": [
                    "Certification bodies may employ auditors who do not fully meet the specified criteria, provided there is documented justification approved by BRCGS."
                ]
            }
        },
        "FSSC_22000": {
            "Initial_Training_and_Experience": {
                "Work_Experience": [
                    "The auditor shall have at least 2 years full-time experience in the food or associated industry.",
                    "Consultancy experience may be recognized for up to 6 months, provided it is equivalent to work experience."
                ],
                "Education": [
                    "A degree in a food-related or bioscience discipline, or completion of a higher education course in a related field."
                ],
                "Training": [
                    "Successful completion of a Lead Auditor Course for FSMS or QMS (minimum 40 hours).",
                    "Completed HACCP training of at least 16 hours."
                ]
            },
            "Audits": {
                "Audit_Requirements": [
                    "Auditors must have completed at least 10 audit days consisting of 5 third-party certification audits covering FSMS, HACCP, and PRP requirements.",
                    "At least 2 audits must be performed under supervision of an FSSC 22000 qualified auditor."
                ],
                "Special_Categories": {
                    "Packaging": [
                        "Auditors specializing in packaging must have a primary qualification in packaging technology.",
                        "Training must cover topics like packaging legislation, standards, and safety control."
                    ]
                }
            }
        },
        "IFS": {
            "General_Requirements": {
                "Education": [
                    "A food-related or bioscience degree (minimum Bachelor's degree or equivalent) or a successfully completed food-related professional higher education."
                ],
                "Work_Experience": [
                    "A minimum of 3 years full-time professional experience in the food industry, including quality assurance, food safety, R&D, or food safety inspection/enforcement.",
                    "Consultancy experience may be recognized for up to 1 year, provided it is documented."
                ]
            },
            "Qualifications": {
                "Lead_Auditor": [
                    "Completed a recognized Lead Auditor course (e.g., IFS, IRCA) with a duration of at least 40 hours.",
                    "Completed a Food Hygiene and HACCP course with a duration of at least 2 days/16 hours."
                ],
                "Audit_Experience": [
                    "Performed a minimum of 7 food safety audits (GFSI recognized food safety certification audits and/or second party audits) in the past 5 years.",
                    "For candidates with no audit experience, participation in 7 audits is required, including 2 shadowing audits and 5 supervised audits."
                ]
            },
            "Advanced_Requirements": {
                "Product_Scope": [
                    "One year of professional experience in the food industry in relation to food processing activities for each applied product scope.",
                    "At least 5 audits per scope, including GFSI recognized or second party audits."
                ],
                "Technology_Scope": [
                    "One year of professional experience in the food industry for each applied technology scope.",
                    "At least 5 audits per scope, including GFSI recognized or second party audits."
                ],
                "Language": [
                    "Proof of fluency in audit language via CEFR B2 certificate, 2 years work experience, or 10 audits conducted in that language."
                ]
            }
        }
    }
    
    # Essayer de charger les référentiels depuis les fichiers JSON
    referentials_dir = "referentiels"
    if os.path.exists(referentials_dir):
        loaded_count = 0
        for filename in os.listdir(referentials_dir):
            if filename.endswith(".json") and filename != "template.json":
                filepath = os.path.join(referentials_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        referential_name = data.get("metadata", {}).get("name", filename.replace(".json", ""))
                        referentials[referential_name] = data
                        loaded_count += 1
                except Exception as e:
                    st.warning(f"Erreur lors du chargement de {filename}: {str(e)}")
        
        if loaded_count > 0:
            st.success(f"✅ {loaded_count} référentiels chargés depuis le dossier 'referentiels/'")
        else:
            st.info("ℹ️ Utilisation des référentiels intégrés (dossier 'referentiels/' vide ou inaccessible)")
    else:
        st.info("ℹ️ Utilisation des référentiels intégrés (dossier 'referentiels/' non trouvé)")
    
    return referentials

# Charger les référentiels
REFERENTIALS = load_referentials_from_json()

def create_referential_with_ai(exigences_text, groq_client):
    """
    Utilise l'IA pour créer un référentiel à partir de texte brut
    """
    prompt = f"""
    Structure ces exigences de référentiel en JSON formaté avec pondérations et références :

    TEXTES À STRUCTURER:
    {exigences_text}

    FORMAT DEMANDÉ:
    {{
      "metadata": {{
        "name": "Nom à déterminer",
        "version": "1.0",
        "description": "Description du référentiel",
        "last_updated": "2025-07-28",
        "source": "Source des exigences"
      }},
      "categories": {{
        "Category_Name": {{
          "weight": 0.3,
          "description": "Description de la catégorie",
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

    CONSIGNES:
    - Identifie les catégories principales et sous-catégories logiques
    - Attribue des pondérations pertinentes (total = 1.0)
    - Numérote les exigences de manière logique
    - Propose un nom de référentiel pertinent
    - Maintiens le sens exact des exigences
    - Ajoute des références aux sections du standard si identifiables
    """
    
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Vous êtes un expert en structuration de référentiels de conformité."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=4000,
            temperature=0.1
        )
        
        # Extraire le JSON de la réponse
        content = response.choices[0].message.content
        # Trouver le JSON dans la réponse (entre ```json et ```)
        import re
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        else:
            # Essayer de parser directement si c'est du JSON pur
            return json.loads(content)
    except Exception as e:
        st.error(f"Erreur lors de la génération du référentiel : {str(e)}")
        return None

def save_referential_to_json(referential_data, filename):
    """
    Sauvegarde un référentiel au format JSON avec gestion des erreurs pour Hugging Face
    """
    try:
        # Vérifier si le dossier referentiels existe, sinon le créer
        referentials_dir = "referentiels"
        if not os.path.exists(referentials_dir):
            os.makedirs(referentials_dir)
        
        filepath = os.path.join(referentials_dir, f"{filename}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(referential_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {str(e)}")
        st.info("ℹ️ Note : Sur Hugging Face Spaces, la persistance des fichiers est limitée. Les nouveaux référentiels seront perdus au redémarrage.")
        return False

def is_admin_authenticated(password):
    """
    Vérifie si le mot de passe admin est correct
    """
    return password == ADMIN_PASSWORD

# Template pour nouveaux référentiels
TEMPLATE_NOUVEAU_REFERENTIEL = {
    "NOM_DU_REFERENTIEL": {
        "General_Requirements": {
            "requirements": [
                "Exigence 1",
                "Exigence 2"
            ]
        },
        "Qualifications": {
            "required_certifications": [
                "Certification 1",
                "Certification 2"
            ]
        },
        "Audit_Experience": {
            "minimum_experience": "Description de l'expérience requise"
        }
    }
}

