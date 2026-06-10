# Cómo conectar el bot con Google Sheets

## Paso 1 — Crear el Google Sheets

1. Ve a sheets.google.com y crea una hoja nueva
2. Nómbrala: "Nero Bot"
3. Crea 4 pestañas (hojas) con estos nombres exactos:
   - Clientes
   - Prestamos
   - Inversores
   - Asesores

## Paso 2 — Encabezados de cada hoja

### Hoja: Clientes
| Celular | Direccion | PIN | Extracto1 | Extracto2 | Cedula | Recibo | Fecha | Cupo | Plazo |

### Hoja: Prestamos
| Celular | Cupo | Plazo | Monto | Periodicidad | Fecha | Estado |

### Hoja: Inversores
| Celular | Direccion | PIN | Fecha |

### Hoja: Asesores
| Nombre | Celular | Fecha |

⚠️ Las columnas "Cupo" y "Plazo" en la hoja Clientes las llenas TÚ manualmente
   para cada cliente aprobado. El bot las lee para saber si tiene crédito disponible.

## Paso 3 — Crear credenciales de Google

1. Ve a console.cloud.google.com
2. Crea un proyecto nuevo (llámalo "Nero Bot")
3. Activa estas dos APIs:
   - Google Sheets API
   - Google Drive API
4. Ve a "Credenciales" → "Crear credenciales" → "Cuenta de servicio"
5. Ponle nombre: "nero-bot"
6. Descarga el archivo JSON de la cuenta de servicio
7. Renómbralo exactamente: credentials.json

## Paso 4 — Dar acceso al Google Sheets

1. Abre el archivo credentials.json
2. Busca el campo "client_email" — copia ese correo (termina en @...iam.gserviceaccount.com)
3. Ve a tu Google Sheets
4. Clic en "Compartir"
5. Pega ese correo y dale permiso de "Editor"

## Paso 5 — Obtener el ID del Google Sheets

La URL de tu hoja se ve así:
https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit

Copia ese ID y pégalo en bot.py donde dice:
GOOGLE_SHEETS_ID = "TU_GOOGLE_SHEETS_ID_AQUI"

## Paso 6 — Subir credentials.json a Railway

1. En Railway, ve a tu proyecto
2. Ve a "Variables"
3. En lugar de subir el archivo, copia TODO el contenido del credentials.json
4. Crea una variable llamada: GOOGLE_CREDENTIALS
5. Pega el contenido completo como valor

Luego en bot.py el código ya maneja esto automáticamente.
