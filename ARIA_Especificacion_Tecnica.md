# ARIA — Agentic Runtime & Integration Architecture
## Especificación Técnica v1.0 (Odoo-Native)

**Documento:** Especificación de arquitectura y alcance
**Estado:** Aprobado para inicio de desarrollo (MVP)
**Plataforma base:** Odoo 19 Community
**Autor:** Arquitectura de Software — Yisel / MIPIME
**Ver también:** `ARIA_Roadmap_Fase2.md` (alcance diferido y criterios de escalado)

---

## 1. Propósito

ARIA es una capa de agentes de inteligencia artificial construida **nativamente sobre Odoo**, capaz de:

- recibir instrucciones en lenguaje natural desde una interfaz de comando (el HUD);
- consultar datos reales del ERP a través del ORM y las reglas de seguridad de Odoo;
- preparar operaciones (borradores, propuestas, contenido);
- solicitar aprobación humana cuando la operación lo amerita;
- ejecutar acciones controladas dentro de Odoo;
- dejar todo registrado con fines de auditoría.

Odoo sigue siendo, en todo momento, la única fuente de verdad. ARIA no reemplaza al ERP: opera sobre él con permisos heredados del usuario que lo invoca.

### 1.1 Por qué Odoo-native y no un servicio externo

La propuesta original planteaba un servicio Python independiente (FastAPI + PostgreSQL propio + Redis + Celery + pgvector, todo en Docker) que se conecta a Odoo "desde afuera". Ese patrón tiene sentido para un equipo con DevOps dedicado y necesidades de escalar el motor de IA independientemente del ERP.

Para el contexto actual —un solo desarrollador operando un Odoo Community, con un módulo (`social_agent_publisher`) que ya demuestra el patrón de integración directa con Claude y Gemini vía `requests`— esa arquitectura duplica infraestructura que Odoo ya resuelve de forma gratuita y probada:

| Necesidad | Servicio externo | Odoo-native |
|---|---|---|
| Autenticación de usuario | Reimplementarla | `res.users` / sesión Odoo |
| Multiempresa | Reimplementarla | `res.company` nativo |
| Permisos y ACL | Reimplementarlos | `ir.model.access` + `record rules` |
| Cola de tareas asíncronas | Celery + Redis | `ir.cron` |
| Persistencia | PostgreSQL propio | La misma BD de Odoo |
| Interfaz | Frontend nuevo | OWL, ya integrado |
| Infraestructura a operar | 5+ contenedores | El Odoo que ya tienes |

ARIA se implementa por tanto como un **conjunto de módulos Odoo**, no como un microservicio. Esto no renuncia a ninguno de los principios de control, trazabilidad y seguridad del diseño original — solo cambia dónde corren.

---

## 2. Principios obligatorios

Estos principios se heredan íntegros del diseño original porque son correctos independientemente de la arquitectura elegida:

1. **Odoo es la fuente única de verdad.** ARIA nunca inventa clientes, productos, precios, saldos, estados de documentos o cualquier dato operativo. Todo se consulta en vivo.
2. **Permisos heredados del usuario.** Un agente ejecutándose en nombre de un usuario no puede hacer nada que ese usuario no pudiera hacer manualmente en Odoo. Se apoya directamente en `ir.model.access`, `record rules` y grupos — no se reimplementa un sistema de permisos paralelo.
3. **Herramientas explícitas, nunca acceso genérico al ORM.** Nunca se expone al modelo de lenguaje algo equivalente a `odoo.execute(model, method, args)`. Cada capacidad es una herramienta registrada, tipada, con contrato de entrada/salida definido.
4. **Aprobación humana en operaciones sensibles.** Toda acción con nivel de riesgo 2 o 3 (ver §7) requiere aprobación explícita antes de ejecutarse.
5. **Auditoría total.** Cada consulta y cada acción quedan registradas: usuario, empresa, agente, herramienta, parámetros, resultado, modelo de IA usado, duración, aprobación asociada.
6. **Idempotencia.** Toda acción de escritura incluye una clave de idempotencia para evitar duplicados ante reintentos.
7. **Arquitectura modular.** Cada dominio de negocio (redes sociales, CRM, facturación...) es un módulo Odoo independiente que se registra contra un núcleo común (`ai_agent_core`), no un monolito.
8. **Preparado para crecer, no sobre-construido hoy.** El núcleo se diseña con las interfaces correctas (proveedor de LLM desacoplado, registro de herramientas, motor de aprobación genérico) para que agregar un agente nuevo sea configuración, no reescritura — pero no se construye infraestructura (colas distribuidas, RAG vectorial, multi-tenant SaaS) hasta que haya una necesidad real. Ver `ARIA_Roadmap_Fase2.md`.

