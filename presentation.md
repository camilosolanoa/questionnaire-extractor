# Guía para la entrevista

## Presentación — 30 segundos

«Construí una aplicación que convierte cuestionarios PDF, Word y Excel en JSON.
React permite subir el archivo y descargar el resultado. FastAPI extrae el texto,
un modelo identifica las preguntas y Pydantic valida la estructura.
Prioricé un flujo simple, errores claros y ejemplos verificables».

## Demo — 2 minutos

1. Abrir https://questionnaire-extractor-one.vercel.app.
2. Descargar el PDF de ejemplo, subirlo y procesarlo: contiene 6 ítems.
3. Mostrar idioma, tipos y alternativas. La pregunta verdadero/falso tiene
   `respuesta_correcta: null`: el documento no indica una clave y no debemos inventarla.
4. Descargar el JSON. Mostrar un error con un archivo `.txt`.

## Recorrido del código — 2 minutos

**Archivo → React → FastAPI → texto → modelo → Pydantic → JSON.**

- `frontend/src/main.tsx`: un componente envía el archivo con `FormData` a
  `POST /api/extract`; muestra carga, error o resultado.
- `backend/main.py` y `files.py`: validan formato, tamaño y contenido; leen el
  documento con `pypdf`, `python-docx` u `openpyxl`.
- `backend/llm.py` y `prompt.txt`: envían el texto a GPT-6 Luna con un esquema
  de salida. El modelo identifica idioma, preguntas, alternativas y claves explícitas.
- `backend/models.py`: comprueba tipos, conteos, números únicos y claves válidas.
  FastAPI devuelve el cuestionario o un error claro.

## Preguntas que debo poder responder

**¿Por qué un modelo?** Los documentos varían en idioma y organización. Las librerías
leen el texto; el modelo interpreta su significado sin reglas frágiles por palabras clave.

**¿Un JSON válido garantiza exactitud?** No. Pydantic valida estructura y coherencia,
pero el modelo puede interpretar mal el documento. El resultado requiere revisión.

**¿Cómo represento emparejamiento?** Uso etiquetas izquierda/derecha, como `L1` y `RB`.
Una clave explícita se expresa como `L1=RB;L2=RA`. Documenté esta decisión en el README.

**¿Por qué no hay base de datos?** El flujo solo necesita procesar y descargar.
No guardo archivos ni resultados; cierro el archivo temporal al terminar.

**¿Cómo lo comprobé?** Hay 33 pruebas automatizadas sin llamadas de pago y tres
ejemplos inventados, en español, italiano e inglés, comparados con resultados esperados.
También comprobé subida, visualización y descarga en el navegador.

**¿Cómo protejo la clave y los datos?** La clave está en variables del servidor.
El texto se envía a OpenAI con `store=False`, que no garantiza retención cero.
Solo deben usarse documentos inventados o públicos, sin datos personales.

**¿Qué limitaciones tiene?** No incluye OCR; limita archivos a 3 MB y 100 ítems.
El límite de peticiones es local al proceso, no una cuota global. GPT-6 Luna es de pago:
esa desviación del requisito gratuito está documentada en el README.

**¿Qué mejoraría?** Más evaluaciones con documentos variados, revisión humana,
OCR y cuotas persistentes antes de ampliar el uso.

**¿Cómo usé IA?** Me asistió con implementación, pruebas y documentación.
Las comprobaciones y limitaciones están registradas; debo poder explicar cada decisión.

## Antes de la llamada

Abrir la demo, el PDF de ejemplo, el repositorio y `/docs`. Ensayar este recorrido
en cinco minutos. Tener a mano el JSON de ejemplo si falla el proveedor y explicar
que es un resultado guardado. No mostrar archivos `.env` ni claves en pantalla.
