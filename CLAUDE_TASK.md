# Tarea: Instalar y extender el módulo `ai_customer_agent`

## Contexto

Este es un módulo estándar de Odoo 19 Community que agrega un agente de
atención al cliente basado en Claude (Anthropic), **con el widget de
chat incluido y auto-instalado** — no requiere editar el theme del
sitio a mano.

- Expone el endpoint `POST /ai_agent/chat`.
- El widget de chat (`static/src/js/ai_agent_widget.js`) se inyecta
  automáticamente en todas las páginas públicas del sitio mediante una
  plantilla que hereda `website.layout` (`views/website_templates.xml`).
  Esa inyección está condicionada a que el widget esté activado y haya
  una API key configurada — si falta cualquiera de las dos, no aparece.
- El agente puede responder FAQs/políticas configuradas, consultar el
  estado real de un pedido (`sale.order`), y escalar a un ticket de
  Helpdesk (o una actividad si Helpdesk no está instalado) cuando no
  puede resolver la consulta.

No depende de n8n ni de ningún servicio externo aparte de la API de
Claude — corre 100% dentro de Odoo, por lo que se instala igual en
cualquier tienda Odoo Community que ya exista y ya tenga el módulo
`website` (o `website_sale` si es e-commerce).

## Qué necesito que hagas

1. **Detectar la carpeta de addons** del proyecto Odoo actual (revisa
   `odoo.conf` / `addons_path`, o el `docker-compose.yml` si Odoo corre
   en contenedor).
2. **Copiar la carpeta `ai_customer_agent/`** dentro de esa ruta de
   addons.
3. **Actualizar la lista de apps** (o reiniciar el contenedor de Odoo
   con `-u ai_customer_agent` / modo desarrollador → Actualizar lista
   de aplicaciones) e **instalar el módulo** "AI Customer Agent
   (Claude)".
4. **Verificar** que aparece el menú "AI Customer Agent" y la sección
   correspondiente en Ajustes.
5. **Configurar valores de prueba** en Ajustes → AI Customer Agent:
   API key de Anthropic (pedímela si no la tenés en el entorno, no la
   inventes ni la hardcodees en el código), nombre de tienda, y
   políticas de ejemplo. Dejá la Fase 2 y Fase 3 **desactivadas** para
   la primera prueba (son opt-in, ver sección "Fases" más abajo).
6. **Probar el endpoint** con curl:
   ```bash
   curl -X POST http://localhost:8069/ai_agent/chat \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "method": "call", "params": {"message": "¿Cuánto tarda el envío?", "session_id": "test-1"}}'
   ```
   Confirmá que la respuesta llega y que se crea un registro en
   `ai.agent.log`.
7. **Verificar que el widget aparece en el sitio**: entrá a la home
   pública del sitio web (no al backoffice) con "Mostrar el widget en
   el sitio público" activado en Ajustes, y confirmá que la burbuja de
   chat aparece abajo a la derecha. Si no aparece, revisá que la API
   key está configurada (la plantilla la oculta si falta) y que el
   asset se sirve correctamente en
   `/ai_customer_agent/static/src/js/ai_agent_widget.js`.
8. **Revisar el código de `controllers/main.py`** y señalarme
   cualquier problema de compatibilidad con la versión específica de
   Odoo del proyecto (por ejemplo, si el proyecto usa un módulo de
   Helpdesk de terceros con otro nombre de modelo en vez de
   `helpdesk.ticket` nativo, hay que ajustar `_escalate_to_human`).

## Fases del agente (todas opt-in, controlables desde Ajustes)

- **Fase 1 (siempre activa)**: responde FAQs y políticas configuradas.
- **Fase 2** (`ai_customer_agent.enable_order_lookup`): permite consultar
  el estado real de un pedido en `sale.order`. Apagada por defecto.
