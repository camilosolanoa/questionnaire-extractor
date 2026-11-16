import { useState } from "react";
import type { FormEvent } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

type Result = {
  titulo: string;
  idioma: string;
  total_items: number;
  items: {
    numero: number;
    enunciado: string;
    tipo: string;
    alternativas: { valor: number | string; texto: string }[];
    respuesta_correcta: number | string | null;
  }[];
};
const labels: Record<string, string> = {
  escala_likert: "Escala Likert",
  seleccion_multiple: "Selección múltiple",
  verdadero_falso: "Verdadero / falso",
  desarrollo: "Desarrollo",
  emparejamiento: "Emparejamiento",
};

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [view, setView] = useState<"preview" | "json">("preview");

  async function process(event: FormEvent) {
    event.preventDefault();
    if (!file || busy) return;
    setError("");
    setResult(null);
    setBusy(true);
    try {
      if (file.size > 3_000_000)
        throw new Error("El archivo supera el límite de 3 MB.");
      const body = new FormData();
      body.append("file", file);
      const response = await fetch("/api/extract", { method: "POST", body });
      const data = await response.json().catch(() => null);
      if (!response.ok)
        throw new Error(
          typeof data?.detail === "string"
            ? data.detail
            : "No se pudo procesar el documento. Intenta de nuevo.",
        );
      setResult(data);
      setView("preview");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "No se pudo conectar al servicio.",
      );
    } finally {
      setBusy(false);
    }
  }

  function download() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(result, null, 2)], { type: "application/json" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "cuestionario.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <main>
      <header>
        <a className="brand" href="/">
          C<span className="brand-dot">.</span> <span>Cuestionarios</span>
        </a>
        <a href="/docs" target="_blank" rel="noreferrer">
          Documentación API ↗
        </a>
      </header>
      <section className="intro">
        <p className="eyebrow">DEL DOCUMENTO A LOS DATOS</p>
        <h1>
          Tus preguntas,
          <br />
          <span>en un formato claro.</span>
        </h1>
        <p>
          Extrae ítems y alternativas de un cuestionario.
          <br />
          Revisa el resultado y descarga un JSON listo para usar.
        </p>
      </section>
      <div className="workspace">
        <section className="panel upload">
          <div className="step">
            01 <span>DOCUMENTO</span>
          </div>
          <h2>Sube tu cuestionario</h2>
          <form onSubmit={process}>
            <label className="file-label" htmlFor="file">
              <span className="file-icon" aria-hidden="true">
                ↑
              </span>
              <strong>Selecciona un archivo</strong>
              <span>PDF · Word (.docx) · Excel (.xlsx)</span>
            </label>
            <input
              id="file"
              type="file"
              accept=".pdf,.docx,.xlsx"
              disabled={busy}
              required
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setResult(null);
                setError("");
              }}
            />
            <p className="hint">
              Hasta 3 MB y 100 ítems. PDF con texto, máximo 20 páginas. No
              incluye OCR.
            </p>
            <p className="privacy">
              Usa solo cuestionarios inventados o de dominio público. No subas
              tests comerciales ni datos personales. El texto se envía a OpenAI
              para procesarlo; esta app no guarda archivos ni resultados.
            </p>
            <button className="primary" disabled={!file || busy} type="submit">
              {busy ? "Procesando documento…" : "Extraer cuestionario →"}
            </button>
            <div aria-live="polite">
              {busy && (
                <p className="hint">
                  Identificando preguntas, alternativas e idioma…
                </p>
              )}
            </div>
            {error && (
              <p className="error" role="alert">
                {error}
              </p>
            )}
          </form>
          <div className="examples">
            <h3>Prueba con un ejemplo</h3>
            <p>Documentos ficticios, sin datos personales.</p>
            <div>
              <a href="/examples/cuestionario-es.pdf" download>
                PDF · Español ↙
              </a>
              <a href="/examples/questionario-it.docx" download>
                Word · Italiano ↙
              </a>
              <a href="/examples/questionnaire-en.xlsx" download>
                Excel · Inglés ↙
              </a>
            </div>
          </div>
        </section>
        <section className="panel result" aria-busy={busy}>
          <div className="step">
            02 <span>RESULTADO</span>
          </div>
          {!result ? (
            <div className="empty">
              <span className="braces" aria-hidden="true">
                {"{ }"}
              </span>
              <h2>Una estructura, muchas preguntas</h2>
              <p>
                Aquí aparecerán los ítems detectados,
                <br />
                sus alternativas y las claves indicadas.
              </p>
              <div className="tags">
                <span>Likert</span>
                <span>Selección múltiple</span>
                <span>V / F</span>
                <span>Desarrollo</span>
                <span>Emparejamiento</span>
              </div>
            </div>
          ) : (
            <>
              <div className="result-heading">
                <div>
                  <h2>{result.titulo}</h2>
                  <p className="hint" role="status">
                    {result.total_items} ítems · Idioma:{" "}
                    {result.idioma.toUpperCase()}
                  </p>
                </div>
                <button onClick={download}>Descargar JSON ↓</button>
              </div>
              <p className="review">
                Revisa el resultado antes de usarlo. La extracción con IA puede
                cometer errores; las claves ausentes se muestran como null.
              </p>
              <div className="tabs" aria-label="Vista del resultado">
                <button
                  aria-pressed={view === "preview"}
                  onClick={() => setView("preview")}
                >
                  Vista previa
                </button>
                <button
                  aria-pressed={view === "json"}
                  onClick={() => setView("json")}
                >
                  JSON
                </button>
              </div>
              {view === "json" ? (
                <pre tabIndex={0}>{JSON.stringify(result, null, 2)}</pre>
              ) : (
                <div className="items">
                  {result.items.map((item) => (
                    <article key={item.numero}>
                      <div className="item-top">
                        <strong>Ítem {item.numero}</strong>
                        <span>{labels[item.tipo] ?? item.tipo}</span>
                      </div>
                      <p>{item.enunciado}</p>
                      {item.alternativas.length > 0 && (
                        <ul>
                          {item.alternativas.map((choice) => (
                            <li key={String(choice.valor)}>
                              <b>{choice.valor}</b> {choice.texto}
                            </li>
                          ))}
                        </ul>
                      )}
                      <small>
                        Respuesta indicada:{" "}
                        {item.respuesta_correcta ?? "null (no indicada)"}
                      </small>
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
        </section>
      </div>
      <footer>
        Extracción asistida por IA · Conserva el idioma original · Sin cuentas
        ni historial
      </footer>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
