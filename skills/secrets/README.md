# secrets/README.md — Configuração de Chaves de API

Crie um arquivo `.env` nesta pasta com o seguinte conteúdo:

```
GEMINI_API_KEY=sua_chave_aqui
GOOGLE_APPLICATION_CREDENTIALS=caminho/para/service-account.json
```

- `GEMINI_API_KEY`: Obtida em https://aistudio.google.com/app/apikey
- `GOOGLE_APPLICATION_CREDENTIALS`: Caminho para o arquivo JSON da service account do Google Cloud (necessário para o Text-to-Speech)

**Atenção:** O arquivo `.env` e arquivos `.json` nesta pasta estão no `.gitignore` e nunca devem ser commitados.