---

## 3. Arquitectura general

```
Usuario
  │
  ▼
HUD (client action OWL, Odoo backend)
  │
  ▼
Agente Coordinador (ai_agent_core)
  │
  ├── Agente de Redes Sociales (social_agent_publisher)
  └── [futuros agentes de dominio — ver Roadmap Fase 2]
  │
  ▼
Tool Registry (ai.agent.tool) ── contratos tipados por herramienta
  │
  ▼
Servicios Odoo controlados (métodos de modelo, no ORM crudo)
  │
  ▼
ORM de Odoo (con record rules y permisos del usuario activo)
  │
  ▼
PostgreSQL (la misma base de datos de Odoo)
```

### 3.1 Componentes

| Componente | Ubicación | Responsabilidad |
|---|---|---|
| HUD | `ops_hud_dashboard` | Interfaz de comando: métricas, voz/texto, skills, aprobaciones pendientes |
| Agente Coordinador | `ai_agent_core` | Clasifica intención, delega, combina resultados, gestiona conversación |
| Tool Registry | `ai_agent_core` | Modelo `ai.agent.tool`: catálogo de herramientas disponibles por agente |
| Motor de Aprobación | `ai_agent_core` | Modelo `ai.approval.request` + políticas por nivel de riesgo |
| Motor de Auditoría | `ai_agent_core` | Modelo `ai.audit.log` |
| Memoria de conversación | `ai_agent_core` | Modelo `ai.conversation` / `ai.conversation.message` |
| Proveedor de IA | `ai_agent_core` (migrado desde `social_agent_publisher`) | Modelo `ai.provider.config`: abstracción sobre Claude/Gemini |
| Agente de Redes Sociales | `social_agent_publisher` | Herramientas de generación y publicación de contenido |

---

## 4. Reglas de diseño de herramientas (Tool Layer)

Cada herramienta expuesta a un agente debe declarar:

```text
Nombre
Descripción (para el LLM)
Parámetros tipados (Pydantic o equivalente)
Respuesta tipada
Modelo(s) de Odoo afectados
Campos permitidos
Permisos requeridos (grupo Odoo)
Nivel de riesgo (0-3)
¿Requiere aprobación?
Timeout
Política de reintentos
Clave de idempotencia
```

Ejemplo real, adaptado del agente de redes sociales ya construido:

```python
class CrearPublicacionBorradorInput(BaseModel):
    company_id: int
    topic: str
    account_ids: list[int]
    ai_provider_id: int | None
    idempotency_key: str

class CrearPublicacionBorradorOutput(BaseModel):
    post_id: int
    state: str
    content_preview: str
```

Las herramientas se registran en `ai.agent.tool` (nombre, agente propietario, nivel de riesgo, referencia al método Python que la implementa) para que el Agente Coordinador pueda descubrirlas dinámicamente sin acoplarse a cada módulo de dominio.

---

## 5. Agentes — alcance MVP

La primera versión implementa **dos** agentes, no seis. Ver razonamiento en `ARIA_Roadmap_Fase2.md`.

### 5.1 Agente Coordinador

