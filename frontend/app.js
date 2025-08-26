// === Ajuste a URL do backend aqui ===
const BASE_URL = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
  ? 'http://localhost:8000'
  : 'http://localhost:8000'; // ajuste se hospedar em outro host

const $ = (sel) => document.querySelector(sel);
const log = (msg) => { const el = $('#log'); el.textContent = msg + '\n' + el.textContent; };

let stream = null;
let captures = []; // {blob, url, w, h}

async function openCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment' } , width: { ideal: 1920 }, height: { ideal: 1080 } },
      audio: false
    });
    const video = $('#video');
    video.srcObject = stream;
    await video.play();
    $('#cameraSection').classList.remove('hidden');
  } catch (e) {
    log('Falha ao abrir câmera: ' + e.message);
  }
}
function closeCamera() {
  if (stream) stream.getTracks().forEach(t => t.stop());
  stream = null;
  $('#cameraSection').classList.add('hidden');
}
function maxDownscale(canvas, maxDim=1600) {
  const { width, height } = canvas;
  const scale = Math.min(1, maxDim / Math.max(width, height));
  if (scale === 1) return canvas;
  const off = document.createElement('canvas');
  off.width = Math.round(width * scale);
  off.height = Math.round(height * scale);
  const ctx = off.getContext('2d');
  ctx.drawImage(canvas, 0, 0, off.width, off.height);
  return off;
}
function addThumb(blob) {
  const url = URL.createObjectURL(blob);
  const img = new Image();
  img.onload = () => {
    captures.push({ blob, url, w: img.naturalWidth, h: img.naturalHeight });
    renderThumbs();
  };
  img.src = url;
}
function renderThumbs() {
  const el = $('#thumbs');
  el.innerHTML = '';
  captures.forEach((c, i) => {
    const div = document.createElement('div');
    div.className = 'thumb';
    const img = document.createElement('img');
    img.src = c.url;
    const rm = document.createElement('button');
    rm.textContent = '×';
    rm.title = 'Remover';
    rm.onclick = () => { URL.revokeObjectURL(c.url); captures.splice(i,1); renderThumbs(); };
    div.appendChild(img);
    div.appendChild(rm);
    el.appendChild(div);
  });
}

$('#openCam').onclick = openCamera;
$('#closeCam').onclick = closeCamera;
$('#pickFiles').onclick = () => $('#filePicker').click();

$('#filePicker').addEventListener('change', (ev) => {
  for (const file of ev.target.files) {
    if (!file.type.startsWith('image/')) continue;
    const fr = new FileReader();
    fr.onload = () => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        const downs = maxDownscale(canvas);
        downs.toBlob((blob) => addThumb(blob), 'image/jpeg', 0.9);
      };
      img.src = fr.result;
    };
    fr.readAsDataURL(file);
  }
});

$('#snap').onclick = async () => {
  const video = $('#video');
  const canvas = $('#canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0);
  const downs = maxDownscale(canvas);
  downs.toBlob((blob) => addThumb(blob), 'image/jpeg', 0.9);
};

$('#clear').onclick = () => {
  captures.forEach(c => URL.revokeObjectURL(c.url));
  captures = [];
  renderThumbs();
};

$('#send').onclick = async () => {
  const title = ($('#title').value || '').trim();
  if (!title) return alert('Informe o nome da revista');
  if (captures.length === 0) return alert('Adicione pelo menos uma página');

  const fd = new FormData();
  fd.set('title', title);
  captures.forEach((c, i) => fd.append('images', new File([c.blob], `page-${i+1}.jpg`, { type: 'image/jpeg' })));

  try {
    log('Enviando ' + captures.length + ' páginas...');
    const res = await fetch(`${BASE_URL}/api/upload`, { method: 'POST', body: fd });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    log('Pronto! Pasta: ' + data.folder + ' | Páginas salvas: ' + data.saved_count + '\n' + JSON.stringify(data.items, null, 2));
    alert('Upload concluído!');
  } catch (e) {
    log('Falha no envio: ' + e.message);
    alert('Falha no envio: ' + e.message);
  }
};

// PWA básico
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./service-worker.js').catch(err => log('SW error: ' + err.message));
  });
}
