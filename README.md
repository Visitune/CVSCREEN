# CVSCREEN
Outils d'analyses des CV ECOCERT
# 📄 Analyse de CV GFSI avec jauges et JSON tolérant

Une application **Streamlit** permettant l'analyse automatisée de CV d'auditeurs selon un **référentiel GFSI** (Global Food Safety Initiative), à l'aide de modèles d'intelligence artificielle.  
Le système fournit une **évaluation par exigence**, des **jauges visuelles** de conformité, et une **synthèse générée par IA**.

---

## 🚀 Fonctionnalités principales

- 📤 Chargement de CV au format PDF
- 📚 Sélection d’un référentiel GFSI (au format JSON)
- 🧠 Analyse automatisée via API Groq (modèles LLM)
- ✅ Évaluation par exigence :
  - Statut : **Conforme / À Challenger / Non Conforme**
  - Justification textuelle
  - Score de confiance (0 à 1)
- 📊 Visualisation avec jauges Plotly (niveau de conformité par exigence)
- 📝 Synthèse IA claire et actionnable
- 📦 Export possible des détails d’analyse

---

## 🖥️ Aperçu de l’interface

- **Barre latérale** :
  - Saisie de la clé API Groq
  - Choix du référentiel
  - Sélection du modèle IA
- **Zone principale** :
  - Téléversement de fichiers PDF
  - Résultats avec jauges interactives
  - Synthèse IA par candidat

---

## 🧰 Technologies utilisées

- [Streamlit](https://streamlit.io/) : UI web interactive
- [Groq API](https://console.groq.com/) : Inférence de modèles open-source
- [PyPDF2](https://pypi.org/project/PyPDF2/) : Extraction de texte PDF
- [Plotly](https://plotly.com/python/) : Graphiques et jauges
- Pandas / JSON / Pathlib / datetime : Traitement et manipulation de données

---

## ⚙️ Installation locale

1. **Cloner le projet :**

   ```bash
   git clone https://github.com/ton-user/ton-repo.git
   cd ton-repo