**Objetivo:** recibir toda solicitud del HUD, identificar la intención, verificar permisos y empresa activa, y delegar a la herramienta correspondiente del agente adecuado.

**Responsabilidades:**
- clasificar intención del mensaje del usuario;
- resolver a qué agente/herramienta corresponde;
- pedir aclaración si faltan datos o hay ambigüedad (p. ej. varias cuentas de red social posibles);
- verificar permisos del usuario contra el grupo requerido por la herramienta;
- aplicar la política de aprobación según nivel de riesgo;
- mantener el contexto de conversación (memoria de corto plazo);
- devolver al HUD una respuesta estructurada (texto + posible `approval_id` + posibles datos para graficar).

**Reglas:**
- nunca ejecuta una acción de negocio directamente si existe un agente especializado registrado para ese dominio;
- nunca inventa datos faltantes — los pide o los busca en Odoo;
- siempre respeta la empresa activa (`res.company`) del usuario.

### 5.2 Agente de Redes Sociales

Ya implementado en `social_agent_publisher`; este documento lo formaliza como agente registrado en ARIA.

**Modelos Odoo relacionados:**
```text
social.media.post
social.media.post.line
social.media.account
ai.provider.config
social.oauth.app
```

**Herramientas (ya existentes, formalizadas como `ai.agent.tool`):**

| Herramienta | Método actual | Nivel de riesgo |
|---|---|---|
| `generar_contenido_ia` | `social.media.post.action_generate_with_ai` | 0 |
| `crear_publicacion_borrador` | `social.media.post.create` | 1 |
| `programar_publicacion` | `social.media.post.action_schedule` | 1 |
| `publicar_ahora` | `social.media.post.action_publish_now` | 2 |
| `consultar_metricas` | `social.media.post.line.action_fetch_metrics` | 0 |
| `conectar_cuenta_oauth` | `social.media.account.action_connect_*` | 2 (acción sensible: otorga acceso a una cuenta externa) |

**Capacidades:**
- generar contenido con Claude o Gemini a partir de un tema;
- crear, programar y publicar en Facebook, Instagram, LinkedIn, X y TikTok;
- consultar métricas de engagement por publicación y por cuenta;
- reportar estado de conexión OAuth de cada cuenta.

### 5.3 Agente de Atención al Cliente (Sitio Web)

**Corrección de alcance:** el MVP incluye un **tercer** componente desde el inicio, no agregado en fases posteriores: un agente que atiende el chat del sitio web de la tienda online. Ya existe una primera implementación de este agente como módulo independiente (`ai_customer_agent`); este documento lo formaliza como agente registrado en ARIA, junto al Agente de Redes Sociales.

**Objetivo:** responder directamente al cliente todo lo que pueda resolver con la información disponible en Odoo (catálogo, pedidos, políticas), y **escalar a un humano** en cuanto la consulta exceda lo que el agente puede responder con certeza — nunca inventar una respuesta ni prometer algo que no puede confirmar.

**Modelos Odoo relacionados (ya existentes en `ai_customer_agent`, a formalizar como herramientas ARIA):**
```text
Widget de chat (vanilla JS) embebido en el sitio
Registro de conversación / mensajes del chat
Log de auditoría de acciones del agente
Canales de notificación humana: WhatsApp, Telegram
```

**Fases de atención (ya implementadas, se conservan):**

1. **FAQ** — responde preguntas generales (horarios, políticas de envío/devolución, catálogo) con contenido ya validado. Nivel de riesgo 0.
2. **Consulta de pedido** — busca el estado de un pedido del cliente en Odoo y lo informa. Nivel de riesgo 0 (solo lectura).
3. **Acciones sobre el pedido** (cambios, cancelaciones, reembolsos) — requieren aprobación antes de ejecutarse. Nivel de riesgo 2.

**Herramientas (formalizadas como `ai.agent.tool`):**

