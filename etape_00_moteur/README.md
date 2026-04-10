# Étape 00 — Le Moteur

## Objectif

Établir la connexion avec un LLM, que ce soit via l'API cloud d'OpenAI ou via un modèle local avec LM Studio.

## Concepts clés

- **API OpenAI** : Interface REST standardisée pour les LLMs
- **Variables d'environnement** : Ne jamais écrire les clés API en dur dans le code
- **Mode cloud vs local** : Même interface, backends différents

## Installation

```bash
cd etape_00_moteur
pip install -r requirements.txt
cp .env.example .env
```

Éditez `.env` et ajoutez votre clé API :

```
OPENAI_API_KEY=sk-votre-vraie-cle-ici
MODE=cloud
```

## Utilisation

### Tester les connexions

```bash
python demo_connexion.py
```

Vous verrez quelles connexions fonctionnent et leur latence.

### Tester la configuration

```bash
python config.py
```

## Changer de mode

Dans votre `.env` :

```bash
# Pour utiliser OpenAI (cloud)
MODE=cloud

# Pour utiliser LM Studio (local)
MODE=local
```

## Configuration LM Studio (optionnel)

1. Téléchargez [LM Studio](https://lmstudio.ai/)
2. Téléchargez un modèle (ex: `mistral-7b-instruct-v0.3`)
3. Allez dans l'onglet "Local Server"
4. Cliquez sur "Start Server" (port 1234 par défaut)
5. Notez le nom exact du modèle chargé et mettez-le dans `LOCAL_MODEL`

## Structure des fichiers

```
etape_00_moteur/
├── config.py          ← Configuration centralisée (cloud/local)
├── demo_connexion.py  ← Test des connexions avec timing
├── .env.example       ← Template pour vos variables d'environnement
├── requirements.txt   ← Dépendances Python
└── README.md          ← Ce fichier
```

## Points importants

- Ne commitez JAMAIS votre fichier `.env` (il contient votre clé API)
- Le fichier `.env.example` sert de documentation — il peut être commité
- `config.py` est réutilisé par les étapes suivantes via `sys.path`

# Info réseau

Pour récupérer l'IP local sous Ubuntu: `ip a` ou `hostname -I`.
Si problème de firewall `sudo ufw allow 1234`

Vérifier que LM Studio écoute bien partout:

ss -tulnp | grep 1234 (on doit voir 0.0.0.0:1234, si on voit 127.0.0.1:1234 ça veut dire que c'est encore bloqué en local)


Exemple de sortie:

 $ hostname -I
192.168.1.141 172.19.0.1 172.17.0.1 172.20.0.1 172.18.0.1 2001:861:5441:a6d0:8242:xx:yyy:ccc 2001:861:5441:a6d0:16fc:zz:aa:vvv

ss -tulnp | grep 1234
tcp   LISTEN 0      511                             0.0.0.0:1234       0.0.0.0:*    users:(("lm-studio",pid=17384,fd=127))
