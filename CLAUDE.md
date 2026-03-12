# CLAUDE.md — Projeto VideoMaker AI Agent

## Visão Geral

Agente de IA para criação automatizada de vídeos verticais (1:00–1:30) para TikTok e YouTube Shorts. O projeto é modular, baseado em ferramentas (skills) independentes orquestradas por um fluxo principal.

**Fase atual: Pipeline completo** (roteiro + avaliação + TTS + legendas + montagem)

---

## Stack e Dependências

- **Linguagem:** Python 3.11+
- **Agente de roteiro:** Google Gemini API (modelo gemini-2.5-flash)
- **Agente avaliador:** Google Gemini API
- **Text-to-Speech:** Google Cloud Text-to-Speech API (en-US Neural2)
- **Speech-to-Text:** Google Cloud Speech-to-Text API (legendas)
- **Montagem de vídeo:** FFmpeg (via subprocess — requer FFmpeg instalado no PATH)
- **Gerenciamento de secrets:** Arquivo local em `skills/secrets/`
- **Pacotes principais:** google-genai, google-cloud-texttospeech, google-cloud-speech, python-dotenv
- **Ambiente virtual:** `.venv` (todas as dependências devem ser instaladas e o projeto executado dentro deste ambiente)

---

## Ambiente Virtual

O projeto utiliza um ambiente virtual Python localizado em `.venv`. **Todas as dependências devem ser instaladas e o projeto deve ser executado dentro deste ambiente.**

```bash
# Ativar o ambiente virtual (Windows)
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar o projeto
python main.py
```

> **Importante:** Nunca instale pacotes globalmente. Sempre ative o `.venv` antes de instalar dependências ou executar o projeto.

---

## Estrutura de Pastas

```
videomaker/
├── .venv/                      # Ambiente virtual Python (não versionado)
├── main.py                     # Orquestrador principal do fluxo (a implementar)
├── test_skills.py              # Script de teste para todas as skills
├── CLAUDE.md                   # Este arquivo
├── requirements.txt            # Dependências do projeto
├── .gitignore                  # Ignorar secrets, audios, vídeos, etc.
├── videos/                     # Pasta de saída — um subdiretório por vídeo
│   ├── video1/
│   │   ├── video.mp4           # Vídeo de fundo (adicionado MANUALMENTE)
│   │   ├── audio.mp3           # Áudio gerado (audio_generator)
│   │   ├── subtitles.srt       # Legendas geradas (subtitle_generator)
│   │   └── output.mp4          # Vídeo final (video_assembler)
│   ├── video2/
│   └── ...
├── skills/
│   ├── secrets/
│   │   ├── .env                # Chaves de API (GEMINI_API_KEY, etc.)
│   │   └── README.md           # Instruções para configurar as chaves
│   ├── script_generator/
│   │   ├── generator.py        # Agente Gemini que gera roteiros
│   │   ├── prompts.py          # System prompt e templates
│   │   └── context/            # Roteiros de referência (JSON com SSML)
│   ├── script_evaluator/
│   │   ├── evaluator.py        # Agente Gemini que avalia e seleciona roteiro
│   │   └── prompts.py          # System prompt e critérios de avaliação
│   ├── audio_generator/
│   │   ├── tts.py              # Integração com Google Cloud TTS
│   │   └── config.py           # Configurações de voz, velocidade, idioma
│   ├── subtitle_generator/
│   │   ├── transcriber.py      # Geração de legendas SRT via Speech-to-Text
│   │   └── config.py           # Configurações de STT e agrupamento
│   └── video_assembler/
│       ├── assembler.py        # Montagem final via FFmpeg
│       └── config.py           # Configurações de codec e estilo de legenda
```

---

## Fluxo Atual

O usuário cria manualmente uma pasta `videos/videoN/` (ex: video1, video2) e coloca um arquivo `video.mp4` dentro dela. O sistema detecta automaticamente a pasta videoX com o maior N e usa como diretório de saída.

Pipeline sequencial:

```
0. DETECÇÃO DE PASTA
   ├── Escaneia videos/ por pastas videoN (regex ^video(\d+)$)
   ├── Seleciona a de maior N
   └── Valida presença de video.mp4 (aviso se ausente)

1. GERAÇÃO DE ROTEIROS (script_generator)
   ├── Carrega contexto de referência (JSONs em context/)
   ├── Gera roteiro #1, #2, #3 (chamadas separadas à API)
   └── Retorna lista de 3 dicts {ssml_content, voice_configurations}

2. AVALIAÇÃO (script_evaluator)
   ├── Recebe os 3 roteiros
   ├── Avalia e seleciona o melhor
   └── Retorna o dict do roteiro vencedor (inalterado)

3. GERAÇÃO DE ÁUDIO (audio_generator)
   ├── Recebe o roteiro vencedor + output_dir
   ├── Envia SSML para Google Cloud TTS
   └── Salva audio.mp3 em videos/videoN/

4. GERAÇÃO DE LEGENDAS (subtitle_generator)
   ├── Recebe audio_path + roteiro + output_dir
   ├── Transcreve via Google Cloud Speech-to-Text
   ├── Agrupa palavras em segmentos de legenda
   └── Salva subtitles.srt em videos/videoN/

5. MONTAGEM DO VÍDEO (video_assembler)
   ├── Recebe video_dir (pasta com video.mp4, audio.mp3, subtitles.srt)
   ├── Obtém duração do áudio via ffprobe
   ├── Combina vídeo + áudio + legendas burned-in com FFmpeg
   ├── Corta pela duração do áudio
   └── Salva output.mp4 em videos/videoN/
```