- **Fase 3** (`ai_customer_agent.enable_actions`): permite proponer
  cancelar un pedido o aplicar un descuento de compensación. Requiere
  que la Fase 2 esté activa. Apagada por defecto.
  - Sub-opción `ai_customer_agent.actions_require_approval` (activada
    por defecto): si está en `True`, la acción queda como registro
    pendiente en el modelo `ai.agent.pending_action` (menú "AI Customer
    Agent → Acciones pendientes") hasta que un usuario humano la
    aprueba desde Odoo. Si está en `False`, la acción se ejecuta
    directamente en cuanto el agente la propone.
  - `ai_customer_agent.discount_percent` define el % máximo de
    descuento que el agente puede ofrecer.

Si probás Fase 3, hacelo primero con `actions_require_approval=True` y
revisá manualmente el registro en "Acciones pendientes" antes de
aprobarlo — no lo dejes en modo automático hasta validar varias
conversaciones reales.

## Notificaciones a humanos — Canales configurables

Todos apagados por defecto, todos independientes entre sí (se puede
activar más de uno a la vez; el aviso se manda por todos los que
estén habilitados).

**WhatsApp vía CallMeBot** (`ai_customer_agent.whatsapp_callmebot_*`)
- No oficial, gratuito, sin cuenta Meta Business.
- Setup manual del usuario (no automatizable): agregar el número del
  bot de CallMeBot a contactos, mandarle "I allow callmebot to send me
  messages" por WhatsApp, guardar el apikey que responde.

**WhatsApp Cloud API** (`ai_customer_agent.whatsapp_meta_*`)
- Oficial, requiere cuenta de Meta Business con WhatsApp Cloud API ya
  configurada (Phone Number ID + Access Token desde
  developers.facebook.com/apps).
- Importante: fuera de la ventana de 24hs desde el último mensaje del
  destinatario al número de negocio, Meta exige usar una plantilla
  (`template`) pre-aprobada en Meta Business Manager, no texto libre.
  Si `whatsapp_meta_template_name` está vacío, el módulo intenta texto
  libre (falla si están fuera de la ventana). Si el usuario configura
  un nombre de plantilla, asumimos que tiene un único parámetro de
  cuerpo — si su plantilla real tiene otra estructura, hay que ajustar
  `_send_whatsapp_meta` en el controller.

**Telegram** (`ai_customer_agent.telegram_*`)
- Oficial, gratuito, sin ventana de 24hs ni plantillas — el canal más
  simple y confiable de los tres.
- Setup: crear un bot hablando con @BotFather en Telegram (comando
  `/newbot`), copiar el token. Para el chat_id: el usuario le escribe
  cualquier mensaje a su bot recién creado, y luego visita
  `https://api.telegram.org/bot<TOKEN>/getUpdates` en el navegador —
  ahí aparece el `chat.id` a usar.

**TikTok**: evaluado y descartado — no existe una API pública de
TikTok para que un negocio envíe notificaciones/mensajes a una
persona de forma proactiva (no es un canal de mensajería como
WhatsApp/Telegram). No se implementó nada para evitar dar una falsa
sensación de que funciona.

## Cosas que NO debes hacer

- No expongas la API key de Anthropic en el código ni en logs.
- No le des al usuario público (`auth="public"`) más acceso que lectura
  sobre `sale.order` y creación de `ai.agent.log` / tickets — revisa que
  el uso de `sudo()` en el controller esté acotado a esas operaciones
  puntuales, no lo expandas sin que te lo pida explícitamente.
- No cambies el endpoint a `auth="user"` — el chat lo usan clientes no
  logueados en el sitio público.

## Extensiones pendientes (hacer solo si te lo pido)

- Function calling real con la API de Claude (tools) en vez del patrón
  actual de "marcador de texto" (`NECESITA_CONSULTA_PEDIDO` /
  `NECESITA_HUMANO`) — es una mejora de robustez, no urgente para el
  piloto.
- Rate limiting sobre `/ai_agent/chat` para evitar abuso, ya que es
  `auth="public"`.
- Soporte multi-tienda si el proyecto tiene multi-company.

## Cómo probar en el entorno local con Docker

Si el proyecto usa el `docker-compose.yml` que ya armamos (Odoo +
Postgres, sin n8n porque ahora el agente vive dentro de Odoo), montá la
carpeta `ai_customer_agent/` en el volumen `./addons` y reiniciá el
contenedor de Odoo con `-u ai_customer_agent`.
