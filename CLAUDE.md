# CLAUDE.md — Projeto VideoMaker AI Agent

## Visão Geral

Agente de IA para criação automatizada de vídeos verticais (1:00–1:30) para TikTok e YouTube Shorts. O projeto é modular, baseado em ferramentas (skills) independentes orquestradas por um fluxo principal.

**Fase atual: Geração de Áudio** (roteiro + avaliação + TTS)

---

## Stack e Dependências

- **Linguagem:** Python 3.11+
- **Agente de roteiro:** Google Gemini API (modelo gemini-2.0-flash ou superior)
- **Agente avaliador:** Google Gemini API
- **Text-to-Speech:** Google Cloud Text-to-Speech API
- **Gerenciamento de secrets:** Arquivo local em `skills/secrets/`
- **Pacotes principais:** google-generativeai, google-cloud-texttospeech, python-dotenv

---

## Estrutura de Pastas

```
videomaker/
├── main.py                     # Orquestrador principal do fluxo
├── CLAUDE.md                   # Este arquivo
├── requirements.txt            # Dependências do projeto
├── .gitignore                  # Ignorar secrets, audios gerados, etc.
├── videos/                     # Pasta de saída — um subdiretório por vídeo
│   ├── video1/
│   │   └── audio.mp3           # Áudio gerado (saída desta fase)
│   ├── video2/
│   └── ...
├── skills/
│   ├── secrets/
│   │   ├── .env                # Chaves de API (GEMINI_API_KEY, GOOGLE_TTS_KEY, etc.)
│   │   └── README.md           # Instruções para configurar as chaves
│   ├── script_generator/
│   │   ├── generator.py        # Agente Gemini que gera roteiros
│   │   ├── prompts.py          # System prompt e templates do agente de roteiro
│   │   └── context/
│   │       └── references.txt  # Roteiros de referência para contexto do agente
│   ├── script_evaluator/
│   │   ├── evaluator.py        # Agente Gemini que avalia e refina o roteiro
│   │   └── prompts.py          # System prompt e critérios de avaliação
│   ├── audio_generator/
│   │   ├── tts.py              # Integração com Google Cloud TTS
│   │   └── config.py           # Configurações de voz, velocidade, idioma
│   ├── subtitle_generator/     # (fase futura)
│   └── video_assembler/        # (fase futura)
```

---

## Fluxo da Fase Atual (Geração de Áudio)

O `main.py` orquestra o seguinte pipeline sequencial:

```
1. GERAÇÃO DE ROTEIROS (script_generator)
   ├── Carrega contexto de referência (references.txt)
   ├── Gera roteiro #1 → salva
   ├── Gera roteiro #2 → salva
   └── Gera roteiro #3 → salva

2. AVALIAÇÃO E REFINAMENTO (script_evaluator)
   ├── Recebe os 3 roteiros
   ├── Avalia qual é o melhor (critérios: gancho, ritmo, CTA, clareza)
   ├── Aplica correções ortográficas e melhorias
   └── Retorna o roteiro final (string)

3. GERAÇÃO DE ÁUDIO (audio_generator)
   ├── Recebe o roteiro final
   ├── Envia para Google Cloud TTS
   ├── Salva o arquivo audio.mp3 em videos/videoN/
   └── Retorna o caminho do arquivo gerado
```

---

## Especificações Detalhadas por Skill

### 1. script_generator (Agente de Roteiro)

**Arquivo principal:** `skills/script_generator/generator.py`

- **API:** Google Gemini (google-generativeai)
- **Temperatura:** 0.9 (alta criatividade)
- **Top-p:** 0.95
- **Modelo:** gemini-2.0-flash (ou o mais recente disponível)
- **Contexto:** Carregar conteúdo integral de `skills/script_generator/context/references.txt` como parte do system prompt
- **Comportamento:**
  - Recebe um **tema/briefing** como input do usuário
  - Gera **3 roteiros distintos**, um de cada vez, em chamadas separadas e iterativas à API
  - Cada roteiro deve ter entre 150–250 palavras (adequado para 1:00–1:30 de vídeo)
  - Cada roteiro deve conter: gancho nos primeiros 3 segundos, desenvolvimento, e CTA (call to action) no final
  - Os roteiros devem variar em abordagem (ex: um mais emocional, um mais informativo, um mais polêmico/curiosidade)
- **System prompt deve incluir:**
  - Papel: "Você é um roteirista especializado em vídeos curtos virais para TikTok e YouTube Shorts"
  - Os roteiros de referência do `references.txt` como exemplos de estilo e tom
  - Instrução explícita: retornar apenas o texto do roteiro, sem marcações ou metadados
