# ARIA — Roadmap y Alcance Diferido
## Qué queda fuera del MVP, por qué, y cómo abordarlo cuando corresponda

**Documento complementario de:** `ARIA_Especificacion_Tecnica.md`

Este documento existe para que ninguna decisión de recorte se pierda ni se confunda con un olvido. Cada punto indica **qué se propuso originalmente**, **por qué se difiere**, y **la condición concreta** que debe cumplirse para retomarlo.

---

## 1. Agentes de dominio adicionales

**Propuesta original:** seis agentes desde el inicio (Coordinador, CRM, Comercial, Facturación, Proyectos, Documental), con una lista de expansión aún mayor (Compras, Inventario, Finanzas, RR.HH., Analítica, Soporte, Automatización).

**Corrección de alcance (ver `ARIA_Especificacion_Tecnica.md` §5.3):** el MVP no queda con un solo agente de dominio — incluye también el **Agente de Atención al Cliente del sitio web** (ya construido como `ai_customer_agent`), porque ya existe y resuelve una necesidad operativa real e inmediata. Lo que se difiere es el resto de la lista: CRM, Comercial, Facturación, Proyectos, Documental y todo lo demás.

**Por qué se difiere el resto:** cada agente nuevo implica modelos, herramientas, matriz de riesgo y pruebas propias. Construir seis a la vez sin haber validado el patrón con los dos que ya existen (Redes Sociales y Atención al Cliente) multiplica el riesgo de diseño incorrecto.

**Cuándo retomarlo:** cuando el Agente de Redes Sociales y el Agente de Atención al Cliente lleven al menos 2-4 semanas operando en producción con aprobaciones y auditoría reales, y el patrón `ai_agent_core` demuestre que agregar una herramienta nueva es rápido (configuración, no reescritura).

**Orden sugerido al retomar** (de mayor a menor valor inmediato dado el contexto de negocio):
1. **Agente CRM** — clientes y oportunidades; base para todo lo demás.
2. **Agente Comercial** — cotizaciones; depende de CRM.
3. **Agente de Facturación** — depende de Comercial.
4. **Agente de Proyectos** — útil para seguimiento de la consultoría/startup.
5. **Agente Documental** — requiere RAG (ver §3), por eso va después.
6. Resto (Compras, Inventario, Finanzas, RR.HH., Analítica, Soporte, Automatización) — solo si el negocio lo demanda; no construir especulativamente.

---

## 2. Infraestructura distribuida (microservicio separado)

**Propuesta original:** servicio FastAPI independiente + PostgreSQL propio + Redis + Celery + Docker Compose multi-contenedor.

**Por qué se difiere:** Odoo ya resuelve autenticación, permisos, multiempresa, persistencia y tareas asíncronas (`ir.cron`). Operar Redis/Celery/Postgres adicionales sin una razón de carga real es costo operativo puro.

**Cuándo retomarlo:** cuando se cumpla **al menos una** de estas condiciones:
- El volumen de solicitudes a agentes empieza a degradar el rendimiento del proceso principal de Odoo (se mide con los tiempos de `ai.audit.log`).
- Se necesita servir ARIA a **más de una instancia de Odoo** (multi-tenant real, no solo multiempresa dentro de la misma base).
- Se necesita que el motor de agentes escale independientemente del ERP (por ejemplo, picos de generación de contenido que no deben afectar la operación normal de Odoo).

Si ese día llega, la migración es viable sin rediseño: `ai_agent_core` ya expone sus operaciones como métodos de modelo con contratos tipados, que se pueden envolver en endpoints FastAPI sin tocar la lógica de negocio.

---

## 3. Memoria corporativa vía RAG (búsqueda semántica documental)

**Propuesta original:** pgvector o Qdrant, más MinIO para almacenamiento de objetos, para dar al Agente Documental capacidad de buscar en contratos, SOPs y manuales por significado, no por palabra exacta.

**Por qué se difiere:** no hay todavía Agente Documental (ver §1), y sin un caso de uso concreto, montar infraestructura vectorial es prematuro. Además, Odoo ya permite búsqueda de texto simple sobre `ir.attachment` y `documents.document`, suficiente para un primer volumen de documentos.

**Cuándo retomarlo:** cuando el Agente Documental esté priorizado **y** el volumen o la ambigüedad de los documentos haga insuficiente la búsqueda por texto exacto (por ejemplo, más de ~200 documentos activos, o necesidad de responder preguntas como "¿qué contratos tienen cláusula de exclusividad?").

**Cómo implementarlo entonces:** `pgvector` como extensión de la misma PostgreSQL de Odoo (no una base separada) es la opción de menor fricción operativa; Qdrant solo si el volumen lo justifica.

---

## 4. Integraciones MCP (Gmail, Calendar, GitHub, WhatsApp, Slack, Notion, Google Drive)

**Propuesta original:** preparar integración MCP con estas siete plataformas desde el diseño inicial.

**Por qué se difiere:** ninguna es indispensable para que el MVP (redes sociales) funcione. Ya existe además experiencia directa con Google Drive vía su conector nativo fuera de ARIA.

