# Comics Scanner – Full-stack App (Mobile front + FastAPI + OpenCV)

Este projeto permite catalogar sua coleção de revistas em quadrinhos:
- **Front-end** para celular com captura pela câmera (ou upload), mini-galeria, compressão local e envio em lote.
- **Back-end (FastAPI + OpenCV)** recebe as imagens, cria uma pasta com o nome da revista e para cada foto detecta as bordas da página,
  aplica **perspectiva (deskew/warp)** e salva **páginas recortadas** e os **originais**.

## Como rodar (backend)
1. Requisitos: Python 3.10+
2. Instale as dependências:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. Rode o servidor:
   ```bash
   uvicorn app:app --reload --port 8000
   ```
   O servidor inicia em `http://localhost:8000/`

> Os arquivos serão salvos em `backend/data/<slug_da_revista>/pages` (recortes) e `backend/data/<slug_da_revista>/raw` (originais).

## Como usar (frontend)
Abra `frontend/index.html` no seu navegador mobile (recomendo usar um servidor local, como a extensão “Live Server” do VSCode,
ou `python -m http.server` dentro da pasta `frontend`).

1. Informe o **nome da revista** (ex.: *Homem-Aranha #123*).
2. Toque em **Abrir câmera** (ou **Selecionar fotos** no fallback) e capture as páginas.
3. Revise as miniaturas, apague as indesejadas, e clique em **Enviar páginas**.
4. O back-end processa e responde com os nomes dos arquivos gerados.

## Estrutura
```
comics-scanner/
  backend/
    app.py
    page_processor.py
    requirements.txt
    run.sh
    data/                # criado em runtime
  frontend/
    index.html
    app.js
    styles.css
    manifest.webmanifest
    service-worker.js
  README.md
```

## Observações técnicas
- A detecção de página busca o **maior contorno quadrilátero** via Canny + aprox poligonal; se não encontrar, usa o **retângulo mínimo**.
- A transformação de perspectiva calcula largura/altura pela maior distância dos lados e força orientação **retrato** (altura ≥ largura).
- Você pode ajustar thresholds no `page_processor.py` (Canny, dilatação/erosão e epsilon do `approxPolyDP`).

## Próximos passos (opcionais)
- Autenticação e acervo com metadados (autor, editora, ano, etc.).
- Renomeação automática das páginas (OCR do número da página ou ordenação por timestamps EXIF).
- Compactação/backup em ZIP ou PDF por edição.
- Servir o **frontend** diretamente pelo FastAPI (montando `StaticFiles`) se desejar tudo em um único servidor.