- **Saída:** Lista com 3 strings (roteiros)

### 2. script_evaluator (Agente Avaliador)

**Arquivo principal:** `skills/script_evaluator/evaluator.py`

- **API:** Google Gemini
- **Temperatura:** 0.3 (mais analítico e preciso)
- **Modelo:** gemini-2.0-flash
- **Comportamento:**
  - Recebe os 3 roteiros gerados
  - Avalia cada um com base nos critérios: poder do gancho, ritmo e fluidez, clareza da mensagem, potencial viral, CTA eficaz, adequação ao formato (1–1:30 min)
  - Seleciona o melhor roteiro
  - Aplica correções ortográficas e gramaticais
  - Faz melhorias pontuais de texto se necessário (sem alterar a essência)
  - Retorna o roteiro final pronto para narração
- **System prompt deve incluir:**
  - Papel: "Você é um diretor criativo especializado em conteúdo viral de formato curto"
  - Critérios de avaliação explícitos
  - Instrução: retornar APENAS o roteiro final corrigido, sem explicações
- **Saída:** String com o roteiro final

### 3. audio_generator (Text-to-Speech)

**Arquivo principal:** `skills/audio_generator/tts.py`

- **API:** Google Cloud Text-to-Speech
- **Configurações (em config.py):**
  - Idioma: pt-BR
  - Voz: selecionar uma voz neural natural (ex: pt-BR-Wavenet-B ou Neural2)
  - Formato de saída: MP3 (AudioEncoding.MP3)
  - Speaking rate: 1.0 (ajustável)
  - Pitch: 0.0 (ajustável)
- **Comportamento:**
  - Recebe o roteiro final (string)
  - Faz a chamada à API do Google Cloud TTS
  - Salva o áudio como `audio.mp3` dentro de `videos/videoN/` (onde N é o próximo número disponível)
- **Saída:** Caminho do arquivo .mp3 gerado

---

## Gerenciamento de Secrets

**Pasta:** `skills/secrets/`

- Todas as chaves de API ficam em `skills/secrets/.env`
- Formato do `.env`:
  ```
  GEMINI_API_KEY=sua_chave_aqui
  GOOGLE_APPLICATION_CREDENTIALS=caminho/para/service-account.json
  ```
- Usar `python-dotenv` para carregar as variáveis no runtime
- O `.gitignore` DEVE incluir:
  ```
  skills/secrets/.env
  skills/secrets/*.json
  videos/*/audio.mp3
  ```

---

## main.py — Orquestrador

O `main.py` é o ponto de entrada. Ele deve:

1. Carregar variáveis de ambiente via dotenv
2. Solicitar ao usuário o tema/briefing do vídeo (input ou argumento CLI)
3. Chamar `script_generator.generate(tema)` → retorna lista de 3 roteiros
4. Chamar `script_evaluator.evaluate(roteiros)` → retorna roteiro final
5. Criar a pasta `videos/videoN/` (N = próximo número sequencial)
6. Chamar `audio_generator.generate(roteiro_final, output_path)` → salva audio.mp3
7. Imprimir no terminal: roteiro final utilizado e caminho do áudio gerado

**Exemplo de execução:**
```bash
python main.py
# ou
python main.py --tema "5 hábitos que mudaram minha vida"
```

---

## Convenções de Código

- Usar **type hints** em todas as funções
- Cada skill expõe **uma função principal** como interface pública (ex: `generate()`, `evaluate()`)
- Tratamento de erros com try/except em todas as chamadas de API
- Logs informativos no terminal (print ou logging) para acompanhar o progresso do pipeline
- Docstrings em todas as funções públicas
- Nenhum hardcode de chaves de API no código — tudo via .env

---

## Fases Futuras (não implementar agora)

Estas skills serão desenvolvidas depois:

- **subtitle_generator:** Transcrever o roteiro em formato de legenda sincronizada (.srt ou .ass) com o áudio
- **video_assembler:** Unir vídeo de fundo (adicionado manualmente em `videos/videoN/`) + áudio + legenda para gerar o vídeo final exportado pronto para upload

---

## Resumo do Escopo Atual

| O que fazer agora | O que NÃO fazer agora |
|---|---|
| script_generator completo | subtitle_generator |
| script_evaluator completo | video_assembler |
| audio_generator completo | Upload automático |
| main.py orquestrando o fluxo | Interface gráfica |
| Estrutura de pastas | Edição de vídeo |
| Gerenciamento de secrets | |

**Resultado esperado desta fase:** Ao executar `python main.py`, o sistema gera 3 roteiros, avalia, escolhe o melhor, gera o áudio via TTS e salva o arquivo `audio.mp3` na pasta correspondente em `videos/`.
