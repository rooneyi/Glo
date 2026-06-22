#!/usr/bin/env bash
# Installe les dépendances Node et compile le dashboard React.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DASH="$ROOT/frontend/dashboard"

if ! command -v node >/dev/null 2>&1; then
  echo "Erreur : Node.js n'est pas installé."
  echo "Installez Node.js 18+ : https://nodejs.org/ ou utilisez nvm (fichier frontend/dashboard/.nvmrc)."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Erreur : npm n'est pas installé (livré avec Node.js)."
  exit 1
fi

NODE_MAJOR="$(node -p "process.versions.node.split('.')[0]")"
if [ "$NODE_MAJOR" -lt 18 ]; then
  echo "Erreur : Node.js $NODE_MAJOR détecté — version 18 minimum requise (Vite 6)."
  exit 1
fi

echo "→ Dossier : $DASH"
cd "$DASH"

if [ ! -f package.json ]; then
  echo "Erreur : package.json introuvable dans frontend/dashboard/"
  exit 1
fi

echo "→ Installation des dépendances npm…"
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

echo "→ Compilation du dashboard…"
npm run build

if [ -f "$ROOT/static/dashboard/dashboard.js" ]; then
  echo "✓ Dashboard prêt : static/dashboard/dashboard.js"
else
  echo "Erreur : le build n'a pas produit static/dashboard/dashboard.js"
  exit 1
fi
