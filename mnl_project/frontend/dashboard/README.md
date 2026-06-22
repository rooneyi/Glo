# Dashboard React (MNL)

Le bundle compilé (`static/dashboard/dashboard.js`) n'est **pas** versionné dans Git.

## Installation (recommandé)

Depuis la racine `mnl_project/` :

```bash
chmod +x scripts/setup-frontend.sh
./scripts/setup-frontend.sh
```

## Manuel

```bash
cd frontend/dashboard
npm ci          # ou npm install si pas de lock
npm run build   # → ../../static/dashboard/dashboard.js
```

## Prérequis

- **Node.js 18+** (voir `.nvmrc` → version 20 avec nvm)
- **npm** 9+

Avec nvm :

```bash
cd frontend/dashboard
nvm install
nvm use
npm ci && npm run build
```