---

## Especificações Detalhadas por Skill

### 1. script_generator (Agente de Roteiro)

**Arquivo principal:** `skills/script_generator/generator.py`

- **API:** Google Gemini (google-genai)
- **Temperatura:** 0.9 (alta criatividade)
- **Top-p:** 0.95
- **Modelo:** gemini-2.5-flash
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
- **Modelo:** gemini-2.5-flash
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

### 4. subtitle_generator (Geração de Legendas)

**Arquivo principal:** `skills/subtitle_generator/transcriber.py`

- **API:** Google Cloud Speech-to-Text
- **Configurações (em config.py):**
  - Idioma: en-US (corresponde ao idioma do TTS)
  - Modelo STT: latest_long
  - Palavras por legenda: 2–6
  - Limite de pausa para quebra: 0.4s
- **Comportamento:**
  - Recebe audio_path, script dict e output_dir
  - Transcreve o áudio com timestamps por palavra (word-level)
  - Agrupa palavras em segmentos curtos (adequados para vídeo vertical)
  - Formata como SRT padrão e salva em videos/videoN/subtitles.srt
- **Saída:** Caminho do arquivo .srt gerado

### 5. video_assembler (Montagem Final)

**Arquivo principal:** `skills/video_assembler/assembler.py`

- **Ferramenta:** FFmpeg (via subprocess, sem pacote Python adicional)
- **Pré-requisito:** FFmpeg instalado e no PATH do sistema
- **Configurações (em config.py):**
  - Codec vídeo: libx264, preset medium, CRF 23
  - Codec áudio: AAC, bitrate 192k
  - Estilo de legenda: fonte Arial, tamanho 20, branco com contorno preto
  - Alinhamento: bottom-center, MarginV 60
- **Comportamento:**
  - Recebe video_dir (caminho da pasta videoN)
  - Valida presença de video.mp4, audio.mp3, subtitles.srt
  - Obtém duração do áudio via ffprobe
  - Executa FFmpeg com subtitles filter (burn-in) e force_style
  - Substitui áudio original do vídeo pela narração (audio.mp3)
  - Corta output pela duração do áudio (-t)
  - Salva output.mp4 na mesma pasta
- **Saída:** Caminho absoluto do output.mp4

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
  videos/*/subtitles.srt
  videos/*/video.mp4
  videos/*/output.mp4
  videos/*/*.mp4
  ```

---

## main.py — Orquestrador

O `main.py` é o ponto de entrada (a ser implementado). Ele deve:

1. Carregar variáveis de ambiente via dotenv
2. Aceitar tema/briefing via argumento CLI (`--tema`) ou input interativo
3. Detectar a pasta `videos/videoN/` de maior N (NÃO cria pastas — o usuário cria manualmente)
4. Validar a presença de video.mp4 (aviso, não erro)
5. Chamar `script_generator.generate(tema)` → retorna lista de 3 dicts
6. Chamar `script_evaluator.evaluate(roteiros)` → retorna dict vencedor
7. Chamar `audio_generator.generate(winner, output_dir)` → salva audio.mp3
8. Chamar `subtitle_generator.generate(audio_path, winner, output_dir)` → salva subtitles.srt
9. Chamar `video_assembler.assemble(output_dir)` → salva output.mp4
10. Imprimir resumo: roteiro final, caminhos dos arquivos gerados

**Exemplo de execução:**
```bash
python main.py --tema "morning coffee routines"
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

## Próxima Fase

- **main.py orquestrador:** Implementar o ponto de entrada CLI com argparse
- **Upload automático:** Upload direto para TikTok/YouTube
- **Interface gráfica:** UI para gerenciar o pipeline

---

## Resumo do Escopo

| Completo | Próxima fase |
|---|---|
| script_generator | main.py orquestrador |
| script_evaluator | Upload automático |
| audio_generator | Interface gráfica |
| subtitle_generator | |
| video_assembler | |
| Detecção automática de pasta videoX | |
| Gerenciamento de secrets | |

**Resultado esperado:** Ao executar `python test_skills.py`, o sistema detecta a pasta videoN mais recente, gera 3 roteiros, avalia, escolhe o melhor, gera o áudio via TTS, gera legendas SRT, monta o vídeo final com legendas burned-in, e salva tudo na pasta videoN correspondente. Cada pasta videoN contém: `video.mp4` (manual) + `audio.mp3` (gerado) + `subtitles.srt` (gerado) + `output.mp4` (vídeo final).