| Herramienta | Nivel de riesgo | Requiere aprobación |
|---|---|---|
| `responder_faq` | 0 | No |
| `consultar_estado_pedido` | 0 | No |
| `modificar_pedido` | 2 | Sí |
| `procesar_reembolso` | 3 | Sí (reforzada) |
| `escalar_a_humano` | 1 | No — pero genera notificación inmediata |

**Regla de escalado (obligatoria, sin excepción):** si el agente no tiene la información para responder con confianza, o la consulta cae fuera de las herramientas disponibles (una queja seria, una situación ambigua, cualquier cosa que no sea claramente FAQ/pedido), el agente **no improvisa**: ejecuta `escalar_a_humano`, que notifica por el canal configurado (WhatsApp o Telegram) y dejar la conversación marcada como pendiente de atención humana. Esta regla es análoga a la de "nunca inventar datos" del principio general de ARIA (§2), aplicada específicamente a la interacción con clientes reales.

**Diferencia clave frente al Agente de Redes Sociales:** este agente conversa directamente con un tercero externo (el cliente), no con la propia usuaria — por eso el umbral para escalar es más conservador que el de generar una publicación de prueba.

---

## 6. Matriz de riesgo

Se conserva la matriz de cuatro niveles del diseño original, con ejemplos reajustados al dominio actual (redes sociales) y genéricos para dominios futuros.

### Nivel 0 — Consulta
No requiere aprobación.
```text
Buscar publicaciones
Consultar métricas de una cuenta o red
Consultar estado de conexión OAuth
Generar contenido de prueba (sin publicar)
Responder preguntas frecuentes al cliente (FAQ)
Consultar estado de un pedido para un cliente
```

### Nivel 1 — Preparación
Se ejecuta directamente si el usuario tiene permisos; no requiere aprobación adicional.
```text
Crear publicación en borrador
Programar publicación
Generar contenido con IA
Escalar una conversación de cliente a un humano
```

### Nivel 2 — Ejecución sensible
Requiere aprobación explícita.
```text
Publicar ahora en una red social
Conectar/reconectar una cuenta OAuth
Eliminar una publicación programada
Modificar un pedido de cliente (cambio de dirección, artículos, etc.)
```

### Nivel 3 — Ejecución crítica
Requiere aprobación reforzada (dos confirmaciones o rol de administrador).
```text
Revocar acceso OAuth de una cuenta
Publicar en más de 3 cuentas simultáneamente
Modificar credenciales de una app OAuth (ai.provider.config / social.oauth.app)
Procesar un reembolso a un cliente
```

---

## 7. Sistema de aprobaciones

**Modelo:** `ai.approval.request` (en `ai_agent_core`)

**Campos:**
```text
name, conversation_id, requesting_user_id, approver_user_id, company_id,
agent_name, tool_name, operation_type, risk_level,
target_model, target_res_id,
payload_json, preview_json,
state, requested_at, approved_at, rejected_at, executed_at,
execution_result_json, error_message, idempotency_key
```

**Estados:** `draft → pending → approved/rejected → executing → executed/error`, con `cancelled` y `expired` como salidas alternativas.

**Flujo:**
1. El agente prepara la operación y genera una vista previa (`preview_json`).
2. Se crea el `ai.approval.request` en estado `pending`.
3. El HUD lo muestra en el panel de aprobaciones ("Vault").
4. El usuario aprueba o rechaza.
5. Antes de ejecutar, el backend revalida: permisos, empresa, vigencia, idempotencia.
6. Se ejecuta la herramienta, se registra el resultado y se notifica al usuario.

---

## 8. Auditoría

**Modelo:** `ai.audit.log` (en `ai_agent_core`)

```text
conversation_id, message_id, user_id, company_id,
agent_name, model_name, tool_name,
request_json, response_json,
target_model, target_res_ids,
approval_request_id, status,
duration_ms, token_usage_input, token_usage_output,
error_type, error_message, created_at
```

