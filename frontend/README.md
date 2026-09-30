# DocuChat AI - Frontend

React + Vite + TypeScript frontend for DocuChat AI.

## Environment Configuration

DocuChat AI supports multiple environments (`local`, `dev`, `staging`, `prod`).
The frontend is designed to be environment-agnostic: a single build artifact works across all environments using relative `/api/v1` routes.

For full environment documentation and deployment guidelines, please refer to the [Root README.md](../README.md#environments).

### Quick Local Run

```bash
npm install
cp .env.example .env
npm run dev
```