**Cuándo retomarlo:** por integración individual, cuando un agente de dominio la necesite concretamente. Ejemplos:
- Gmail/Calendar → cuando exista el Agente Comercial (enviar cotizaciones, agendar seguimientos).
- GitHub → si se agrega un Agente de Desarrollo/DevOps (no priorizado en este roadmap).
- WhatsApp → como canal de notificación del motor de aprobaciones, útil temprano si las aprobaciones deben llegar fuera del HUD.
- Slack/Notion → solo si el flujo de trabajo del equipo se traslada a esas herramientas.

No se recomienda preparar las siete "por si acaso": cada conector agrega superficie de seguridad (credenciales, scopes) que hay que auditar.

---

## 5. Abstracción multi-proveedor de LLM más allá de Claude/Gemini

**Propuesta original:** interfaz `LLMProvider` genérica preparada para cualquier proveedor.

**Estado real:** ya existe y ya funciona — `ai.provider.config` en `social_agent_publisher` implementa exactamente ese patrón para Claude y Gemini. Se conserva tal cual, solo se traslada a `ai_agent_core` para que otros agentes lo reutilicen.

**Qué se difiere:** agregar proveedores adicionales (OpenAI, modelos locales, etc.) — no hay necesidad de negocio identificada hoy.

**Cuándo retomarlo:** si un proveedor actual sube de precio de forma no competitiva, cambia condiciones de servicio, o el negocio requiere un modelo específico (por ejemplo, por residencia de datos). El patrón ya soporta agregarlo sin romper nada existente.

---

## 6. Observabilidad avanzada (OpenTelemetry, tracing distribuido)

**Propuesta original:** OpenTelemetry con trazas distribuidas desde el día uno.

**Por qué se difiere:** con un solo proceso (Odoo) y sin microservicios distribuidos, el tracing distribuido no aporta frente a simplemente consultar `ai.audit.log`, que ya tiene identificador de conversación, duración y resultado por operación.

**Cuándo retomarlo:** junto con la migración a infraestructura distribuida (§2) — en ese momento sí hay múltiples servicios que correlacionar y OpenTelemetry se vuelve valioso.

---

## 7. API REST pública (`/api/chat`, `/api/approvals`, etc.)

**Propuesta original:** API HTTP completa como si ARIA fuera un servicio consumido por múltiples clientes externos.

**Por qué se difiere:** en el MVP el único cliente es el HUD, dentro del propio backend de Odoo, que puede llamar directamente a métodos de modelo vía RPC de Odoo (`web/dataset/call_kw`) sin necesidad de una capa REST adicional.

**Cuándo retomarlo:** cuando exista un cliente externo real (app móvil propia, integración de un tercero, canal de WhatsApp/Slack para aprobaciones). En ese momento se expone un controlador `http.Controller` en `ai_agent_core` con los mismos contratos ya definidos en las herramientas — no hay que rediseñar los contratos, solo envolverlos.

---

## 8. Motor de clasificación de intención con framework de agentes dedicado

**Propuesta original:** "framework de agentes con soporte de tools y handoffs" (tipo OpenAI Agents SDK) desde el inicio.

**Por qué se difiere:** con dos agentes (Coordinador + Redes Sociales) y un catálogo de herramientas pequeño, un enrutador propio simple (basado en palabras clave + confirmación cuando hay ambigüedad, con fallback a una llamada al LLM para clasificar cuando el enrutador simple no resuelve) es suficiente y evita una dependencia externa pesada.

**Cuándo retomarlo:** cuando el catálogo de herramientas crezca (Fase 2 con CRM/Comercial/Facturación) y la clasificación de intención empiece a fallar con el enfoque simple. En ese punto, evaluar un framework dedicado — la estructura de `ai.agent` / `ai.agent.tool` ya está pensada para no requerir cambios en el modelo de datos al hacer ese cambio.

---

## Resumen ejecutivo del recorte

| Elemento diferido | Se retoma cuando... |
|---|---|
| Agentes CRM/Comercial/Facturación/Proyectos/Documental/otros | El Agente de Redes Sociales valide el patrón en producción |
| Microservicio + Redis + Celery + Docker multi-contenedor | Haya evidencia real de carga o necesidad multi-tenant |
| RAG vectorial (pgvector/Qdrant) | Exista Agente Documental y volumen documental lo justifique |
| Integraciones MCP (7 plataformas) | Cada una, individualmente, cuando un agente la necesite |
| Proveedores de LLM adicionales | Necesidad de negocio concreta (costo, residencia de datos) |
| OpenTelemetry | Junto con la migración a infraestructura distribuida |
| API REST pública | Exista un cliente externo real al HUD |
| Framework de agentes dedicado | El enrutador simple empiece a fallar con más herramientas |

Nada de esto se descarta — se secuencia. El objetivo del MVP es demostrar el patrón completo (herramienta → aprobación → ejecución → auditoría) con un dominio ya dominado, antes de multiplicarlo.