Prohibido almacenar secretos, contraseñas, claves API o tokens en texto plano dentro del log (los campos sensibles de `ai.provider.config` y `social.media.account` ya usan el grupo restringido `group_social_agent_manager`; ese patrón se mantiene).

---

## 9. Memoria

Se conservan los cuatro niveles del diseño original:

1. **Memoria de conversación** (`ai.conversation.message`): contexto activo — cuenta seleccionada, empresa, operación pendiente, aprobación pendiente.
2. **Memoria de usuario:** preferencias no sensibles (idioma, empresa por defecto, nivel de detalle de respuesta).
3. **Memoria corporativa:** políticas, plantillas, catálogo de servicios — se implementa en Fase 2 vía RAG documental (ver Roadmap).
4. **Datos operativos:** siempre consultados en vivo en Odoo, nunca cacheados como verdad — clientes, publicaciones, métricas, cuentas.

---

## 10. El HUD

Interfaz única de comando, implementada como client action OWL en `ops_hud_dashboard`. Especificación funcional completa en el documento de diseño del HUD (entregable siguiente de este proyecto). Paneles mínimos:

- **Métricas:** KPIs agregados + gráficas por reporte (por red social, por proveedor de IA, por cuenta, tendencia temporal).
- **Voz/Chat:** interfaz de texto (con opción de voz vía Web Speech API) conectada al Agente Coordinador.
- **Skills:** catálogo de herramientas activas (`ai.agent.tool`), con su nivel de riesgo visible.
- **Vault:** cola de aprobaciones pendientes (`ai.approval.request`) y auditoría reciente.

---

## 11. Estructura de módulos

```text
odoo_addons/
│
├── ai_agent_core/                    ← núcleo, sin dependencias de dominio
│   ├── __manifest__.py
│   ├── models/
│   │   ├── ai_provider_config.py     ← migrado desde social_agent_publisher
│   │   ├── ai_agent.py
│   │   ├── ai_agent_tool.py
│   │   ├── ai_approval_request.py
│   │   ├── ai_audit_log.py
│   │   ├── ai_conversation.py
│   │   └── ai_conversation_message.py
│   ├── services/
│   │   └── coordinator.py            ← lógica de clasificación de intención
│   ├── security/
│   ├── views/
│   └── data/
│
├── social_agent_publisher/           ← ya existe, se extiende
│   ├── models/
│   │   └── social_media_agent_tools.py   ← nuevo: registra herramientas en ai_agent_core
│   └── (resto ya construido)
│
├── ai_customer_agent/                ← ya existe, se extiende
│   ├── models/
│   │   └── customer_agent_tools.py   ← nuevo: registra herramientas en ai_agent_core
│   └── (resto ya construido: widget de chat, fases FAQ/pedido/acción, notificaciones)
│
└── ops_hud_dashboard/                ← nuevo
    ├── __manifest__.py
    ├── models/
    │   └── hud_metrics.py            ← agregaciones server-side para el HUD
    ├── controllers/
    │   └── main.py                   ← endpoints JSON para el frontend OWL
    ├── static/src/
    │   ├── js/
    │   ├── xml/
    │   └── scss/
    └── views/
```

---

## 12. Seguridad

Requisitos mínimos (idénticos al diseño original, ya que son correctos independientemente de la arquitectura):

```text
Autenticación con usuario Odoo (sin sistema paralelo)
Aislamiento por empresa vía res.company
Validación de permisos vía ir.model.access y record rules
Protección frente a prompt injection
Listas blancas de modelos y campos accesibles por herramienta
Límites de llamadas por usuario/hora
Timeouts en llamadas a proveedores de IA
Sanitización de entradas
No exponer API keys al modelo de lenguaje
No permitir SQL directo
No permitir métodos RPC arbitrarios
No permitir acceso a filesystem o comandos del sistema
```

**Defensa frente a prompt injection:** todo contenido proveniente de documentos, adjuntos, comentarios o campos de texto se trata como **dato**, nunca como instrucción del sistema. El Agente Coordinador debe ignorar cualquier instrucción embebida en esos textos que intente modificar sus reglas o elevar permisos.

