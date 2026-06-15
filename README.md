# Fundación Philia Sophia - Calendario pedagógico

Aplicación local desarrollada en Python + Streamlit para organizar el trabajo pedagógico de la Fundación Philia Sophia.

Permite gestionar:

- Contenidos curriculares semanales importados desde Excel.
- Efemérides educativas.
- Eventos institucionales.
- Recursos pedagógicos a producir.
- Agenda semanal de trabajo.
- Exportaciones en Excel, CSV y PDF.

## 1. Instalación

Descomprimir la carpeta y abrir una terminal dentro de `philia_sophia_app`.

Crear un entorno virtual:

```bash
python -m venv .venv
```

Activarlo en Windows:

```bash
.venv\Scripts\activate
```

Activarlo en macOS/Linux:

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar la aplicación:

```bash
streamlit run app.py
```

## 2. Archivos incluidos

La carpeta `data/` ya contiene los seis Excel utilizados para construir la primera versión:

- Matemática y Geometría - Nivel Inicial.
- Prácticas del Lenguaje y Literatura - Nivel Inicial.
- Matemática - Nivel Primario.
- Lengua - Nivel Primario.
- Matemática - Secundaria Ciclo Básico.
- Lengua y Literatura - Secundaria Ciclo Básico.

La app importa automáticamente esos archivos cuando la base SQLite está vacía.

## 3. Cómo cargar nuevos Excel

Entrar en la sección **Importar Excel**.

Allí se puede:

- Importar todos los Excel ubicados en `data/`.
- Subir un nuevo archivo `.xlsx` o `.xlsm`.
- Analizar la estructura de hojas, encabezados y columnas.

Los registros duplicados se evitan mediante un hash curricular construido con nivel, unidad, área, semana, eje y contenido.

## 4. Estructura normalizada

Los Excel originales tienen estructuras distintas. La aplicación normaliza esos campos a una tabla común:

- Nivel.
- Sala / grado / año.
- Área.
- Mes.
- Semana del mes.
- Semana lectiva.
- Semana calendario.
- Estado calendario.
- Eje.
- Contenido.
- Foco de alfabetización.
- Contexto de enseñanza.
- Momento 1.
- Momento 2.
- Momento 3.
- Momento 4.
- Observaciones.

## 5. Uso recomendado

### Panel principal
Muestra un resumen general: contenidos importados, efemérides, eventos, recursos pendientes y publicados.

### Consulta curricular semanal
Permite filtrar por nivel, sala/grado/año, área, mes y semana lectiva. Desde un contenido seleccionado se puede crear un recurso pedagógico.

### Calendario pedagógico
Integra contenidos, recursos, efemérides y eventos en vistas filtrables.

### Efemérides
Permite agregar, editar y eliminar efemérides, vinculándolas con niveles, áreas e ideas de recursos.

### Eventos
Permite registrar capacitaciones, reuniones, campañas, lanzamientos o publicaciones especiales.

### Recursos
Permite cargar y seguir el estado de producción de imágenes, carruseles, PDFs, historietas, videos, guías docentes y publicaciones de Instagram.

### Agenda semanal
Genera una agenda con contenidos curriculares, efemérides, recursos y eventos. Permite exportar a Excel y PDF.

## 6. Posibles mejoras futuras

- Login por usuarios y roles.
- Calendario visual mensual tipo agenda.
- Integración con Google Calendar.
- Tablero Kanban de recursos.
- Exportación con diseño institucional completo.
- Generador automático de prompts para imágenes, carruseles o guías docentes.
- Publicación web con Streamlit Community Cloud.
- Sincronización con una base en la nube.

## 7. Nota pedagógica

La aplicación no modifica los contenidos curriculares originales. Los toma como fuente de organización, los normaliza y permite vincularlos con recursos, efemérides y eventos para facilitar el trabajo semanal de la Fundación Philia Sophia.


## Correcciones de la versión actualizada

- Panel principal: ahora reconoce `Semana 3` y `3` como la misma semana del mes.
- Consulta curricular: meses y semanas aparecen ordenados correctamente.
- Interfaz: se incorporó el logo oficial de Fundación Philia Sophia.
- Base incluida: se normalizó la forma de mostrar los grados de Primaria.
