import { useState } from 'react';
import type { FormEvent } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

type Result = { titulo: string; idioma: string; total_items: number; items: unknown[] };

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<Result | null>(null);

  async function process(event: FormEvent) {
    event.preventDefault();
    if (!file || busy) return;
    setError('');
    setResult(null);
    setBusy(true);
    try {
      if (file.size > 3_000_000) throw new Error('El archivo supera el límite de 3 MB.');
      const body = new FormData();
      body.append('file', file);
      const response = await fetch('/api/extract', { method: 'POST', body });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(typeof data?.detail === 'string'
        ? data.detail : 'No se pudo procesar el documento. Intenta de nuevo.');
      setResult(data);
    } catch (error) {
      setError(error instanceof TypeError ? 'No se pudo conectar al servicio.'
        : error instanceof Error ? error.message : 'Ocurrió un error. Intenta de nuevo.');
    } finally {
      setBusy(false);
    }
  }

  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'cuestionario.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return <main>
    <header><h1>Extractor de cuestionarios</h1><a href='/docs'>API</a></header>
    <p>Sube un documento y descarga sus preguntas y alternativas en JSON.</p>
    <form onSubmit={process} aria-busy={busy}>
      <label htmlFor='file'>Archivo PDF, Word (.docx) o Excel (.xlsx)</label>
      <input id='file' type='file' accept='.pdf,.docx,.xlsx' required disabled={busy}
        onChange={event => {
          setFile(event.target.files?.[0] ?? null);
          setResult(null);
          setError('');
        }} />
      <p className='hint'>Máximo 3 MB y 100 ítems. PDF con texto de hasta 20 páginas; sin OCR.</p>
      <p className='hint'>Usa solo material inventado o de dominio público, sin datos personales ni tests comerciales.
        El texto se envía a OpenAI; esta app no guarda archivos ni resultados.</p>
      <button className='primary' type='submit' disabled={!file || busy}>Extraer cuestionario →</button>
      <p role='status'>{busy ? 'Procesando documento…' : ''}</p>
      {error && <p className='error' role='alert'>{error}</p>}
    </form>
    <p className='examples'>Ejemplos inventados:
      <a href='/examples/cuestionario-es.pdf' download>PDF · Español</a>
      <a href='/examples/questionario-it.docx' download>Word · Italiano</a>
      <a href='/examples/questionnaire-en.xlsx' download>Excel · Inglés</a>
    </p>
    {result && <section aria-labelledby='result-title'>
      <h2 id='result-title'>{result.titulo}</h2>
      <div className='result-heading'>
        <p role='status'>{result.total_items} ítems · Idioma: {result.idioma.toUpperCase()}</p>
        <button onClick={download}>Descargar JSON ↓</button>
      </div>
      <p className='hint'>Revisa el resultado antes de usarlo. La IA puede cometer errores.
        Las respuestas no indicadas en el documento aparecen como null.</p>
      <pre tabIndex={0} aria-label='Resultado JSON'>{JSON.stringify(result, null, 2)}</pre>
    </section>}
  </main>;
}

createRoot(document.getElementById('root')!).render(<App />);