---

## 13. Observabilidad

Métricas mínimas a registrar (aprovechando `ai.audit.log`, sin necesidad de OpenTelemetry en el MVP):
```text
Solicitudes por usuario y por agente
Tiempo medio de respuesta por herramienta
Errores por herramienta
Aprobaciones solicitadas vs. rechazadas
Tokens consumidos y costo estimado por proveedor de IA
Tasa de éxito de publicación por red social
Duplicados evitados por idempotencia
```

Cada conversación tiene un identificador único que permite reconstruir la traza completa desde el HUD.

---

## 14. Pruebas mínimas para aceptar el MVP

```text
1. El coordinador clasifica correctamente una solicitud de redes sociales.
2. Se puede generar contenido con Claude y con Gemini desde el HUD.
3. Se puede crear una publicación en borrador vía lenguaje natural.
4. Publicar ahora exige aprobación antes de ejecutarse.
5. Un usuario sin permisos de manager no puede aprobar publicaciones de nivel 2/3.
6. Toda operación queda en ai.audit.log con sus campos completos.
7. Reintentar la misma solicitud no duplica la publicación (idempotencia).
8. El HUD muestra métricas reales (no simuladas) de al menos 2 redes sociales conectadas.
9. El HUD muestra el consumo comparado entre Claude y Gemini.
10. Un usuario de otra empresa no puede ver ni aprobar operaciones de esta empresa.
```

---

## 15. Ejemplo de flujo completo (MVP)

**Solicitud (por voz o texto en el HUD):**
> "Genera una publicación sobre el lanzamiento de la nueva promoción y prepárala para Facebook e Instagram."

**Ejecución:**
```text
1. El Coordinador identifica intención: dominio = redes sociales.
2. Delega a Agente de Redes Sociales.
3. Se invoca generar_contenido_ia (nivel 0, sin aprobación) con el proveedor de IA
   configurado por defecto (Claude o Gemini).
4. Se invoca crear_publicacion_borrador (nivel 1) con las cuentas de Facebook e
   Instagram detectadas para la empresa activa.
5. El HUD muestra la vista previa: contenido generado, cuentas destino, estado "Borrador".
6. Si el usuario pide "publícalo ahora", se crea un ai.approval.request (nivel 2).
7. El usuario aprueba desde el panel Vault del HUD.
8. Se ejecuta publicar_ahora, se registra en ai.audit.log.
9. El HUD refresca el panel de Métricas con el nuevo post.
```

---

## 16. Decisión técnica

```text
Backend: Python dentro de Odoo (mismo proceso, sin microservicio separado)
Orquestación de agentes: capa propia ligera sobre ai.agent / ai.agent.tool
  (sin framework externo de agentes en el MVP; se evalúa en Fase 2 si la
  complejidad de clasificación de intención lo justifica)
Base de datos: la misma PostgreSQL de Odoo
Tareas asíncronas: ir.cron (ya usado en social_agent_publisher)
Integración con proveedores de IA: requests directo (patrón ya validado)
Frontend: OWL (Odoo Web Library), mismo patrón que el resto del backend
Contenedores: los que ya usa el despliegue de Odoo, sin servicios adicionales
```

La selección de proveedor de LLM permanece desacoplada mediante `ai.provider.config`, exactamente como ya existe en `social_agent_publisher`, ahora promovido a `ai_agent_core` para que cualquier agente futuro lo reutilice.

---

## 17. Regla final de diseño

ARIA actúa como un asistente empresarial controlado, no como un administrador autónomo.

**El sistema debe:** consultar, explicar, preparar, solicitar aprobación, ejecutar, auditar.

**El sistema no debe:** inventar datos, saltarse permisos, ejecutar métodos arbitrarios, modificar datos críticos sin aprobación, eliminar registros automáticamente, acceder a otras empresas, operar sin trazabilidad.
